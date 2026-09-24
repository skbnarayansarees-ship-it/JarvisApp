import os
import sys
import re
import subprocess
import asyncio
from datetime import datetime
import flet as ft
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------
# 1. CLOUD DETECT & DUMMY AUDIO FALLBACK
# ---------------------------------------------------------
# Render par hardware audio crash rokne ke liye
IS_CLOUD = "RENDER" in os.environ or "PORT" in os.environ

if IS_CLOUD:
    os.environ["SDL_AUDIODRIVER"] = "dummy"

# Pygame & Speech Recognition imports with safety
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False

# ---------------------------------------------------------
# 2. ENVIRONMENT & API SETUP
# ---------------------------------------------------------
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY") or "YOUR_OPENROUTER_API_KEY"
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
MODEL_NAME = "google/gemini-2.5-flash"

HINGLISH_PROMPT = (
    "You are Jarvis, an advanced AI assistant. Always reply in simple, natural "
    "Hinglish (Hindi written using English alphabet). Keep responses short and helpful "
    "(maximum 2 to 3 sentences)."
)

def get_time_context():
    now = datetime.now()
    return (
        f"\n\n[SYSTEM LIVE CONTEXT] Current Date: {now.strftime('%A, %d %B %Y')}, "
        f"Current Time: {now.strftime('%I:%M:%S %p')}"
    )

# ---------------------------------------------------------
# 3. LOCAL SYSTEM COMMAND HANDLER
# ---------------------------------------------------------
def handle_system_commands(user_input: str) -> str | None:
    """Handles PC commands locally. On Cloud, gives a friendly notification."""
    cmd = user_input.lower()
    
    # PC-only actions
    if "open chrome" in cmd or "chrome kholo" in cmd:
        if IS_CLOUD:
            return "Chrome aapke local PC par khulega. Render cloud server par local apps run nahi ho sakti."
        try:
            subprocess.Popen(["start", "chrome"], shell=True)
            return "Opening Google Chrome on your computer..."
        except Exception as e:
            return f"Chrome open nahi ho paaya: {str(e)}"

    elif "open notepad" in cmd or "notepad kholo" in cmd:
        if IS_CLOUD:
            return "Notepad local PC app hai. Cloud web version me ye text-chat mode me available hai."
        try:
            subprocess.Popen(["notepad"])
            return "Notepad opened!"
        except Exception as e:
            return f"Notepad open nahi ho paaya: {str(e)}"

    elif "open calculator" in cmd or "calculator kholo" in cmd:
        if IS_CLOUD:
            return "Calculator local PC par chalne wali app hai."
        try:
            subprocess.Popen(["calc"])
            return "Opening Calculator..."
        except Exception as e:
            return f"Calculator open nahi hua: {str(e)}"

    elif "time" in cmd or "samay" in cmd or "wakt" in cmd:
        now = datetime.now().strftime("%I:%M %p")
        return f"Abhi time ho raha hai: {now}"

    elif "date" in cmd or "tareek" in cmd:
        today = datetime.now().strftime("%d %B %Y")
        return f"Aaj ki date hai: {today}"

    return None

# ---------------------------------------------------------
# 4. FLET GUI APPLICATION
# ---------------------------------------------------------
def main(page: ft.Page):
    page.title = "JARVIS AI ASSISTANT"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0B0F19"
    page.padding = 20

    # Header Controls
    title = ft.Text("JARVIS AI SYSTEM", size=24, color=ft.colors.CYAN_ACCENT, weight=ft.FontWeight.BOLD)
    env_tag = "CLOUD WEB MODE" if IS_CLOUD else "LOCAL DESKTOP MODE"
    subtitle = ft.Text(f"Status: Online ({env_tag})", size=13, color=ft.colors.GREEN_400)

    # Chat Log Container
    chat_list = ft.ListView(
        expand=True,
        spacing=12,
        auto_scroll=True,
    )

    def append_chat(sender: str, text: str, is_user: bool = False):
        bg = "#1E293B" if is_user else "#0F172A"
        border_col = ft.colors.CYAN_600 if is_user else ft.colors.BLUE_700
        align = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START

        card = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(sender, size=11, weight=ft.FontWeight.BOLD, color=ft.colors.CYAN_200),
                            ft.Text(text, size=14, color=ft.colors.WHITE, selectable=True),
                        ],
                        spacing=4,
                    ),
                    padding=12,
                    border_radius=10,
                    bgcolor=bg,
                    border=ft.border.all(1, border_col),
                    width=420,
                )
            ],
            alignment=align,
        )
        chat_list.controls.append(card)
        page.update()

    def process_query(user_msg: str):
        if not user_msg.strip():
            return

        # Check for local system commands first
        sys_response = handle_system_commands(user_msg)
        if sys_response:
            append_chat("JARVIS", sys_response, is_user=False)
            return

        # Otherwise query Gemini via OpenRouter
        try:
            messages = [
                {"role": "system", "content": HINGLISH_PROMPT + get_time_context()},
                {"role": "user", "content": user_msg}
            ]
            
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()
            append_chat("JARVIS", reply, is_user=False)

        except Exception as e:
            append_chat("JARVIS", f"API Request error: {str(e)}", is_user=False)

    def on_send_click(e):
        text = user_input.value.strip()
        if not text:
            return
        user_input.value = ""
        page.update()
        
        append_chat("You", text, is_user=True)
        process_query(text)

    # Input Fields
    user_input = ft.TextField(
        hint_text="Ask JARVIS or type a command...",
        expand=True,
        border_color=ft.colors.CYAN_500,
        border_radius=15,
        on_submit=on_send_click,
    )

    send_button = ft.IconButton(
        icon=ft.icons.SEND_ROUNDED,
        icon_color=ft.colors.CYAN_400,
        on_click=on_send_click,
    )

    input_layout = ft.Row(
        controls=[user_input, send_button],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # Adding controls to main page
    page.add(
        title,
        subtitle,
        ft.Divider(color=ft.colors.CYAN_900),
        chat_list,
        input_layout,
    )

    # Welcome Message
    append_chat("JARVIS", f"Systems fully online in {env_tag}. Main ready for input!", is_user=False)

# ---------------------------------------------------------
# 5. ENTRY POINT (WEB & LOCAL COMPATIBLE)
# ---------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port
    )