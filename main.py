from flask import Flask, render_template, request, jsonify
import urllib.request
import urllib.parse
import re
import time
import os
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# API Key Setup
api_key = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

global_state = {
    "action": "none",
    "payload": "",
    "timestamp": time.time()
}

system_instruction = """
You are Jarvis, an advanced, highly empathetic, and human-like AI assistant. 
- You have real-time internet access provided via prompts. Always act like you know the latest current affairs.
- If the user speaks in English, reply in English. 
- If the user speaks in Hinglish (Hindi written in English script), reply completely in Hinglish.
- Act like a caring friend. If they say "mujhe accha nhin lg rhaa", "kya kar rahe ho", or sound sad, show deep empathy, console them, and ask what's bothering them naturally.
- Keep your responses short, natural, clear, and conversational.
"""

def search_youtube(query):
    """Instant YouTube Search"""
    query_string = urllib.parse.urlencode({"search_query": query})
    html_content = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
    search_results = re.findall(r'watch\?v=(\S{11})', html_content.read().decode())
    if search_results:
        return search_results[0]
    return None

def get_latest_news(query):
    """Real-Time Internet Search via Google News RSS"""
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        resp = requests.get(url, timeout=5)
        root = ET.fromstring(resp.content)
        news_items = []
        for item in root.findall('.//item')[:3]:
            title = item.find('title').text
            news_items.append(title)
        if news_items:
            return "Live Web Info: " + " | ".join(news_items)
    except Exception:
        pass
    return ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global global_state
    user_msg = request.json.get('message', '').lower()
    
    # 1. YouTube Play Command
    if 'play' in user_msg:
        song_name = user_msg.replace('jarvis', '').replace('play', '').strip()
        video_id = search_youtube(song_name)
        
        if video_id:
            global_state = {
                "action": "play_youtube",
                "payload": video_id,
                "timestamp": time.time()
            }
            return jsonify({"response": f"Playing {song_name} for everyone right away, boss.", "action": "play"})
        else:
            return jsonify({"response": "Sorry boss, gaana nahi mila."})

    # 2. Check for News / Latest Info
    real_time_context = ""
    trigger_words = ['news', 'latest', 'aaj', 'kal', 'kaun', 'match', 'score', 'kya chal raha hai', 'kya kar rahe ho']
    if any(word in user_msg for word in trigger_words):
        real_time_context = get_latest_news(user_msg.replace('jarvis', '').strip())

    if real_time_context:
        full_prompt = f"Real-Time Data: {real_time_context}\n\nUser: {user_msg}"
    else:
        full_prompt = "User: " + user_msg

    try:
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(system_instruction + "\n" + full_prompt)
        ai_reply = response.text.strip()
    except Exception:
        ai_reply = "Network mein thodi dikkat hai boss."

    return jsonify({"response": ai_reply, "action": "chat"})

@app.route('/sync', methods=['GET'])
def sync_devices():
    global global_state
    return jsonify(global_state)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
