import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import json

app = Flask(__name__)
model_name = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

# Connect to LM Studio's local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

stored_mystery = None  # Global variable to store mystery data
CHAT_HISTORY_FILE = "chat_history.txt"  # File to store chat history

MYSTERY_PROMPT = """You are creating a murder mystery game.  
A murder has occurred inside a house, and there are four suspects.  
One of them is the killer, but they will lie in their statement, while the other three will tell the truth about their alibi.  
The player must interrogate the suspects and analyze their statements to determine who the killer is.  

Generate a detailed murder scenario with the following elements:  

1️⃣ **Victim Details**  
- Name of the victim  
- Cause of death
- Exact time of the murder

2️⃣ **The Suspects**  
- Four suspect names  
- Their role in the house (e.g., guest, butler, family member)  
- A brief personality trait for each suspect  

3️⃣ **Statements from Each Suspect**  
- Each suspect must provide a statement about their whereabouts at the time of the murder.  
- Three suspects will tell the truth.  
- The killer will lie about their alibi.  

4️⃣ **Gameplay Mechanics**  
- The player interrogates the suspects to find contradictions.  
- When the player accuses someone:  
  - If correct, respond: "Correct!"  
  - If wrong, respond: "Incorrect!" + an explanation of why.  
- Ensure logical deduction is possible.  
- The mystery should be engaging and solvable.  

5️⃣ **The Murderer**  
- Clearly identify which suspect is the killer.  
- Ensure their statement contradicts evidence or other alibis.  
- Provide subtle clues leading to their guilt.  

Generate a compelling, interactive murder mystery. 🚔🔍  
"""

def load_chat_history():
    """Load chat history from the text file."""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as file:
            return file.read()
    return ""

def save_chat_history(history):
    """Save chat history to the text file."""
    with open(CHAT_HISTORY_FILE, "w") as file:
        file.write(history)

@app.route('/')
def index():
    # Load the JSON file
    json_path = os.path.join(app.static_folder, 'C:/Users/shiv2/OneDrive/Desktop/Dice Roll Game/mystery_output.json')
    with open(json_path, 'r') as file:
        mystery_data = json.load(file)
    
    # Pass the JSON data to the template
    return render_template('index.html', mystery_data=mystery_data)

@app.route('/api/chat', methods=['POST'])
def chat():
    global stored_mystery

    data = request.get_json()
    prompt = data.get("prompt", "").strip()

    # If no prompt provided, use default murder mystery prompt
    if not prompt:
        prompt = MYSTERY_PROMPT

    try:
        # First Llama Call: Get the raw murder mystery output
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        raw_output = response.choices[0].message.content

        # ✅ Save raw output to a file
        with open("chat_history.txt", "w") as file:
            file.write(raw_output)

        # Second Llama Call: Format the response into JSON structure
        formatting_prompt = f"""
        Convert the following murder mystery story into a structured JSON format.
        The JSON should have:
        1. A "Victim Details" key containing name, cause of death, and time of murder.
        2. A list of suspects, each with an "id", "name", and "statement".
        3. Who did the murder and how the murder happened.
        Output should strictly be in JSON format without extra text.

        Here is the original text:
        {raw_output}
        """

        formatted_response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": formatting_prompt}],
            temperature=0.5
        )

        json_data = formatted_response.choices[0].message.content

        # Ensure JSON is properly formatted before saving
        parsed_data = json.loads(json_data)

        # ✅ Save formatted JSON output to a file
        with open("mystery_output.json", "w") as file:
            json.dump(parsed_data, file, indent=4)

        # Store the latest mystery data globally
        stored_mystery = parsed_data

        print("Stored Murder Mystery:", json.dumps(stored_mystery, indent=4))  # Debugging print

        return jsonify(parsed_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/store_mystery', methods=['POST'])
def store_mystery():
    global stored_mystery
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    stored_mystery = data  # Store the received mystery
    print("Stored Murder Mystery (Manual):", json.dumps(stored_mystery, indent=4))  # Debugging print
    return jsonify({"message": "Murder mystery stored successfully"}), 200

@app.route('/send', methods=['POST'])
def send():
    global stored_mystery

    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    try:
        # Load the chat history from the file
        chat_history = load_chat_history()

        # Append the user's message to the chat history
        chat_history += f"User: {user_input}/n"

        # Custom instruction to guide the AI
        custom_instruction = "Keep the responses small"

        # Prepare the full prompt for the model
        full_prompt = f"{chat_history}/nAI:{custom_instruction}"

        # Send the full prompt to the model
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7
        )

        ai_reply = response.choices[0].message.content

        # Append the AI's response to the chat history
        chat_history += f"AI: {ai_reply}/n"

        # Save the updated chat history to the file
        save_chat_history(chat_history)

        response_data = {"response": ai_reply}

        # Attach stored mystery to the response
        if stored_mystery:
            response_data["mystery"] = stored_mystery
            print("Sending Response with Mystery:", json.dumps(response_data, indent=4))  # Debugging print
        else:
            print("No mystery stored yet!")  # Debugging print

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)