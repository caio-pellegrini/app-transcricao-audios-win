from whisper_api import WhisperAPI

class Transcriber:
    def __init__(self):
        self.api = WhisperAPI()

    def transcribe_audio(self, filepath):
        return self.api.transcribe(filepath)
