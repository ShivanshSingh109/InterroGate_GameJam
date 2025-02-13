document.addEventListener("DOMContentLoaded", function () {
    let loadButton = document.getElementById("load-mystery"); // Assume a button exists
    if (loadButton) {
        loadButton.addEventListener("click", fetchChatResponse);
    }
});


async function fetchChatResponse() {
    try {
        let response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        });

        let data = await response.json();
        if (data.error) {
            document.getElementById("chatbox").innerHTML = `<p><strong>Error:</strong> ${data.error}</p>`;
            return;
        }

        document.getElementById("chatbox").innerHTML = formatJSON(data);
    } catch (error) {
        console.error("Error fetching chat:", error);
    }
}

function formatJSON(data) {
    let output = `<h2>Victim Details</h2>`;
    output += `<p><strong>Name:</strong> ${data["Victim Details"].name}</p>`;
    output += `<p><strong>Cause of Death:</strong> ${data["Victim Details"]["cause of death"]}</p>`;
    output += `<p><strong>Time of Murder:</strong> ${data["Victim Details"]["time of murder"]}</p>`;

    output += `<h2>Suspects</h2>`;
    data.Suspects.forEach(suspect => {
        output += `<p><strong>${suspect.name}:</strong> ${suspect.statement}</p>`;
    });

    return output;
}

async function sendMessage() {
    let inputField = document.getElementById("user-input");
    let message = inputField.value.trim();
    if (!message) return;

    appendMessage("You", message);
    inputField.value = ""; // Clear input

    try {
        let response = await fetch("/send", {  // Updated to call the correct Flask route
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message }) // Send the message properly
        });

        let data = await response.json();
        appendMessage("Llama", data.response || data.error || "No response received.");
    } catch (error) {
        console.error("Error fetching chat:", error);
        appendMessage("Error", "Failed to connect to the server.");
    }
}


function appendMessage(sender, message) {
    let chatbox = document.getElementById("chatbox");
    if (!chatbox) return;

    chatbox.innerHTML += `<p><strong>${sender}:</strong> ${message}</p>`;
}
