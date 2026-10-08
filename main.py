from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
# CORS allow karna zaroori hai taaki frontend backend se connect ho sake (Connection problem solve)
CORS(app) 

# Yahan aap apna AI logic laga sakte hain (Jaise Gemini, OpenAI, etc.)
def get_ai_response(user_text):
    user_text = user_text.lower()
    
    # Dummy logic for testing. Aap isko apne API se replace kar sakte hain.
    if "president of india" in user_text:
        return "The President of India is Droupadi Murmu."
    elif "hello" in user_text or "hi" in user_text:
        return "Hello! I am JARVIS. How can I help you today?"
    else:
        return f"Sir, aapne kaha: {user_text}. Mere paas abhi iska live data nahi hai."

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        
        if not user_message:
            return jsonify({"response": "Please say something."}), 400

        # AI se response lena
        bot_reply = get_ai_response(user_message)
        
        return jsonify({"response": bot_reply}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "Sorry sir, backend mein koi error aa gaya hai."}), 500

if __name__ == '__main__':
    # Server port 5000 par run hoga
    app.run(debug=True, port=5000)
