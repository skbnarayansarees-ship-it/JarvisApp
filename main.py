from flask import Flask, render_template, request, jsonify
import urllib.request
import urllib.parse
import re
import time
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# API Key setup (Use .env file for safety)
api_key = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# Yeh variable sab devices ko sync rakhega
global_state = {
    "action": "none",
    "payload": "",
    "timestamp": time.time()
}

# Jarvis ka Dimag (System Prompt)
system_instruction = """
You are Jarvis, an advanced, highly empathetic, and human-like AI assistant. 
- If the user speaks in English, reply in English. 
- If the user speaks in Hinglish (Hindi written in English) or Hindi, reply completely in Hinglish.
- Act like a caring friend, NOT a robot.
- If they ask "kyaa kr rhe ho?", reply casually like: "Bas aapka hi intezaar tha, bataiye kya chal raha hai?"
- If they say "mujhe accha nhin lg rhaa" or sound sad, show deep empathy, console them, and ask what's bothering them. Offer good human-like advice.
Keep your responses short, natural, and conversational.
"""

def search_youtube(query):
    """Bina yt-dlp ke direct fast search for instant play"""
    query_string = urllib.parse.urlencode({"search_query": query})
    html_content = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
    search_results = re.findall(r'watch\?v=(\S{11})', html_content.read().decode())
    if search_results:
        return search_results[0]
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global global_state
    user_msg = request.json.get('message', '').lower()
    
    # 1. Check if user wants to play a song
    if 'play' in user_msg:
        # Extract song name
        song_name = user_msg.replace('jarvis', '').replace('play', '').strip()
        video_id = search_youtube(song_name)
        
        if video_id:
            # Update global state so ALL devices play it
            global_state = {
                "action": "play_youtube",
                "payload": video_id,
                "timestamp": time.time()
            }
            return jsonify({"response": f"Playing {song_name} for everyone right away, boss.", "action": "play"})
        else:
            return jsonify({"response": "Sorry boss, gaana nahi mila."})

    # 2. Normal Chat via Gemini with Human Empathy
    try:
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(system_instruction + "\nUser: " + user_msg)
        ai_reply = response.text.strip()
    except Exception as e:
        ai_reply = "Network mein kuch dikkat hai boss, baad mein try karein."

    return jsonify({"response": ai_reply, "action": "chat"})

@app.route('/sync', methods=['GET'])
def sync_devices():
    """Sabhi connected devices har 2 second mein yahan se check karenge ki kya play karna hai"""
    global global_state
    return jsonify(global_state)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
