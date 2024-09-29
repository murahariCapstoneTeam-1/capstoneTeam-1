document.getElementById('send-btn').onclick = function() {
    var userMessage = document.getElementById('user-input').value;
    var chatBox = document.getElementById('chat-box');
    
    chatBox.innerHTML += `<p><strong>You:</strong> ${userMessage}</p>`;
    
    fetch('/chat', {
        method: 'POST',
        body: new URLSearchParams({
            'message': userMessage
        })
    })
    .then(response => response.json())
    .then(data => {
        chatBox.innerHTML += `<p><strong>Bot:</strong> ${data.response}</p>`;
    });
};
