import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class WhisperAPI:
    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.client = OpenAI(api_key=self.api_key)

    def transcribe(self, filepath):
        audio_file = open(filepath, "rb")
        transcription = self.client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            response_format="text"
        )
        return transcription

