Wake word add karne se Jarvis hamesha background me passive wait karega aur jab aap "Hey Jarvis" ya "Jarvis" bologe, tabhi active hokar aapki command sunega aur reply karega.

Step 1: main.py me Wake Word Logic Add Karo
Apne main.py code me ye naya listen_for_wake_word() function aur updated main execution loop replace kar do:

Python
import os
import sys
import time
import webbrowser
import requests
import pyttsx3
import speech_recognition as sr
import pywhatkit
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ------------------- VOICE & TTS ENGINE -------------------
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 175)

def speak(text):
    print(f"Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()

def wish_me():
    hour = int(time.strftime("%H"))
    if 0 <= hour < 12:
        speak("Good Morning Boss!")
    elif 12 <= hour < 18:
        speak("Good Afternoon Boss!")
    else:
        speak("Good Evening Boss!")
    speak("Jarvis is online. Say 'Hey Jarvis' to wake me up.")

# ------------------- WAKE WORD DETECTOR -------------------
def listen_for_wake_word():
    """Background me chup-chaap sunega aur 'Jarvis' detect karega"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[Standby Mode: Waiting for 'Hey Jarvis'...]")
        r.pause_threshold = 0.8
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            # Chote time limits taaki Fast check ho sake
            audio = r.listen(source, timeout=3, phrase_time_limit=3)
            query = r.recognize_google(audio, language='en-IN').lower()
            
            if "jarvis" in query or "hey jarvis" in query:
                print("[Wake Word Detected!]")
                return True
        except Exception:
            return False
    return False

# ------------------- COMMAND LISTENER -------------------
def listen():
    """Wake word ke baad main command sunne ke liye"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("[Active Mode: Listening for your command...]")
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            query = r.recognize_google(audio, language='en-IN').lower()
            print(f"You said: {query}\n")
            return query
        except Exception:
            speak("I couldn't hear you clearly Boss.")
            return ""

# ------------------- OPENROUTER AI INTEGRATION -------------------
def ask_ai(prompt):
    if not OPENROUTER_API_KEY:
        return "Boss, OpenRouter API key missing hai."

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
                "content": "You are Jarvis, an intelligent voice AI. Answer concisely in 2-3 short sentences max."
            },
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            return "Apologies Boss, server error occurred."
    except Exception:
        return "Network connection issue."

# ------------------- MAIN COMMAND PROCESSOR -------------------
def process_command(command):
    if not command:
        return True

    # 1. GAANE & YOUTUBE
    if "play" in command or "gaana" in command:
        song_name = command.replace("play", "").replace("gaana", "").replace("bjao", "").replace("chalao", "").strip()
        if song_name:
            speak(f"Playing {song_name} on YouTube...")
            pywhatkit.playonyt(song_name)

    # 2. SYSTEM APPS
    elif "open notepad" in command:
        speak("Opening Notepad...")
        os.system("notepad")

    elif "open calculator" in command:
        speak("Opening Calculator...")
        os.system("calc")

    elif "open chrome" in command:
        speak("Opening Google Chrome...")
        os.system("start chrome")

    # 3. WEBSITES
    elif "open youtube" in command:
        speak("Opening YouTube...")
        webbrowser.open("https://www.youtube.com")

    elif "open google" in command:
        speak("Opening Google...")
        webbrowser.open("https://www.google.com")

    # 4. EXIT COMMANDS
    elif any(word in command for word in ["exit", "quit", "stop", "bye", "band ho jao"]):
        speak("Goodbye Boss!")
        return False

    # 5. GENERAL QUESTIONS -> AI
    else:
        speak("Thinking...")
        ai_reply = ask_ai(command)
        speak(ai_reply)

    return True

# ------------------- EXECUTION LOOP -------------------
if __name__ == "__main__":
    wish_me()
    running = True
    
    while running:
        # Step 1: Standby Mode me wait karega
        if listen_for_wake_word():
            speak("Yes Boss?")
            
            # Step 2: Wake word milte hi main command sunega
            user_input = listen()
            if user_input:
                running = process_command(user_input)