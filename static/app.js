class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.chatbox__send--footer')
        };

        this.state = false; // Chatbox visibility state
        this.messages = []; // Array to store chat messages
        this.apiUrl = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
            ? 'http://127.0.0.1:5000/get_response'
            : 'https://capstoneteam-1.onrender.com/get_response';
    }

    display() {
        const { openButton, chatBox, sendButton } = this.args;

        if (!openButton || !chatBox || !sendButton) {
            console.error('Some required chatbox elements are missing. Check your HTML.');
            return;
        }

        openButton.addEventListener('click', () => this.toggleState(chatBox));
        sendButton.addEventListener('click', () => this.onSendButton(chatBox));

        const inputField = chatBox.querySelector('.chatbox__footer input');
        if (inputField) {
            inputField.addEventListener('keyup', (event) => {
                if (event.key === 'Enter') {
                    this.onSendButton(chatBox);
                }
            });
        } else {
            console.error('Input field inside chatbox footer not found.');
        }
    }

    toggleState(chatBox) {
        this.state = !this.state;

        // Toggle chatbox visibility
        if (this.state) {
            chatBox.classList.add('chatbox--active');
        } else {
            chatBox.classList.remove('chatbox--active');
        }
    }

    onSendButton(chatBox) {
        const inputField = chatBox.querySelector('.chatbox__footer input');
        if (!inputField) {
            console.error('Input field inside chatbox footer not found.');
            return;
        }

        const userMessage = inputField.value.trim();
        if (userMessage === '') {
            console.warn('Input is empty. Nothing to send.');
            return;
        }

        // Push user message to chat messages
        this.messages.push({ name: 'User', message: userMessage });

        // Send message to the server
        fetch(this.apiUrl, {
            method: 'POST',
            body: JSON.stringify({ message: userMessage }),
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Push chatbot's response
            this.messages.push({ name: 'Sam', message: data.response });
            this.updateChatText(chatBox);
            inputField.value = ''; // Clear input field after sending
        })
        .catch(error => {
            console.error('Error while fetching response:', error);
            this.messages.push({ name: 'Sam', message: 'Sorry, I am unable to process your request. Please try again later.' });
            this.updateChatText(chatBox);
            inputField.value = ''; // Clear input field
        });
    }

    updateChatText(chatBox) {
        const messagesContainer = chatBox.querySelector('.chatbox__messages > div');
        if (!messagesContainer) {
            console.error('Chat messages container not found.');
            return;
        }

        let messagesHTML = '';
        this.messages.forEach((message) => {
            if (message.name === 'Sam') {
                messagesHTML += `<div class="messages__item messages__item--visitor">${message.message}</div>`;
            } else {
                messagesHTML += `<div class="messages__item messages__item--operator">${message.message}</div>`;
            }
        });

        messagesContainer.innerHTML = messagesHTML;
    }
}

// Initialize and display the chatbox
const chatbox = new Chatbox();
chatbox.display();