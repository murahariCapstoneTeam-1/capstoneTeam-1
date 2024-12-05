import os
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from datetime import timedelta
from chat import get_response  # here weare importing chatbot response function
import smtplib
import secrets
from email.message import EmailMessage
from db import db  # this is to import db from db.py
from model import User  # Import User model after db setup

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # this is 16 bytes = 32 characters or we can set a strong secret key manually here.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

db.init_app(app)  # Initialize the db with the app

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        mobile_number = request.form['mobile_number']
        email = request.form['email']
        confirm_email = request.form['confirm_email']
        password = request.form['password']

        if email != confirm_email:
            flash("Emails do not match!", "danger")
            return redirect(url_for('register'))

        new_user = User(full_name=full_name, mobile_number=mobile_number, email=email, password=password)# type: ignore
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.full_name
            session.permanent = True  # Keeps session active based on PERMANENT_SESSION_LIFETIME
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    
    return render_template('login.html')

# Home (chatbot) page after login
@app.route('/home')
def home():
    if 'user_id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])

# Logout route
@app.route('/logout')
def logout():
    if 'user_id' in session:
        send_chat_history(session['user_id'])  # Sends chat history to email on logout
        session.clear()  # Clear session data, including chat history
        flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Chatbot response route
@app.route('/get_response', methods=['POST'])
def get_chatbot_response():
    data = request.get_json()
    user_message = data.get('message')
    response = get_response(user_message)  # This should return a string response from chat.py

    # Store the conversation in the session
    if 'chat_history' not in session:
        session['chat_history'] = []

    session['chat_history'].append({'user': user_message, 'bot': response})

    # Return the bot response to the frontend
    return jsonify(response=response)

# Function to send chat history via email on logout
def send_chat_history(user_id):
    user = User.query.get(user_id)
    if user:
        # Retrieve chat history from session
        chat_history = session.get('chat_history', [])
        
        # If there's no chat history, send a default message
        if not chat_history:
            chat_text = "No chat history available."
        else:
            # Format chat history into a readable format
            chat_text = "\n".join([f"User: {msg['user']}\nBot: {msg['bot']}\n" for msg in chat_history])

        # Create the email message
        msg = EmailMessage()
        msg.set_content(f"Dear {user.full_name},\n\nThanks for chatting with us, we hope you're enjoying your experience with McAssist!\n\nHere is your chat history:\n{chat_text}\nNote: Want to share your feedback? Simply click 'Reply' to this email and describe your feedback in up to 500 words. We'd love to hear your thoughts!\n\nBest regards,\nMcAssist Team")
        msg['Subject'] = 'Your McAssist Chat History'
        msg['From'] = 'muraharimmh@gmail.com'
        msg['To'] = user.email

        # Gmail SMTP settings
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_user = 'muraharimmh@gmail.com'
        smtp_password = 'mpue unni czjl ibit'  # Use Gmail app password for security

        # Send email via Gmail SMTP
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                smtp.starttls()  # Encrypt connection
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)
            print("Chat history sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")

# Ensure app context for db creation
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the tables (ensure it only runs once)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
