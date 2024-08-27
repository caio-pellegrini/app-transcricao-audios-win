# Transcritor de Áudio com Whisper API

Este é um projeto de transcrição de áudio que utiliza a API Whisper da OpenAI para converter arquivos de áudio em texto. A aplicação é construída em Python e possui uma interface gráfica simples usando `tkinter`.

## Funcionalidades

- **Importar Arquivos de Áudio**: Suporta vários formatos de áudio, como MP3, WAV, etc.
- **Transcrição**: Envia o áudio para a API Whisper para obter a transcrição em texto.
- **Copiar Transcrição**: Permite copiar a transcrição gerada para a área de transferência.
- **Resetar**: Limpa o campo de texto e reinicia a aplicação para uma nova transcrição.

## Tecnologias Utilizadas

- **Python 3.x**
- **tkinter**: Para a interface gráfica.
- **Whisper API**: Para realizar a transcrição de áudio.

## Pré-requisitos

- **Python 3.x**
- **pip**: Gerenciador de pacotes Python.

## Instalação

1. **Clone o repositório**:

    ```bash
    git clone https://github.com/usuario/transcritor-de-audio.git
    cd transcritor-de-audio
    ```

2. **Crie e ative um ambiente virtual**:

    ```bash
    python -m venv env
    source env/bin/activate  # No Windows: .\env\Scripts\activate
    ```

3. **Instale as dependências**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure sua chave de API**:

    - Crie um arquivo `.env` no diretório raiz do projeto e adicione sua chave de API:
    
      ```plaintext
      API_KEY=sua-api-key-aqui
      ```

    - **OU**: Configure a variável de ambiente `API_KEY` diretamente no seu sistema.

5. **Instale o `ffmpeg`**:

    - **Windows**: Baixe o `ffmpeg` [aqui](https://ffmpeg.org/download.html) e adicione ao PATH.
    - **macOS**: Use Homebrew:
    
      ```bash
      brew install ffmpeg
      ```

    - **Linux**:
    
      ```bash
      sudo apt-get install ffmpeg
      ```

## Uso

1. **Execute a aplicação**:

    ```bash
    python main.py
    ```

2. **Importe um arquivo de áudio** clicando no botão "Importar Arquivo".

3. **Inicie a transcrição** clicando em "Iniciar Transcrição". O texto transcrito aparecerá na área de texto.

4. **Copie a transcrição** para a área de transferência usando o botão "Copiar Transcrição".

5. **Resete a aplicação** para limpar os campos e começar novamente clicando no botão "Resetar".

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma issue ou enviar um pull request.
