import os
os.environ["SDL_AUDIODRIVER"] = "dummy"  # Prevents pygame crash on cloud servers
import asyncio  
import json
import os
import re
import subprocess
import tempfile
import threading
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime

import edge_tts
import flet as ft
from dotenv import load_dotenv
from openai import OpenAI
import pygame
import speech_recognition as sr
import vosk

# ---------------------------------------------------------
# 1. SETUP ENVIRONMENT & GLOBAL VARIABLES
# ---------------------------------------------------------
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    api_key = "YOUR_OPENROUTER_API_KEY"

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
MODEL_NAME = "google/gemini-2.5-flash"
VOICE = "en-IN-PrabhatNeural"
active_song_pid = None

pygame.mixer.init()
recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.5
recognizer.dynamic_energy_threshold = True

vosk_model = None
if os.path.exists("model"):
    try:
        vosk_model = vosk.Model("model")
    except Exception as e:
        print(f"Vosk model loading failed: {e}")

HINGLISH_PROMPT = (
    "You are Jarvis, a helpful AI assistant. Always reply in simple, natural "
    "Hinglish (Hindi written using English alphabet). Keep responses short "
    "(maximum 2 to 3 sentences)."
)

def get_time_context():
    now_ist = datetime.now()
    return (
        "\n\n[SYSTEM LIVE CONTEXT] Current Date: "
        f"{now_ist.strftime('%A, %d %B %Y')}, Current Time: "
        f"{now_ist.strftime('%I:%M:%S %p')} IST"
    )

# ---------------------------------------------------------
# 2. SYSTEM COMMAND HANDLERS
# ---------------------------------------------------------
def open_in_chrome(url):
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            try:
                subprocess.Popen([path, "--new-window", url])
                return
            except Exception:
                pass
    webbrowser.open(url)

def handle_close_commands(query, speak_func):
    query_lower = query.lower()
    global active_song_pid

    close_triggers = ["close", "stop", "band", "band kr do", "band karo", "hatao", "क्लोज", "बंद", "हटाo"]
    if not any(ct in query_lower for ct in close_triggers):
        return False

    if any(w in query_lower for w in ["stopwatch", "stop watch", "स्टॉपवॉच", "स्टापवाच"]):
        speak_func("Stopwatch band kar di hai.")
        subprocess.run([
            "powershell", "-Command",
            "Get-Process chrome,msedge -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like '*Stopwatch*'} | Stop-Process -Force"
        ], capture_output=True)
        return True

    if any(w in query_lower for w in ["timer", "time", "टाइमर", "समय", "wakt", "stop time", "stop timer"]):
        speak_func("Timer band kar diya hai.")
        subprocess.run([
            "powershell", "-Command",
            "Get-Process chrome,msedge -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like '*Timer*' -or $_.MainWindowTitle -like '*Countdown*'} | Stop-Process -Force"
        ], capture_output=True)
        return True

    if any(w in query_lower for w in ["match", "cricket", "match schedule", "मैच"]):
        speak_func("Cricket schedule tab band kar diya hai.")
        subprocess.run([
            "powershell", "-Command",
            "Get-Process chrome,msedge -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like '*Cricket*' -or $_.MainWindowTitle -like '*Live Score*'} | Stop-Process -Force"
        ], capture_output=True)
        return True

    if any(w in query_lower for w in ["song", "music", "youtube", "gana"]):
        speak_func("YouTube song band kar raha hoon.")
        if active_song_pid:
            try:
                subprocess.run(["taskkill", "/f", "/t", "/pid", str(active_song_pid)], capture_output=True)
                active_song_pid = None
            except Exception:
                pass
        else:
            subprocess.run([
                "powershell", "-Command",
                "Get-Process chrome,msedge -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like '*YouTube*' -or $_.MainWindowTitle -like '*watch*'} | Stop-Process -Force"
            ], capture_output=True)
        return True

    if "spotify" in query_lower:
        subprocess.run(["taskkill", "/f", "/im", "Spotify.exe"], capture_output=True)
        speak_func("Spotify band kar diya hai.")
        return True

    if "notepad" in query_lower:
        subprocess.run(["taskkill", "/f", "/im", "notepad.exe"], capture_output=True)
        speak_func("Notepad band kar diya hai.")
        return True

    return False

