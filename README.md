# LocalGPT Chat Interface

A local chatbot interface that runs on your computer using Ollama models. This application provides a user-friendly web interface for interacting with various AI models locally.

## Features

- Chat with multiple AI models locally
- Upload and reference PDF, DOCX, and TXT files
- Adjust AI temperature settings
- Create and manage different chat projects
- System prompt customization

## Prerequisites

1. Install [Ollama](https://ollama.ai/download)
2. Install [Python](https://www.python.org/downloads/) (3.8 or higher)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/jpenzell/LocalGPT.git
   cd LocalGPT
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

The chat interface will automatically open in your default web browser.

## Usage

1. Select an AI model from the dropdown menu
2. Type your message in the input box
3. Press Enter or click Submit to send your message
4. Use the Clear button to start a new conversation
5. Adjust the temperature slider to control response creativity
6. Upload documents to reference in your conversation
7. Create different projects to organize your chats

## Models

The application uses Ollama models. To download a new model:
```bash
ollama pull modelname
```

Common models include:
- mistral
- llama2
- codellama
- neural-chat

## Support

For issues or questions, please open an issue on the GitHub repository.
