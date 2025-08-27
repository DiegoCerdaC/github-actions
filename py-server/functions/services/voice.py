import requests, base64, io
from config import OPENAI_API_KEY

def base64_to_blob(base64_string):
    try:
        # Decode base64 string to bytes
        audio_bytes = base64.b64decode(base64_string)

        # Create a file-like object
        audio_file = io.BytesIO(audio_bytes)
        
        return audio_file
    except Exception as e:
        print(f"Error converting base64 to blob: {str(e)}")
        raise e

def encode_audio_to_base64(audio):
    try:
        # Ensure we're working with bytes
        if not isinstance(audio, bytes):
            raise ValueError(f"Expected bytes, got {type(audio)}")

        base64_encoded_data = base64.b64encode(audio)
        base64_string = base64_encoded_data.decode("utf-8")

        return base64_string
    except Exception as e:
        print(f"Error in encode_audio_to_base64: {str(e)}")
        raise e

def transcribe_audio(base64_audio):
    try:
        audio_data = base64_to_blob(base64_audio)
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        form_data = {
            "model": "whisper-1",
            "language": "en"
        }
        files = {
            "file": ("audio.mp3", audio_data)
        }
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            data=form_data,
            files=files
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}")
            
        result = response.json()
        if not isinstance(result, dict) or "text" not in result:
            raise ValueError(f"Unexpected API response format: {result}")

        return result["text"]
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}", flush=True)
        raise e

def generate_speech_from_text(text: str):
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini-tts",
            "input": text,
            "voice": "alloy",
            "instructions": "friendly, upbeat"
        }
        response = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.reason}")
            
        return response.content
    except Exception as e:
        print(f"Error generating speech: {str(e)}", flush=True)
        raise e
