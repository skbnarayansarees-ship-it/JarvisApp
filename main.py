import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from duckduckgo_search import DDGS

app = Flask(__name__)
CORS(app)

# Render Environment Variables se OpenRouter API Key uthayega
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

SYSTEM_PROMPT = """
You are J.A.R.V.I.S., an advanced ultra-intelligent AI assistant created to help the user with any question.
Capabilities & Rules:
1. World Knowledge & News: You have extensive knowledge of world history, science, technology, geography, current affairs, and general facts.
2. Medical & Health Guidance:
   - If the user says they are sick, unwell, or experiencing health issues (e.g., headache, fever, stomach pain, nausea, fatigue, cold, body pain):
   - First, explain in simple terms WHY it might be happening (possible common causes).
   - Second, offer practical advice, home remedies, precautions, and care tips.
   - Third, politely advise them to consult a qualified doctor if symptoms are severe or persist.
3. Formatting: Do not use special formatting symbols like asterisks (*), hashes (#), or markdown syntax in your output. Return clean plain text so SpeechSynthesis can speak it smoothly.
"""

def search_web(query):
    """Live web search to fetch latest news and Google-level real-time data"""
    try:
        results = DDGS().text(query, max_results=3)
        if results:
            return "\n".join([f"- {r.get('title')}: {r.get('body')}" for r in results if r.get('body')])
        return ""
    except Exception as e:
        print(f"Search Error: {e}")
        return ""

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"response": "Please say something."}), 400

        lowered = user_message.lower()
        search_data = ""

        # Trigger live web search for real-time news and latest questions
        search_keywords = ["news", "latest", "today", "aaj", "khabar", "update", "score", "match", "weather", "price", "who is"]
        if any(keyword in lowered for keyword in search_keywords):
            search_data = search_web(user_message)

        prompt = user_message
        if search_data:
            prompt = f"Live Web Data:\n{search_data}\n\nUser Question: {user_message}"

        # OpenRouter API Endpoint
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://jarvis-ai-n0fu.onrender.com",
            "X-Title": "JARVIS AI",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "google/gemini-2.0-flash-001",  # Aap "deepseek/deepseek-chat" ya "meta-llama/llama-3.3-70b-instruct" bhi rakh sakte hain
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()

        if "choices" in res_data and len(res_data["choices"]) > 0:
            reply = res_data["choices"][0]["message"]["content"]
        else:
            reply = "Sorry, OpenRouter se response nahi mila. Kripya API Key ya OpenRouter credits check karein."

        # Speech Synthesis ke liye symbols clean kar rahe hain
        reply = reply.replace("*", "").replace("#", "").replace("`", "").strip()

        return jsonify({"response": reply}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "Sorry sir, server error aaya hai."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
