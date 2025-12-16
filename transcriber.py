import os
import tempfile
import subprocess
import sys
from pydub import AudioSegment
from whisper_api import WhisperAPI

# Configura o subprocess para suprimir janelas de terminal no Windows
if sys.platform == "win32":
    # Salva a função original do Popen
    _original_popen = subprocess.Popen
    
    # Cria uma versão silenciosa do Popen para Windows
    def _silent_popen(*args, **kwargs):
        """Wrapper do subprocess.Popen que suprime janelas de terminal no Windows"""
        # Redireciona stdout e stderr para DEVNULL
        kwargs.setdefault('stdout', subprocess.DEVNULL)
        kwargs.setdefault('stderr', subprocess.DEVNULL)
        
        # Configura para não mostrar janela de terminal
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        
        return _original_popen(*args, **kwargs)
    
    # Aplica o monkey patch globalmente
    subprocess.Popen = _silent_popen

class Transcriber:
    def __init__(self, model="gpt-4o-mini-transcribe", use_diarization=False):
        self.api = WhisperAPI()
        self.model = model
        self.use_diarization = use_diarization
        self.MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB em bytes
        self.CHUNK_SIZE = 24 * 1024 * 1024  # 24MB por chunk (margem de segurança)

    def transcribe_audio(self, filepath, model=None, use_diarization=None):
        """
        Transcreve um arquivo de áudio
        
        Args:
            filepath: Caminho para o arquivo de áudio
            model: Modelo a ser usado (usa self.model se None)
            use_diarization: Se True, usa diarização (usa self.use_diarization se None)
        """
        # Usa parâmetros fornecidos ou os padrões da instância
        model = model if model is not None else self.model
        use_diarization = use_diarization if use_diarization is not None else self.use_diarization
        
        file_size = self.api.get_file_size(filepath)
        
        # Se o arquivo for menor que 25MB, processa normalmente
        if file_size <= self.MAX_FILE_SIZE:
            return self.api.transcribe(filepath, model=model, use_diarization=use_diarization)
        
        # Se for maior, divide e processa em partes
        return self._transcribe_large_file(filepath, model, use_diarization)
    
    def _transcribe_large_file(self, filepath, model, use_diarization):
        """Divide um arquivo grande em partes menores e transcreve cada uma independentemente"""
        transcriptions = []
        temp_files = []
        
        try:
            # Carrega o áudio (a saída do ffmpeg já está suprimida pelo monkey patch)
            audio = AudioSegment.from_file(filepath)
            duration_ms = len(audio)
            
            # Calcula a duração aproximada de cada chunk (em milissegundos)
            # Estima baseado no tamanho do arquivo original
            file_size = self.api.get_file_size(filepath)
            bytes_per_ms = file_size / duration_ms if duration_ms > 0 else 1
            chunk_duration_ms = int(self.CHUNK_SIZE / bytes_per_ms)
            
            # Garante um tamanho mínimo de chunk (pelo menos 1 minuto ou 10% do arquivo)
            min_chunk_duration = min(60000, duration_ms // 10)
            chunk_duration_ms = max(chunk_duration_ms, min_chunk_duration)
            
            # Processa o áudio em chunks (cada um transcrito independentemente)
            start_ms = 0
            chunk_number = 1
            
            while start_ms < duration_ms:
                end_ms = min(start_ms + chunk_duration_ms, duration_ms)
                chunk = audio[start_ms:end_ms]
                
                # Salva o chunk temporariamente
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_path = temp_file.name
                temp_file.close()
                temp_files.append(temp_path)
                
                try:
                    # Exporta o chunk
                    chunk.export(temp_path, format="mp3", bitrate="128k")
                    
                    # Verifica se o chunk ainda é muito grande e ajusta se necessário
                    chunk_size = os.path.getsize(temp_path)
                    current_start = start_ms
                    current_end = end_ms
                    
                    # Se o chunk for muito grande, reduz progressivamente
                    while chunk_size > self.MAX_FILE_SIZE and (current_end - current_start) > 10000:  # Mínimo de 10 segundos
                        # Reduz pela metade
                        current_end = current_start + (current_end - current_start) // 2
                        chunk = audio[current_start:current_end]
                        chunk.export(temp_path, format="mp3", bitrate="128k")
                        chunk_size = os.path.getsize(temp_path)
                    
                    # Se ainda for muito grande após reduções, usa um bitrate menor
                    if chunk_size > self.MAX_FILE_SIZE:
                        chunk.export(temp_path, format="mp3", bitrate="64k")
                        chunk_size = os.path.getsize(temp_path)
                    
                    # Transcreve o chunk independentemente (sem contexto de chunks anteriores)
                    transcription = self.api.transcribe(
                        temp_path, 
                        model=model, 
                        use_diarization=use_diarization
                    )
                    
                    if transcription and transcription.strip():
                        transcriptions.append(transcription.strip())
                    
                    # Atualiza o ponto de início para o próximo chunk
                    start_ms = current_end
                    chunk_number += 1
                    
                except Exception as e:
                    # Se houver erro ao processar um chunk, continua com os próximos
                    print(f"Erro ao processar chunk {chunk_number}: {str(e)}")
                    start_ms = end_ms
                    chunk_number += 1
                finally:
                    # Remove o arquivo temporário
                    if os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
            
            # Combina todas as transcrições com espaços entre elas
            if not transcriptions:
                raise Exception("Não foi possível transcrever nenhuma parte do arquivo.")
            
            return "\n\n".join(transcriptions)
            
        except Exception as e:
            # Limpa arquivos temporários em caso de erro
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            
            # Se já tiver algumas transcrições, retorna o que conseguiu
            if transcriptions:
                return "\n\n".join(transcriptions)
            raise e
