import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_TTS_CHARS = 1000  # safe limit to avoid truncated/cut-off audio


def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        transcription = groq_client.audio.transcriptions.create(
            file=f,
            model="whisper-large-v3",
        )
    return transcription.text


def synthesize_speech(text, output_path, voice="troy"):
    if len(text) > MAX_TTS_CHARS:
        text = text[:MAX_TTS_CHARS].rsplit(".", 1)[0] + ". (Full details sent as text.)"

    response = groq_client.audio.speech.create(
        model="canopylabs/orpheus-v1-english",
        voice=voice,
        input=text,
        response_format="wav",
    )
    with open(output_path, "wb") as f:
        f.write(response.read())
    return output_path
