import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from duckduckgo_search import DDGS

app = Flask(__name__)
CORS(app)

# Render Environment Variables se API key uthayega
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

system_prompt = """
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

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=system_prompt
)

def search_web(query):
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

        search_keywords = ["news", "latest", "today", "aaj", "khabar", "update", "score", "match", "weather", "price", "who is"]
        if any(keyword in lowered for keyword in search_keywords):
            search_data = search_web(user_message)

        prompt = user_message
        if search_data:
            prompt = f"Live Web Data:\n{search_data}\n\nUser Question: {user_message}"

        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(prompt)
        reply = response.text

        reply = reply.replace("*", "").replace("#", "").replace("`", "").strip()

        return jsonify({"response": reply}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "Sorry, server mein error aaya hai. Kripya API key check karein."}), 500

if __name__ == '__main__':
    # Render ke liye Dynamic Port handle karna
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