def handle_alarm_timer_stopwatch_cricket(query, speak_func):
    query_lower = query.lower()
    if any(w in query_lower for w in ["close", "stop", "band", "hatao"]):
        return False

    if any(kw in query_lower for kw in ["india ka match", "match kab h", "upcoming match", "cricket match", "match schedule"]):
        speak_func("India ke upcoming cricket matches ka schedule search kar raha hoon.")
        open_in_chrome("https://www.google.com/search?q=india+upcoming+cricket+match+schedule")
        return True

    if any(kw in query_lower for kw in ["stopwatch", "stop watch", "स्टॉपवॉच", "स्टापवाच"]):
        speak_func("Online stopwatch khol raha hoon.")
        open_in_chrome("https://vclock.com/stopwatch/")
        return True

    if any(kw in query_lower for kw in ["alarm", "alaram", "अलार्म"]):
        speak_func("Online alarm khol raha hoon.")
        open_in_chrome("https://vclock.com/alarm/")
        return True

    if any(kw in query_lower for kw in ["timer", "time", "टाइमर", "samay", "wakt", "समय"]):
        match_min = re.search(r"(\d+)\s*(min|minute|minutes|minut|मिनट)", query_lower)
        match_sec = re.search(r"(\d+)\s*(sec|second|seconds|सेकंड)", query_lower)

        total_seconds = 0
        if match_min:
            total_seconds += int(match_min.group(1)) * 60
        if match_sec:
            total_seconds += int(match_sec.group(1))

        if total_seconds > 0:
            speak_func(f"Theek hai, {total_seconds} seconds ka online timer khol raha hoon.")
            open_in_chrome(f"https://www.google.com/search?q=timer+for+{total_seconds}+seconds")
        else:
            speak_func("Online timer khol raha hoon.")
            open_in_chrome("https://vclock.com/timer/")
        return True

    return False

