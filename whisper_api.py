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


# TESTES FURUTOS PARA RESOLVER PROBLEMAS DE IMPORTAÇÃO DE AUDIOS LONGOS
# from openai import OpenAI
# from pydub import AudioSegment
# import os

# class WhisperAPI:
#     def __init__(self, api_key):
#         self.api_key = api_key
#         self.client = OpenAI(api_key=self.api_key)
#         self.segment_duration_ms = 5 * 60 * 1000  # 5 minutos em milissegundos

#     def transcribe(self, filepath):
#         audio = AudioSegment.from_file(filepath)
#         audio_segments = self.split_audio(audio, self.segment_duration_ms)
        
#         transcription_texts = []
#         for i, segment in enumerate(audio_segments):
#             segment_path = self.export_segment(segment, i)
#             with open(segment_path, 'rb') as audio_file:
#                 transcription = self.client.audio.transcriptions.create(
#                     model="whisper-1",
#                     file=audio_file,
#                     response_format="text"
#                 )
#                 transcription_texts.append(transcription['text'])
#             os.remove(segment_path)
        
#         return " ".join(transcription_texts)

#     def split_audio(self, audio, segment_duration_ms):
#         segments = []
#         for start_ms in range(0, len(audio), segment_duration_ms):
#             end_ms = start_ms + segment_duration_ms
#             segments.append(audio[start_ms:end_ms])
#         return segments

#     def export_segment(self, segment, index):
#         segment_path = f"segment_temp_{index}.mp3"
#         segment.export(segment_path, format="mp3")
#         return segment_path
