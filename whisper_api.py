import os
from openai import OpenAI
from dotenv import load_dotenv

# Tenta carregar do .env (para desenvolvimento)
# Se não existir, não é problema - vamos usar variáveis de ambiente do sistema
load_dotenv()

class WhisperAPI:
    def __init__(self):
        # Tenta obter a API_KEY de várias fontes:
        # 1. Variável de ambiente OPENAI_API_KEY (padrão da OpenAI)
        # 2. Variável de ambiente API_KEY (do .env)
        # 3. Variável de ambiente do sistema
        self.api_key = os.getenv('OPENAI_API_KEY') or os.getenv('API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "API_KEY não configurada!\n\n"
                "Por favor, configure a chave da API OpenAI de uma das seguintes formas:\n\n"
                "1. Variável de ambiente do sistema:\n"
                "   - Windows (PowerShell): $env:OPENAI_API_KEY='sua-chave-aqui'\n"
                "   - Windows (CMD): set OPENAI_API_KEY=sua-chave-aqui\n"
                "   - Linux/Mac: export OPENAI_API_KEY='sua-chave-aqui'\n\n"
                "2. Arquivo .env na mesma pasta do executável:\n"
                "   Crie um arquivo chamado '.env' com: OPENAI_API_KEY=sua-chave-aqui\n\n"
                "3. Ou use: API_KEY=sua-chave-aqui (alternativa)"
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB em bytes
        
        # Modelos disponíveis
        self.MODELS = {
            "gpt-4o-mini-transcribe": {
                "name": "GPT-4o Mini (Rápido e Econômico)",
                "supports_prompt": True,
                "supports_diarization": False,
                "default_response_format": "text",
                "cost_per_minute": 0.003  # $0.003 / minuto
            },
            "gpt-4o-transcribe": {
                "name": "GPT-4o (Alta Qualidade)",
                "supports_prompt": True,
                "supports_diarization": False,
                "default_response_format": "text",
                "cost_per_minute": 0.006  # $0.006 / minuto
            },
            "gpt-4o-transcribe-diarize": {
                "name": "GPT-4o com Diarização",
                "supports_prompt": False,
                "supports_diarization": True,
                "default_response_format": "diarized_json",
                "cost_per_minute": 0.006  # $0.006 / minuto
            },
            "whisper-1": {
                "name": "Whisper-1 (Legado)",
                "supports_prompt": True,
                "supports_diarization": False,
                "default_response_format": "text",
                "cost_per_minute": 0.006  # $0.006 / minuto
            }
        }

    def get_file_size(self, filepath):
        """Retorna o tamanho do arquivo em bytes"""
        return os.path.getsize(filepath)
    
    def get_model_info(self, model):
        """Retorna informações sobre o modelo"""
        return self.MODELS.get(model, self.MODELS["gpt-4o-mini-transcribe"])
    
    def get_model_cost(self, model):
        """Retorna o custo por minuto do modelo"""
        model_info = self.get_model_info(model)
        return model_info.get("cost_per_minute", 0.003)

    def transcribe(self, filepath, model="gpt-4o-mini-transcribe", prompt=None, use_diarization=False):
        """
        Transcreve um arquivo de áudio
        
        Args:
            filepath: Caminho para o arquivo de áudio
            model: Modelo a ser usado (padrão: gpt-4o-mini-transcribe)
            prompt: Prompt contextual opcional para melhorar a transcrição
            use_diarization: Se True, usa diarização (requer gpt-4o-transcribe-diarize)
        
        Returns:
            Se use_diarization=True, retorna dict com segments
            Caso contrário, retorna string com a transcrição
        """
        model_info = self.get_model_info(model)
        
        # Se diarização foi solicitada, usa o modelo de diarização
        if use_diarization:
            if not model_info["supports_diarization"]:
                model = "gpt-4o-transcribe-diarize"
                model_info = self.get_model_info(model)
        
        # Determina formato de resposta
        if model_info["supports_diarization"]:
            response_format = "diarized_json"
        else:
            response_format = model_info["default_response_format"]
        
        # Prepara parâmetros da API
        params = {
            "model": model,
            "file": open(filepath, "rb"),
            "response_format": response_format
        }
        
        # Adiciona prompt se suportado e fornecido
        if model_info["supports_prompt"] and prompt:
            params["prompt"] = prompt
        
        # Adiciona chunking_strategy para diarização com arquivos > 30s
        if model_info["supports_diarization"]:
            # Verifica duração aproximada (assume que arquivos > 25MB são longos)
            file_size = self.get_file_size(filepath)
            if file_size > 5 * 1024 * 1024:  # > 5MB provavelmente > 30s
                params["chunking_strategy"] = "auto"
        
        try:
            transcription = self.client.audio.transcriptions.create(**params)
            
            # Fecha o arquivo
            params["file"].close()
            
            # Processa resposta baseado no formato
            if response_format == "diarized_json":
                return self._format_diarized_response(transcription)
            else:
                # Para formato text, retorna diretamente
                if hasattr(transcription, 'text'):
                    return transcription.text
                return str(transcription)
        
        except Exception as e:
            # Garante que o arquivo seja fechado em caso de erro
            if 'file' in params and not params["file"].closed:
                params["file"].close()
            raise e
    
    def _format_diarized_response(self, transcription):
        """
        Formata resposta de diarização em string legível
        
        Args:
            transcription: Objeto de resposta da API com segments
        
        Returns:
            String formatada com falantes e timestamps
        """
        if not hasattr(transcription, 'segments') or not transcription.segments:
            return ""
        
        formatted_segments = []
        for segment in transcription.segments:
            speaker = getattr(segment, 'speaker', 'Desconhecido')
            text = getattr(segment, 'text', '')
            start = getattr(segment, 'start', 0)
            end = getattr(segment, 'end', 0)
            
            # Formata timestamps
            start_time = self._format_timestamp(start)
            end_time = self._format_timestamp(end)
            
            formatted_segments.append(
                f"[{speaker}] {text} [{start_time} - {end_time}]"
            )
        
        return "\n".join(formatted_segments)
    
    def _format_timestamp(self, seconds):
        """Formata segundos em formato HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
