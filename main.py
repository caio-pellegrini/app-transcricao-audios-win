import tkinter as tk
from tkinter import filedialog, messagebox
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from transcriber import Transcriber

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcritor de Áudio")
        
        self.transcriber = Transcriber()

        self.filepath = ""

        # Frame para alinhar os elementos na mesma linha com padding ajustado
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=20)  # Aumente o valor de pady aqui para mais espaço

        # Elementos da UI dentro do frame
        self.import_button = tk.Button(self.button_frame, text="Importar Arquivo", command=self.import_file, font=("Helvetica", 10))
        self.import_button.pack(side="left", padx=5)

        self.transcribe_button = tk.Button(self.button_frame, text="Iniciar Transcrição", command=self.start_transcription, font=("Helvetica", 10))
        self.transcribe_button.pack(side="left", padx=5)

        self.loading_label = tk.Label(root, text="", font=("Helvetica", 10))
        self.loading_label.pack()  # Ajuste o padding vertical conforme necessário

        # Adiciona margens à área de texto
        self.text_frame = tk.Frame(root, padx=20, pady=10)
        self.text_frame.pack(pady=10, fill="both", expand=True)

        # Configura a área de texto
        self.text_area = tk.Text(self.text_frame, height=20, width=60, font=("Helvetica", 11), wrap="word", padx=10, pady=10)
        self.text_area.pack(fill="both", expand=True)

        # Adiciona botão de copiar
        self.copy_button = tk.Button(root, text="Copiar Transcrição", command=self.copy_transcription, font=("Helvetica", 10))
        self.copy_button.pack(pady=10)

        # Adiciona botão de resetar
        self.reset_button = tk.Button(root, text="Resetar", command=self.reset, font=("Helvetica", 10))
        self.reset_button.pack(pady=10)

    def import_file(self):
        self.filepath = filedialog.askopenfilename(
            filetypes=[("Arquivos de Áudio", "*.mp3 *.mp4 *.mpeg *.mpga *.m4a *.wav *.webm")]
        )
        if self.filepath:
            messagebox.showinfo("Arquivo Selecionado", f"Arquivo selecionado: {self.filepath}")

    def start_transcription(self):
        if not self.filepath:
            messagebox.showwarning("Nenhum Arquivo", "Por favor, importe um arquivo de áudio primeiro.")
            return

        self.loading_label.config(text="Transcrevendo...")
        self.root.update_idletasks()

        try:
            transcription = self.transcriber.transcribe_audio(self.filepath)
            self.loading_label.config(text="")
            self.text_area.insert(tk.END, transcription)
        except Exception as e:
            self.loading_label.config(text="")
            messagebox.showerror("Erro", str(e))

    def copy_transcription(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_area.get("1.0", tk.END))
        messagebox.showinfo("Copiado", "Transcrição copiada para a área de transferência.")

    def reset(self):
        self.filepath = ""
        self.text_area.delete("1.0", tk.END)
        self.loading_label.config(text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()
