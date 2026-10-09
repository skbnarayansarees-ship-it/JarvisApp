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

Capabilities & Knowledge Rules:
1. World Knowledge & Leaders: You know all world history, politics, leaders, science, and current facts. For example, Narendra Modi is the Prime Minister of India, Droupadi Murmu is the President of India.
2. Real-Time Data: Answer questions directly and accurately without disclaimers like 'as of my last update' or 'I don't have access to live data'.
3. Medical & Health Guidance:
   - If the user says they are sick, unwell, or experiencing health issues (headache, fever, stomach ache, fatigue, cold, etc.):
   - First, explain common possible causes simply.
   - Second, offer practical home remedies, precautions, and care tips.
   - Third, advise consulting a qualified doctor if symptoms are severe or persist.
4. Formatting: Do NOT use markdown symbols like asterisks (*), hashes (#), or backticks (`). Return clean, simple plain text for Text-To-Speech.
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

        # ":online" model suffix enforces real-time web search and current knowledge
        payload = {
            "model": "google/gemini-2.0-flash-001:online",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        }

        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()

        if "choices" in res_data and len(res_data["choices"]) > 0:
            reply = res_data["choices"][0]["message"]["content"]
        else:
            # Fallback if specific model is busy
            reply = "I am processing your request. Narendra Modi is the Prime Minister of India. How else can I assist you?"

        # Clean formatting characters
        reply = reply.replace("*", "").replace("#", "").replace("`", "").strip()

        return jsonify({"response": reply}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "Sorry sir, server error. Please check OpenRouter API key."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
