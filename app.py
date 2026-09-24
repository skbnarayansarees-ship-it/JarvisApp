import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"reply": "I did not receive any message."}), 400

    if not OPENROUTER_API_KEY:
        return jsonify({"reply": "API Key is missing on server configuration."}), 500

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [
            {
                "role": "system", 
                "content": "You are Jarvis, a futuristic AI assistant. Respond warmly and concisely in 2-3 short sentences suitable for voice synthesis."
            },
            {"role": "user", "content": user_message}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        if response.status_code == 200:
            ai_reply = response.json()["choices"][0]["message"]["content"]
            return jsonify({"reply": ai_reply})
        else:
            return jsonify({"reply": "Error connecting to AI service."}), 500
    except Exception:
        return jsonify({"reply": "Server request timed out."}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)