import os
import io
from groq import Groq
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=60.0)


def speech_to_text(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """User ki awaaz ko text mein convert karo (Groq Whisper)."""
    transcription = groq_client.audio.transcriptions.create(
        file=(filename, audio_bytes),
        model="whisper-large-v3",
        response_format="text"
    )
    return transcription


def text_to_speech(text: str) -> bytes:
    """Text ko awaaz mein convert karo (Google TTS - English only)."""
    tts = gTTS(text=text, lang='en', slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()


# Test
if __name__ == "__main__":
    print("Testing TTS...")
    audio = text_to_speech("Hello! I am GlamourBot, your personal fashion assistant.")
    with open("test_output.mp3", "wb") as f:
        f.write(audio)
    print("[DONE] test_output.mp3 saved!")