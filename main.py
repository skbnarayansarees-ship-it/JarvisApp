import os
import re
from datetime import datetime
import flet as ft
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------
# 1. SETUP ENVIRONMENT & GLOBAL VARIABLES
# ---------------------------------------------------------
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY") or "YOUR_OPENROUTER_API_KEY"
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
MODEL_NAME = "google/gemini-2.5-flash"

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
# 2. FLET GUI MAIN APPLICATION (WEB CLOUD READY)
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

    def process_query(user_input):
        if not user_input.strip():
            return

        set_status("Processing request...", ft.colors.YELLOW_ACCENT)

        messages = [
            {"role": "system", "content": HINGLISH_PROMPT + get_time_context()},
            {"role": "user", "content": user_input}
        ]

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME, messages=messages, max_tokens=250, temperature=0.7
            )
            reply_text = response.choices[0].message.content.strip()
            append_to_chat("JARVIS", reply_text, is_user=False)
            set_status("Online - Ready", ft.colors.GREEN_ACCENT)
        except Exception as e:
            append_to_chat("JARVIS", f"Mujhe response process karne mein dikkat aayi: {str(e)}", is_user=False)
            set_status("Error", ft.colors.RED_ACCENT)

    def send_click(e):
        user_msg = input_field.value.strip()
        if not user_msg:
            return
        input_field.value = ""
        page.update()
        append_to_chat("You", user_msg, is_user=True)
        process_query(user_msg)

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

    append_to_chat("JARVIS", "Core systems initialized. Online and ready for commands!", is_user=False)
    page.update()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)