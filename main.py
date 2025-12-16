import tkinter as tk
from tkinter import filedialog
import ctypes
import os
import threading
from docx import Document
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
        self.root.geometry("900x700")
        
        # Configura tema moderno
        set_appearance_mode("dark")
        set_default_color_theme("blue")
        
        self.transcriber = Transcriber()
        self.api = WhisperAPI()  # Para acessar informações de custo
        self.filepath = ""
        self.is_processing = False
        self.selected_model = "gpt-4o-mini-transcribe"  # Modelo padrão (mais barato)
        self.use_diarization = False

        # Container principal
        self.main_frame = CTkFrame(root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Cabeçalho
        self.header_frame = CTkFrame(self.main_frame)
        self.header_frame.pack(fill="x", pady=(0, 20))

        self.title_label = CTkLabel(
            self.header_frame, 
            text="🎤 Transcritor de Áudio", 
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=10)

        # Área de informações do arquivo
        self.file_info_frame = CTkFrame(self.main_frame)
        self.file_info_frame.pack(fill="x", pady=(0, 15))

        self.file_label = CTkLabel(
            self.file_info_frame, 
            text="📁 Nenhum arquivo selecionado",
            font=("Arial", 12),
            anchor="w"
        )
        self.file_label.pack(fill="x", padx=15, pady=10)

        self.file_size_label = CTkLabel(
            self.file_info_frame,
            text="",
            font=("Arial", 10),
            text_color="gray",
            anchor="w"
        )
        self.file_size_label.pack(fill="x", padx=15, pady=(0, 10))

        # Frame de configurações (modelo e diarização)
        self.settings_frame = CTkFrame(self.main_frame)
        self.settings_frame.pack(fill="x", pady=(0, 15))

        # Label e ComboBox para seleção de modelo
        self.model_label = CTkLabel(
            self.settings_frame,
            text="Modelo:",
            font=("Arial", 12),
            anchor="w"
        )
        self.model_label.pack(side="left", padx=(15, 5), pady=10)

        self.model_combo = CTkComboBox(
            self.settings_frame,
            values=[
                "gpt-4o-mini-transcribe",
                "gpt-4o-transcribe",
                "gpt-4o-transcribe-diarize",
                "whisper-1"
            ],
            command=self._on_model_change,
            font=("Arial", 11),
            width=200
        )
        self.model_combo.set("gpt-4o-mini-transcribe")
        self.model_combo.pack(side="left", padx=5, pady=10)

        # Label para mostrar o custo do modelo
        self.cost_label = CTkLabel(
            self.settings_frame,
            text="",
            font=("Arial", 10),
            text_color="gray",
            anchor="w"
        )
        self.cost_label.pack(side="left", padx=(10, 0), pady=10)
        self._update_cost_label()  # Atualiza com o custo inicial

        # Checkbox para diarização
        self.diarization_checkbox = CTkCheckBox(
            self.settings_frame,
            text="Usar Diarização (identificar falantes)",
            command=self._on_diarization_change,
            font=("Arial", 11)
        )
        self.diarization_checkbox.pack(side="left", padx=(20, 15), pady=10)

        # Frame de botões
        self.button_frame = CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", pady=(0, 15))

        self.import_button = CTkButton(
            self.button_frame,
            text="📂 Selecionar Arquivo",
            command=self.import_file,
            font=("Arial", 14),
            height=40,
            corner_radius=10
        )
        self.import_button.pack(side="left", padx=5, fill="x", expand=True)

        self.transcribe_button = CTkButton(
            self.button_frame,
            text="▶️ Iniciar Transcrição",
            command=self.start_transcription,
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=10,
            fg_color="#1f8a4f",
            hover_color="#166d3d"
        )
        self.transcribe_button.pack(side="left", padx=5, fill="x", expand=True)

        # Área de status e progresso
        self.status_frame = CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", pady=(0, 15))

        self.status_label = CTkLabel(
            self.status_frame,
            text="",
            font=("Arial", 12),
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=15, pady=(10, 5))

        self.progress_bar = CTkProgressBar(self.status_frame)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 10))
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Esconde inicialmente

        # Área de transcrição
        self.text_frame = CTkFrame(self.main_frame)
        self.text_frame.pack(fill="both", expand=True, pady=(0, 15))

        self.text_label = CTkLabel(
            self.text_frame,
            text="📝 Transcrição:",
            font=("Arial", 14, "bold"),
            anchor="w"
        )
        self.text_label.pack(fill="x", padx=15, pady=(10, 5))

        self.text_area = CTkTextbox(
            self.text_frame,
            font=("Arial", 12),
            wrap="word",
            corner_radius=10
        )
        self.text_area.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Frame de ações
        self.action_frame = CTkFrame(self.main_frame)
        self.action_frame.pack(fill="x")

        self.copy_button = CTkButton(
            self.action_frame,
            text="📋 Copiar",
            command=self.copy_transcription,
            font=("Arial", 12),
            height=35,
            corner_radius=8,
            fg_color="#2b5aa0",
            hover_color="#1e3f6f"
        )
        self.copy_button.pack(side="left", padx=5, fill="x", expand=True)

        self.save_button = CTkButton(
            self.action_frame,
            text="💾 Salvar como Word",
            command=self.save_transcription_to_word,
            font=("Arial", 12),
            height=35,
            corner_radius=8,
            fg_color="#2d7a4d",
            hover_color="#1f5634"
        )
        self.save_button.pack(side="left", padx=5, fill="x", expand=True)

        self.clear_button = CTkButton(
            self.action_frame,
            text="🗑️ Limpar",
            command=self.clear_text,
            font=("Arial", 12),
            height=35,
            corner_radius=8,
            fg_color="#8b2a2a",
            hover_color="#6b1f1f"
        )
        self.clear_button.pack(side="left", padx=5, fill="x", expand=True)

        self.reset_button = CTkButton(
            self.action_frame,
            text="🔄 Novo Arquivo",
            command=self.reset,
            font=("Arial", 12),
            height=35,
            corner_radius=8
        )
        self.reset_button.pack(side="left", padx=5, fill="x", expand=True)

    def format_file_size(self, size_bytes):
        """Formata o tamanho do arquivo em formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

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
            file_size = os.path.getsize(self.filepath)
            file_size_str = self.format_file_size(file_size)
            
            self.file_label.configure(text=f"📁 {filename}")
            self.file_size_label.configure(text=f"Tamanho: {file_size_str}")
            
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
        self.text_area.delete("1.0", tk.END)
        self.status_label.configure(text="")
        self.progress_bar.pack_forget()
        # Reseta modelo para padrão
        self.selected_model = "gpt-4o-mini-transcribe"
        self.model_combo.set("gpt-4o-mini-transcribe")
        self.use_diarization = False
        self.diarization_checkbox.deselect()
        self.diarization_checkbox.configure(state="normal")

if __name__ == "__main__":
    root = CTk()
    app = TranscriptionApp(root)
    root.mainloop()
