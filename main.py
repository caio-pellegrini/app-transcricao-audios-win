import tkinter as tk
from tkinter import filedialog
import ctypes
import os
import threading
from docx import Document
from pydub import AudioSegment
from customtkinter import CTk, CTkFrame, CTkButton, CTkLabel, CTkTextbox, CTkProgressBar, CTkComboBox, CTkCheckBox, set_appearance_mode, set_default_color_theme

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from transcriber import Transcriber
from whisper_api import WhisperAPI

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcritor de Áudio")
        
        # Configura tema moderno
        set_appearance_mode("dark")
        set_default_color_theme("blue")
        
        # Maximiza a janela por padrão
        # Aguarda a janela ser criada antes de maximizar
        self.root.update_idletasks()
        # Tenta maximizar imediatamente e também após um pequeno delay
        self._maximize_window()
        self.root.after(50, self._maximize_window)
        
        self.transcriber = Transcriber()
        self.api = WhisperAPI()  # Para acessar informações de custo
        self.filepath = ""
        self.is_processing = False
        self.selected_model = "whisper-1"  # Modelo padrão
        self.use_diarization = False

        # Container principal - usa grid para permitir proporções exatas
        self.main_frame = CTkFrame(root)
        self.main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Configura grid para proporções 40/60
        self.main_frame.grid_columnconfigure(0, weight=2, uniform="cols")  # 40% (2/5)
        self.main_frame.grid_columnconfigure(1, weight=3, uniform="cols")  # 60% (3/5)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Coluna esquerda (40%)
        self.left_frame = CTkFrame(self.main_frame)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        # Coluna direita (60%)
        self.right_frame = CTkFrame(self.main_frame)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

        # Cabeçalho (esquerda)
        self.header_frame = CTkFrame(self.left_frame)
        self.header_frame.pack(fill="x", pady=(0, 20))

        self.title_label = CTkLabel(
            self.header_frame, 
            text="🎤 Transcritor de Áudio", 
            font=("Arial", 22, "bold")
        )
        self.title_label.pack(pady=15)

        # Área de informações do arquivo (esquerda)
        self.file_info_frame = CTkFrame(self.left_frame)
        self.file_info_frame.pack(fill="x", pady=(0, 20))

        self.file_label = CTkLabel(
            self.file_info_frame, 
            text="📁 Nenhum arquivo selecionado",
            font=("Arial", 13),
            anchor="w"
        )
        self.file_label.pack(fill="x", padx=20, pady=(15, 8))

        self.file_size_label = CTkLabel(
            self.file_info_frame,
            text="",
            font=("Arial", 11),
            text_color="gray",
            anchor="w"
        )
        self.file_size_label.pack(fill="x", padx=20, pady=(0, 8))

        self.estimated_cost_label = CTkLabel(
            self.file_info_frame,
            text="",
            font=("Arial", 11),
            text_color="#4CAF50",
            anchor="w"
        )
        self.estimated_cost_label.pack(fill="x", padx=20, pady=(0, 8))

        self.estimated_time_label = CTkLabel(
            self.file_info_frame,
            text="",
            font=("Arial", 11),
            text_color="gray",
            anchor="w"
        )
        self.estimated_time_label.pack(fill="x", padx=20, pady=(0, 15))

        # Frame de configurações (modelo e diarização) (esquerda)
        self.settings_frame = CTkFrame(self.left_frame)
        self.settings_frame.pack(fill="x", pady=(0, 20))

        # Container para modelo e custo (linha superior)
        self.model_row = CTkFrame(self.settings_frame)
        self.model_row.pack(fill="x", padx=15, pady=(15, 10))

        # Label e ComboBox para seleção de modelo
        self.model_label = CTkLabel(
            self.model_row,
            text="Modelo:",
            font=("Arial", 13, "bold"),
            anchor="w"
        )
        self.model_label.pack(side="left", padx=(0, 10))

        self.model_combo = CTkComboBox(
            self.model_row,
            values=[
                "gpt-4o-mini-transcribe",
                "gpt-4o-transcribe",
                "gpt-4o-transcribe-diarize",
                "whisper-1"
            ],
            command=self._on_model_change,
            font=("Arial", 12),
            width=220,
            height=35
        )
        self.model_combo.set("whisper-1")
        self.model_combo.pack(side="left", padx=(0, 15), fill="x", expand=True)

        # Label para mostrar o custo do modelo
        self.cost_label = CTkLabel(
            self.model_row,
            text="",
            font=("Arial", 11),
            text_color="gray",
            anchor="w"
        )
        self.cost_label.pack(side="left", padx=(10, 0))
        self._update_cost_label()  # Atualiza com o custo inicial

        # Checkbox para diarização (linha inferior)
        self.diarization_checkbox = CTkCheckBox(
            self.settings_frame,
            text="Usar Diarização (identificar falantes)",
            command=self._on_diarization_change,
            font=("Arial", 12)
        )
        self.diarization_checkbox.pack(side="left", padx=(20, 15), pady=(0, 15))

        # Frame de botões (esquerda)
        self.button_frame = CTkFrame(self.left_frame)
        self.button_frame.pack(fill="x", pady=(0, 20))

        self.import_button = CTkButton(
            self.button_frame,
            text="📂 Selecionar Arquivo",
            command=self.import_file,
            font=("Arial", 15),
            height=50,
            corner_radius=12
        )
        self.import_button.pack(fill="x", padx=10, pady=(10, 8))

        self.transcribe_button = CTkButton(
            self.button_frame,
            text="▶️ Iniciar Transcrição",
            command=self.start_transcription,
            font=("Arial", 15, "bold"),
            height=50,
            corner_radius=12,
            fg_color="#1f8a4f",
            hover_color="#166d3d"
        )
        self.transcribe_button.pack(fill="x", padx=10, pady=(0, 10))

        # Área de status e progresso (esquerda) - expande para ocupar espaço restante
        self.status_frame = CTkFrame(self.left_frame)
        self.status_frame.pack(fill="both", expand=True, pady=(0, 0))

        self.status_label = CTkLabel(
            self.status_frame,
            text="",
            font=("Arial", 13),
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=20, pady=(15, 10))

        self.progress_bar = CTkProgressBar(self.status_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 15))
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Esconde inicialmente

        # Área de transcrição (direita)
        self.text_frame = CTkFrame(self.right_frame)
        self.text_frame.pack(fill="both", expand=True, pady=(0, 20))

        self.text_label = CTkLabel(
            self.text_frame,
            text="📝 Transcrição:",
            font=("Arial", 16, "bold"),
            anchor="w"
        )
        self.text_label.pack(fill="x", padx=20, pady=(15, 10))

        self.text_area = CTkTextbox(
            self.text_frame,
            font=("Arial", 13),
            wrap="word",
            corner_radius=12
        )
        self.text_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Frame de ações (direita)
        self.action_frame = CTkFrame(self.right_frame)
        self.action_frame.pack(fill="x", pady=(0, 0))

        # Primeira linha de botões
        self.action_row1 = CTkFrame(self.action_frame)
        self.action_row1.pack(fill="x", padx=10, pady=(0, 10))

        self.copy_button = CTkButton(
            self.action_row1,
            text="📋 Copiar",
            command=self.copy_transcription,
            font=("Arial", 13),
            height=45,
            corner_radius=10,
            fg_color="#2b5aa0",
            hover_color="#1e3f6f"
        )
        self.copy_button.pack(side="left", padx=(0, 8), fill="x", expand=True)

        self.save_button = CTkButton(
            self.action_row1,
            text="💾 Salvar como Word",
            command=self.save_transcription_to_word,
            font=("Arial", 13),
            height=45,
            corner_radius=10,
            fg_color="#2d7a4d",
            hover_color="#1f5634"
        )
        self.save_button.pack(side="left", padx=(0, 8), fill="x", expand=True)

        # Segunda linha de botões
        self.action_row2 = CTkFrame(self.action_frame)
        self.action_row2.pack(fill="x", padx=10, pady=(0, 10))

        self.clear_button = CTkButton(
            self.action_row2,
            text="🗑️ Limpar",
            command=self.clear_text,
            font=("Arial", 13),
            height=45,
            corner_radius=10,
            fg_color="#8b2a2a",
            hover_color="#6b1f1f"
        )
        self.clear_button.pack(side="left", padx=(0, 8), fill="x", expand=True)

        self.reset_button = CTkButton(
            self.action_row2,
            text="🔄 Novo Arquivo",
            command=self.reset,
            font=("Arial", 13),
            height=45,
            corner_radius=10
        )
        self.reset_button.pack(side="left", padx=(0, 8), fill="x", expand=True)

    def _maximize_window(self):
        """Maximiza a janela de forma compatível com Windows"""
        try:
            # No Windows, usa state('zoomed')
            self.root.state('zoomed')
        except Exception as e:
            try:
                # Tenta usando wm_state (alternativa)
                self.root.wm_state('zoomed')
            except:
                try:
                    # Fallback: define geometria para ocupar toda a tela
                    # Remove a barra de título e bordas do cálculo
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight()
                    # Usa a geometria completa da tela
                    self.root.geometry(f"{screen_width}x{screen_height}+0+0")
                except:
                    # Último fallback: tamanho grande padrão
                    self.root.geometry("1400x900")

    def format_file_size(self, size_bytes):
        """Formata o tamanho do arquivo em formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def get_audio_duration(self, filepath):
        """Obtém a duração do arquivo de áudio em minutos"""
        try:
            audio = AudioSegment.from_file(filepath)
            duration_seconds = len(audio) / 1000.0  # pydub retorna em milissegundos
            duration_minutes = duration_seconds / 60.0
            return duration_minutes
        except Exception as e:
            print(f"Erro ao obter duração do áudio: {str(e)}")
            return None
    
    def calculate_estimated_cost(self, duration_minutes, model):
        """Calcula o custo estimado da transcrição"""
        if duration_minutes is None:
            return None
        cost_per_minute = self.api.get_model_cost(model)
        # O custo mínimo é sempre de 1 minuto, mesmo que o áudio seja menor
        effective_minutes = max(duration_minutes, 1.0)
        estimated_cost = effective_minutes * cost_per_minute
        return estimated_cost
    
    def update_estimated_cost_label(self):
        """Atualiza o label com o custo estimado"""
        if not self.filepath:
            self.estimated_cost_label.configure(text="")
            self.estimated_time_label.configure(text="")
            return
        
        # Obtém o tamanho do arquivo
        file_size = os.path.getsize(self.filepath)
        file_size_str = self.format_file_size(file_size)
        
        duration_minutes = self.get_audio_duration(self.filepath)
        if duration_minutes is None:
            self.file_size_label.configure(
                text=f"Tamanho: {file_size_str} | ⚠️ Não foi possível calcular a duração do áudio",
                text_color="orange"
            )
            self.estimated_cost_label.configure(text="")
            self.estimated_time_label.configure(text="")
            return
        
        # Formata a duração do áudio
        if duration_minutes < 1:
            duration_str = f"{duration_minutes * 60:.1f} segundos"
        else:
            duration_str = f"{duration_minutes:.2f} minutos"
        
        # Atualiza o label com tamanho e duração na mesma linha
        self.file_size_label.configure(
            text=f"Tamanho: {file_size_str} | Duração: {duration_str}",
            text_color="gray"
        )
        
        estimated_cost = self.calculate_estimated_cost(duration_minutes, self.selected_model)
        if estimated_cost is None:
            self.estimated_cost_label.configure(text="")
            self.estimated_time_label.configure(text="")
            return
        
        # Formata o custo: 2 casas decimais normalmente, mais casas apenas se < 0.01
        if estimated_cost < 0.01:
            cost_str_usd = f"${estimated_cost:.3f}"
        else:
            cost_str_usd = f"${estimated_cost:.2f}"
        
        # Calcula o custo em reais (1 USD = 5 BRL)
        cost_brl = estimated_cost * 5
        if cost_brl < 0.01:
            cost_str_brl = f"R$ {cost_brl:.3f}"
        else:
            cost_str_brl = f"R$ {cost_brl:.2f}"
        
        self.estimated_cost_label.configure(
            text=f"💰 Custo estimado: {cost_str_usd} ({cost_str_brl})",
            text_color="#4CAF50"
        )
        
        # Calcula o tempo estimado de transcrição (1 min de áudio = 5 seg de transcrição)
        estimated_transcription_seconds = int(duration_minutes * 5)
        if estimated_transcription_seconds < 60:
            time_str = f"{estimated_transcription_seconds} segundos"
        else:
            minutes = estimated_transcription_seconds // 60
            seconds = estimated_transcription_seconds % 60
            if seconds == 0:
                time_str = f"{minutes} min"
            else:
                time_str = f"{minutes} min e {seconds} seg"
        
        self.estimated_time_label.configure(
            text=f"⏳ Tempo estimado para transcrição: {time_str}",
            text_color="gray"
        )

    def import_file(self):
        if self.is_processing:
            return
        
        self.filepath = filedialog.askopenfilename(
            title="Selecione um arquivo de áudio",
            filetypes=[
                ("Arquivos de Áudio", "*.mp3 *.mp4 *.mpeg *.mpga *.m4a *.wav *.webm"),
                ("Todos os arquivos", "*.*")
            ]
        )
        
        if self.filepath:
            filename = os.path.basename(self.filepath)
            
            self.file_label.configure(text=f"📁 {filename}")
            
            # Atualiza o custo estimado (que também atualiza o tamanho e duração)
            self.update_estimated_cost_label()
            
            # Limpa a transcrição anterior
            self.text_area.delete("1.0", tk.END)
            self.status_label.configure(text="")

    def update_progress(self, value):
        """Atualiza a barra de progresso"""
        self.progress_bar.set(value)
        self.root.update_idletasks()

    def animate_progress(self):
        """Anima a barra de progresso enquanto processa"""
        import time
        value = 0
        direction = 1
        while self.is_processing:
            value += direction * 0.02
            if value >= 0.9:
                direction = -1
            elif value <= 0.1:
                direction = 1
            self.progress_bar.set(value)
            self.root.update_idletasks()
            time.sleep(0.1)

    def start_transcription(self):
        if self.is_processing:
            return
            
        if not self.filepath:
            self.status_label.configure(
                text="⚠️ Por favor, selecione um arquivo primeiro",
                text_color="orange"
            )
            return

        # Prepara a UI para processamento
        self.is_processing = True
        self.transcribe_button.configure(state="disabled", text="⏳ Processando...")
        self.import_button.configure(state="disabled")
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 10))
        
        # Verifica o tamanho do arquivo
        file_size = os.path.getsize(self.filepath)
        max_size = 25 * 1024 * 1024  # 25MB
        
        if file_size > max_size:
            self.status_label.configure(
                text="🔄 Arquivo grande detectado. Dividindo e transcrevendo em partes...",
                text_color="yellow"
            )
        else:
            self.status_label.configure(
                text="🔄 Transcrevendo áudio...",
                text_color="cyan"
            )
        
        # Inicia animação de progresso em thread separada
        progress_thread = threading.Thread(target=self.animate_progress, daemon=True)
        progress_thread.start()
        
        # Executa transcrição em thread separada para não travar a UI
        transcription_thread = threading.Thread(target=self._transcribe_async, daemon=True)
        transcription_thread.start()

    def _update_cost_label(self):
        """Atualiza o label com o custo do modelo selecionado"""
        cost = self.api.get_model_cost(self.selected_model)
        cost_text = f"Custo: ${cost:.3f} / minuto"
        self.cost_label.configure(text=cost_text)
        # Atualiza também o custo estimado se houver arquivo selecionado
        if self.filepath:
            self.update_estimated_cost_label()

    def _on_model_change(self, value):
        """Callback quando o modelo é alterado"""
        self.selected_model = value
        # Atualiza o label de custo
        self._update_cost_label()
        # Se o modelo selecionado é o de diarização, ativa o checkbox automaticamente
        if value == "gpt-4o-transcribe-diarize":
            self.diarization_checkbox.select()
            self.diarization_checkbox.configure(state="disabled")
            self.use_diarization = True
        else:
            # Se mudou para outro modelo, habilita o checkbox e atualiza use_diarization baseado no estado
            self.diarization_checkbox.configure(state="normal")
            self.use_diarization = self.diarization_checkbox.get()
    
    def _on_diarization_change(self):
        """Callback quando a opção de diarização é alterada"""
        self.use_diarization = self.diarization_checkbox.get()
        # Se diarização foi ativada, sugere o modelo apropriado
        if self.use_diarization and self.selected_model != "gpt-4o-transcribe-diarize":
            # Atualiza o combo para o modelo de diarização
            self.model_combo.set("gpt-4o-transcribe-diarize")
            self.selected_model = "gpt-4o-transcribe-diarize"
            self._update_cost_label()  # Atualiza o custo quando muda o modelo

    def _transcribe_async(self):
        """Executa a transcrição em thread separada"""
        try:
            transcription = self.transcriber.transcribe_audio(
                self.filepath,
                model=self.selected_model,
                use_diarization=self.use_diarization
            )
            
            # Atualiza UI na thread principal
            self.root.after(0, self._transcription_complete, transcription, None)
        except Exception as e:
            self.root.after(0, self._transcription_complete, None, str(e))

    def _transcription_complete(self, transcription, error):
        """Callback chamado quando a transcrição termina"""
        self.is_processing = False
        self.progress_bar.pack_forget()
        self.transcribe_button.configure(state="normal", text="▶️ Iniciar Transcrição")
        self.import_button.configure(state="normal")
        
        if error:
            self.status_label.configure(
                text=f"❌ Erro: {error}",
                text_color="red"
            )
        else:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", transcription)
            self.status_label.configure(
                text="✅ Transcrição concluída com sucesso!",
                text_color="green"
            )

    def copy_transcription(self):
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            self.status_label.configure(
                text="⚠️ Nenhuma transcrição para copiar",
                text_color="orange"
            )
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_label.configure(
            text="📋 Transcrição copiada para a área de transferência!",
            text_color="green"
        )
        # Limpa a mensagem após 3 segundos
        self.root.after(3000, lambda: self.status_label.configure(text=""))

    def save_transcription_to_word(self):
        """Salva a transcrição em um arquivo .docx"""
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            self.status_label.configure(
                text="⚠️ Nenhuma transcrição para salvar",
                text_color="orange"
            )
            return
        
        # Abre diálogo para escolher onde salvar
        filepath = filedialog.asksaveasfilename(
            title="Salvar transcrição como Word",
            defaultextension=".docx",
            filetypes=[
                ("Documento Word", "*.docx"),
                ("Todos os arquivos", "*.*")
            ]
        )
        
        if not filepath:
            return  # Usuário cancelou
        
        try:
            # Cria um novo documento Word
            doc = Document()
            
            # Adiciona o texto da transcrição
            # Se houver quebras de linha, preserva usando parágrafos
            paragraphs = text.split('\n')
            for para_text in paragraphs:
                if para_text.strip():  # Ignora linhas vazias
                    doc.add_paragraph(para_text)
                else:
                    doc.add_paragraph()  # Adiciona parágrafo vazio para espaçamento
            
            # Salva o documento
            doc.save(filepath)
            
            self.status_label.configure(
                text=f"✅ Transcrição salva em: {os.path.basename(filepath)}",
                text_color="green"
            )
            # Limpa a mensagem após 5 segundos
            self.root.after(5000, lambda: self.status_label.configure(text=""))
            
        except Exception as e:
            self.status_label.configure(
                text=f"❌ Erro ao salvar arquivo: {str(e)}",
                text_color="red"
            )

    def clear_text(self):
        self.text_area.delete("1.0", tk.END)
        self.status_label.configure(text="🗑️ Texto limpo")

    def reset(self):
        if self.is_processing:
            return
            
        self.filepath = ""
        self.file_label.configure(text="📁 Nenhum arquivo selecionado")
        self.file_size_label.configure(text="")
        self.estimated_cost_label.configure(text="")
        self.estimated_time_label.configure(text="")
        self.text_area.delete("1.0", tk.END)
        self.status_label.configure(text="")
        self.progress_bar.pack_forget()
        # Reseta modelo para padrão
        self.selected_model = "whisper-1"
        self.model_combo.set("whisper-1")
        self.use_diarization = False
        self.diarization_checkbox.deselect()
        self.diarization_checkbox.configure(state="normal")

if __name__ == "__main__":
    root = CTk()
    app = TranscriptionApp(root)
    # Garante que a janela seja maximizada após tudo ser criado
    root.update()
    root.mainloop()
