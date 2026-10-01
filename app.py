import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"reply": "I did not receive any message."}), 400

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"reply": "API Key is missing in Vercel Environment Variables."}), 200

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://vercel.app",
        "X-Title": "Jarvis Web App"
    }
    
    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [
            {
                "role": "system", 
                "content": "You are Jarvis, a futuristic AI assistant. Answer warmly and concisely in 2-3 short sentences suitable for voice synthesis."
            },
            {"role": "user", "content": user_message}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        res_json = response.json()
        
        if response.status_code == 200:
            ai_reply = res_json['choices'][0]['message']['content']
            return jsonify({"reply": ai_reply})
        else:
            # Shows exact OpenRouter error message on screen
            error_details = res_json.get('error', {}).get('message', f"HTTP {response.status_code}")
            return jsonify({"reply": f"AI Error: {error_details}"}), 200

    except Exception as e:
        return jsonify({"reply": f"Connection Error: {str(e)}"}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)