def play_direct_youtube(song_query):
    global active_song_pid
    try:
        search_term = f"{song_query} official song"
        query_string = urllib.parse.urlencode({"search_query": search_term})
        html_content = urllib.request.urlopen(
            urllib.request.Request(
                f"https://www.youtube.com/results?search_query={query_string}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
        ).read().decode("utf-8")
        matches = re.findall(r"\/watch\?v=([a-zA-Z0-9_-]{11})", html_content)
        if matches:
            watch_url = f"https://www.youtube.com/watch?v={matches[0]}"
            for path in [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
            ]:
                if os.path.exists(path):
                    proc = subprocess.Popen([path, "--new-window", watch_url])
                    active_song_pid = proc.pid
                    return
            webbrowser.open(watch_url)
    except Exception:
        open_in_chrome(f"https://www.youtube.com/results?search_query={urllib.parse.quote(song_query + ' song')}")

def handle_music_commands(query_lower, speak_func):
    if any(w in query_lower for w in ["close", "stop", "band", "hatao"]):
        return False
    if any(pt in query_lower for pt in ["play", "chalao", "bajao", "sunao", "चलाओ", "बजाओ", "सुनाओ", "प्ले", "song", "gana"]):
        cleaned = query_lower
        for w in ["play", "chalao", "bajao", "sunao", "चलाओ", "बजाओ", "सुनाओ", "प्ले", "song", "gana", "youtube", "on"]:
            cleaned = cleaned.replace(w, "")
        song_query = cleaned.strip()
        if song_query:
            speak_func(f"YouTube par {song_query} chala raha hoon.")
            threading.Thread(target=lambda: play_direct_youtube(song_query), daemon=True).start()
            return True
    return False

def handle_app_commands(query_lower, speak_func):
    if any(w in query_lower for w in ["close", "stop", "band", "hatao"]):
        return False

    if "spotify" in query_lower:
        speak_func("Spotify khol raha hoon.")
        subprocess.Popen(["start", "spotify:"], shell=True)
        return True

    app_rules = {
        "notepad": ["notepad", "नोटपैड"],
        "chrome": ["chrome", "क्रोम"],
        "calculator": ["calculator", "calc", "कैलकुलेटर"],
        "youtube": ["youtube", "यूट्यूब"],
    }
    for app_key, keywords in app_rules.items():
        if any(kw in query_lower for kw in keywords):
            if app_key == "notepad":
                speak_func("Notepad khol raha hoon.")
                subprocess.Popen(["start", "notepad"], shell=True)
            elif app_key == "chrome":
                speak_func("Google Chrome khol raha hoon.")
                open_in_chrome("https://www.google.com")
            elif app_key == "calculator":
                speak_func("Calculator khol raha hoon.")
                subprocess.Popen(["start", "calc"], shell=True)
            elif app_key == "youtube":
                speak_func("YouTube khol raha hoon.")
                open_in_chrome("https://www.youtube.com")
            return True
    return False

# ---------------------------------------------------------
# 3. FLET GUI MAIN APPLICATION
# ---------------------------------------------------------
def main(page: ft.Page):
    page.title = "JARVIS AI ASSISTANT"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0B0F19"
    page.padding = 20

    # --- UI Components ---
    title = ft.Text("JARVIS ONLINE", size=26, color=ft.colors.CYAN_ACCENT, weight=ft.FontWeight.BOLD)
    status = ft.Text("Status: Core systems ready...", size=14, color=ft.colors.WHITE70)

    chat_list = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    def set_status(text, color=ft.colors.WHITE70):
        status.value = f"Status: {text}"
        status.color = color
        page.update()

    def append_to_chat(sender, message, is_user=False):
        bg_color = "#1E293B" if is_user else "#0F172A"
        align = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        border_col = ft.colors.CYAN_700 if is_user else ft.colors.BLUE_700

        chat_card = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(sender, size=12, weight=ft.FontWeight.BOLD, color=ft.colors.CYAN_200),
                            ft.Text(message, size=15, color=ft.colors.WHITE, selectable=True),
                        ],
                        spacing=3,
                    ),
                    padding=12,
                    border_radius=12,
                    bgcolor=bg_color,
                    border=ft.border.all(1, border_col),
                    width=450,
                )
            ],
            alignment=align,
        )
        chat_list.controls.append(chat_card)
        page.update()

    def speak(text):
        append_to_chat("JARVIS", text, is_user=False)
        set_status("Speaking...", ft.colors.GREEN_ACCENT)

        clean_text = re.sub(r"[\*\#\_\`\~\>]", "", text).strip()
        temp_audio_file = os.path.join(tempfile.gettempdir(), f"jarvis_tts_{datetime.now().timestamp()}.mp3")

        async def _generate_audio():
            communicate = edge_tts.Communicate(clean_text, VOICE, rate="+0%")
            await communicate.save(temp_audio_file)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_generate_audio())
            loop.close()

            if os.path.exists(temp_audio_file):
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass

                pygame.mixer.music.load(temp_audio_file)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

                pygame.mixer.music.unload()
                os.remove(temp_audio_file)

        except Exception as e:
            print(f"Audio Generation/Playback Error: {e}")

        set_status("Listening...", ft.colors.WHITE70)

    def listen():
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                try:
                    query = recognizer.recognize_google(audio, language="hi-IN")
                    if query.strip():
                        append_to_chat("You (Voice)", query, is_user=True)
                        return query.lower()
                except Exception:
                    if vosk_model:
                        raw_audio_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                        rec = vosk.KaldiRecognizer(vosk_model, 16000)
                        if rec.AcceptWaveform(raw_audio_data):
                            result = json.loads(rec.Result())
                            query = result.get("text", "")
                            if query.strip():
                                append_to_chat("You (Offline Voice)", query, is_user=True)
                                return query.lower()
                    return ""
            except Exception:
                return ""

    def process_query(user_input):
        if not user_input.strip():
            return

        set_status("Processing request...", ft.colors.YELLOW_ACCENT)

        if handle_close_commands(user_input, speak):
            return
        if handle_alarm_timer_stopwatch_cricket(user_input, speak):
            return
        if handle_music_commands(user_input, speak):
            return
        if handle_app_commands(user_input, speak):
            return

        messages = [
            {"role": "system", "content": HINGLISH_PROMPT + get_time_context()},
            {"role": "user", "content": user_input}
        ]

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME, messages=messages, max_tokens=250, temperature=0.7
            )
            reply_text = response.choices[0].message.content.strip()
            speak(reply_text)
        except Exception as e:
            speak(f"Mujhe response process karne mein dikkat aayi: {str(e)}")

    def background_assistant_loop():
        speak("Core systems initialized. Voice and typed commands active.")
        while True:
            user_input = listen()
            if not user_input:
                continue

            if any(w in user_input for w in ["exit system", "shutdown jarvis", "bye jarvis", "बाय"]):
                speak("Goodbye! System power down.")
                break

            process_query(user_input)

    def send_click(e):
        user_msg = input_field.value.strip()
        if not user_msg:
            return
        input_field.value = ""
        page.update()
        append_to_chat("You (Typed)", user_msg, is_user=True)
        threading.Thread(target=process_query, args=(user_msg,), daemon=True).start()

    input_field = ft.TextField(
        hint_text="Type a command or ask something...",
        expand=True,
        border_color=ft.colors.CYAN_400,
        border_radius=20,
        on_submit=send_click
    )

    send_btn = ft.IconButton(
        icon=ft.icons.SEND_ROUNDED,
        icon_color=ft.colors.CYAN_400,
        on_click=send_click
    )

    input_row = ft.Row(
        controls=[input_field, send_btn],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    page.add(
        title,
        status,
        ft.Divider(color=ft.colors.CYAN_900),
        chat_list,
        input_row,
    )
    page.update()

    # Start Voice Listening Background Thread
    threading.Thread(target=background_assistant_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)