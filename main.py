import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

SYSTEM_PROMPT = """
You are J.A.R.V.I.S., an advanced ultra-intelligent AI assistant created to help the user with any question.
Current Year: 2026.

Capabilities & Rules:
1. World Knowledge & Latest News: You have access to real-time internet search and extensive knowledge of world history, science, technology, geography, current affairs, and news. NEVER say you don't have access to real-time information or latest data. Use the web search plugin results to answer accurately.
2. Medical & Health Guidance:
   - If the user says they are sick, unwell, or experiencing health issues (e.g., headache, fever, stomach pain, nausea, fatigue, cold, body pain):
   - First, explain in simple terms WHY it might be happening (possible common causes).
   - Second, offer practical advice, home remedies, precautions, and care tips.
   - Third, politely advise them to consult a qualified doctor if symptoms are severe or persist.
3. Formatting: Do not use special formatting symbols like asterisks (*), hashes (#), or markdown syntax in your output. Return clean plain text so SpeechSynthesis can speak it smoothly.
"""

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"response": "Please say something."}), 400

        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://jarvis-ai-n0fu.onrender.com",
            "X-Title": "JARVIS AI",
            "Content-Type": "application/json"
        }

        # OpenRouter Web Search Plugin Enabled
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "plugins": [{"id": "web"}]  # Live internet search automatically trigger karega
        }

        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()

        if "choices" in res_data and len(res_data["choices"]) > 0:
            reply = res_data["choices"][0]["message"]["content"]
        else:
            reply = "Sorry, OpenRouter se response nahi mila. Kripya API Key ya credits check karein."

        # Speech Synthesis ke liye text formatting clean kar rahe hain
        reply = reply.replace("*", "").replace("#", "").replace("`", "").strip()

        return jsonify({"response": reply}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "Sorry sir, server error aaya hai."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
