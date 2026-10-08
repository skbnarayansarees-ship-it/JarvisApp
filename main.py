from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app) 

# YAHAN APNI API KEY DAALEIN
GEMINI_API_KEY = "YOUR_API_KEY_HERE" 

# Gemini AI ko setup kar rahe hain taaki isko duniya ki saari knowledge ho
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        
        if not user_message:
            return jsonify({"response": "Please say something."}), 400

        # Real AI se response lena
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(user_message)
        bot_reply = response.text
        
        # Bot bolte waqt symbols (* ya #) na bole isliye unhe hata rahe hain
        bot_reply = bot_reply.replace("*", "").replace("#", "")
        
        return jsonify({"response": bot_reply}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "Server problem ya API key missing hai."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
