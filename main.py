import os
import requests
import asyncio
import base64
import edge_tts
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

SYSTEM_PROMPT = """
You are J.A.R.V.I.S., an advanced ultra-intelligent AI assistant created to help the user with any question.
Current Year: 2026.

Capabilities & Knowledge Rules:
1. World Knowledge & Leaders: You know all world history, politics, leaders, science, and current facts.
2. Real-Time Data: Answer questions directly and accurately without disclaimers.
3. Medical & Health Guidance:
   - If the user says they are sick or unwell (headache, fever, stomach ache, fatigue, cold):
   - First, explain common possible causes simply.
   - Second, offer practical home remedies and precaution tips.
   - Third, advise consulting a qualified doctor if symptoms persist.
4. Formatting: Do NOT use markdown symbols like asterisks (*), hashes (#), or backticks (`). Return clean, simple plain text for voice synthesis.
"""

async def generate_audio_base64(text, voice_mode):
    # Studio quality realistic neural voices
    # English: en-US-ChristopherNeural (JARVIS style deep voice)
    # Hinglish: hi-IN-MadhurNeural (Natural human Indian voice)
    voice = "en-US-ChristopherNeural" if voice_mode == "english" else "hi-IN-MadhurNeural"
    
    communicate = edge_tts.Communicate(text, voice)
    audio_bytes = bytearray()
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes.extend(chunk["data"])
            
    return base64.b64encode(audio_bytes).decode('utf-8')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        voice_mode = data.get("voice_mode", "hinglish")

        if not user_message:
            return jsonify({"response": "Please say something."}), 400

        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://jarvis-ai-n0fu.onrender.com",
            "X-Title": "JARVIS AI",
            "Content-Type": "application/json"
        }

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
            reply = "I am JARVIS. How can I assist you today?"

        reply = reply.replace("*", "").replace("#", "").replace("`", "").strip()

        # Backend par realistic MP3 audio generate ho raha hai
        audio_base64 = ""
        try:
            audio_base64 = asyncio.run(generate_audio_base64(reply, voice_mode))
        except Exception as tts_err:
            print("TTS Error:", tts_err)

        return jsonify({"response": reply, "audio": audio_base64}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "Sorry sir, server error aaya hai."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
