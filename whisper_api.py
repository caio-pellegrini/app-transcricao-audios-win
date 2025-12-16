import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class WhisperAPI:
    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.client = OpenAI(api_key=self.api_key)
        self.MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB em bytes

    def get_file_size(self, filepath):
        """Retorna o tamanho do arquivo em bytes"""
        return os.path.getsize(filepath)

    def transcribe(self, filepath):
        audio_file = open(filepath, "rb")
        transcription = self.client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            response_format="text"
        )
        audio_file.close()
        return transcription

