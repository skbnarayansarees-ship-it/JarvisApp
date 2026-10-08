from flask import Flask, request, jsonify, render_template, send_file
from pathlib import Path
from urllib.parse import quote
import asyncio
import os
import tempfile
import uuid

import requests
import edge_tts
import yt_dlp


app = Flask(__name__)

PORT = int(os.environ.get("PORT", "5000"))

BASE_DIR = Path(__file__).resolve().parent

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "deepseek/deepseek-chat"

OPENROUTER_API_KEY = os.environ.get(
    "OPENROUTER_API_KEY",
    ""
).strip()

# Local development only.
# Do NOT upload this file to GitHub.
if not OPENROUTER_API_KEY:
    key_file = BASE_DIR / "openrouter_key.txt"

    if key_file.exists():
        try:
            OPENROUTER_API_KEY = (
                key_file
                .read_text(encoding="utf-8")
                .strip()
            )
        except Exception:
            OPENROUTER_API_KEY = ""

TTS_VOICE = "en-IN-PrabhatNeural"


ENGLISH_SYSTEM_PROMPT = """
You are JARVIS, a helpful AI assistant.

The user selected English.

Reply naturally and conversationally.
Do not use unnecessary markdown.
Do not use emojis unless the user asks.
Do not claim to have live/current information unless the application
actually provides it.
"""

HINGLISH_SYSTEM_PROMPT = """
You are JARVIS, a friendly AI assistant.

The user selected Hinglish.

Reply in natural everyday Indian Hinglish.
Sound like a normal person, not a textbook.
Mix Hindi and English naturally.
Do not use unnecessary markdown.
Do not use emojis unless the user asks.
Do not claim to have live/current information unless the application
actually provides it.
"""


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "success": True,
        "message": "Jarvis server is running"
    })


@app.route("/ask-ai", methods=["POST"])
def ask_ai():
    try:
        data = request.get_json(silent=True) or {}

        prompt = str(data.get("prompt", "")).strip()
        language = str(
            data.get("language", "english")
        ).lower().strip()

        if not prompt:
            return jsonify({
                "success": False,
                "error": "Please enter a message."
            }), 400

        if not OPENROUTER_API_KEY:
            return jsonify({
                "success": False,
                "error": "OpenRouter API key is not configured."
            }), 500

        system_prompt = (
            HINGLISH_SYSTEM_PROMPT
            if language == "hinglish"
            else ENGLISH_SYSTEM_PROMPT
        )

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": request.host_url.rstrip("/"),
            "X-Title": "JARVIS AI Assistant",
        }

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }

        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=90,
        )

        if response.status_code != 200:
            try:
                error_data = response.json()
                error_message = (
                    error_data
                    .get("error", {})
                    .get("message")
                )
            except Exception:
                error_message = None

            if not error_message:
                error_message = response.text

            return jsonify({
                "success": False,
                "error": f"OpenRouter error: {error_message}"
            }), 502

        result = response.json()

        choices = result.get("choices", [])

        if not choices:
            return jsonify({
                "success": False,
                "error": "OpenRouter returned no answer."
            }), 502

        answer = (
            choices[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not answer:
            return jsonify({
                "success": False,
                "error": "OpenRouter returned an empty response."
            }), 502

        return jsonify({
            "success": True,
            "answer": answer
        })

    except requests.Timeout:
        return jsonify({
            "success": False,
            "error": "AI request timed out."
        }), 504

    except Exception as exc:
        print("ASK AI ERROR:", repr(exc))

        return jsonify({
            "success": False,
            "error": "AI server error."
        }), 500


async def generate_tts(text, output_path):
    communicator = edge_tts.Communicate(
        text,
        TTS_VOICE,
        rate="+0%",
        volume="+0%",
    )

    await communicator.save(output_path)


@app.route("/speak", methods=["POST"])
def speak():
    temp_path = None

    try:
        data = request.get_json(silent=True) or {}

        text = str(data.get("text", "")).strip()

        if not text:
            return jsonify({
                "success": False,
                "error": "No text provided."
            }), 400

        text = text[:20000]

        filename = (
            f"jarvis_{uuid.uuid4().hex}.mp3"
        )

        temp_path = os.path.join(
            tempfile.gettempdir(),
            filename
        )

        asyncio.run(
            generate_tts(
                text,
                temp_path
            )
        )

        if not os.path.exists(temp_path):
            raise RuntimeError(
                "TTS file was not created."
            )

        response = send_file(
            temp_path,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="jarvis.mp3",
            max_age=0,
        )

        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as exc:
                print("TTS CLEANUP ERROR:", repr(exc))

        return response

    except Exception as exc:
        print("TTS ERROR:", repr(exc))

        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

        return jsonify({
            "success": False,
            "error": "Voice generation failed."
        }), 500


@app.route("/youtube", methods=["POST"])
def youtube():
    try:
        data = request.get_json(silent=True) or {}

        query = str(
            data.get("query", "")
        ).strip()

        if not query:
            return jsonify({
                "success": False,
                "error": "No YouTube query provided."
            }), 400

        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                "ytsearch1:" + query,
                download=False
            )

        entries = info.get("entries", [])

        if not entries:
            search_url = (
                "https://www.youtube.com/results"
                "?search_query="
                + quote(query)
            )

            return jsonify({
                "success": True,
                "video_id": None,
                "title": query,
                "url": search_url,
            })

        entry = entries[0]

        video_id = entry.get("id")
        title = entry.get("title") or query

        if video_id:
            video_url = (
                "https://www.youtube.com/watch?v="
                + str(video_id)
            )

            return jsonify({
                "success": True,
                "video_id": video_id,
                "title": title,
                "url": video_url,
            })

        search_url = (
            "https://www.youtube.com/results"
            "?search_query="
            + quote(query)
        )

        return jsonify({
            "success": True,
            "video_id": None,
            "title": query,
            "url": search_url,
        })

    except Exception as exc:
        print("YOUTUBE ERROR:", repr(exc))

        search_url = (
            "https://www.youtube.com/results"
            "?search_query="
            + quote(
                str(
                    (request.get_json(silent=True) or {})
                    .get("query", "music")
                )
            )
        )

        return jsonify({
            "success": True,
            "video_id": None,
            "title": "YouTube search",
            "url": search_url,
        })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )
