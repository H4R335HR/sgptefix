# Script Name: `sgptefix`

## Description:

`sgptefix` is a Python script created to simplify the setup and configuration of **Shell-GPT (SGPT)** in environments like **EC-Council Labs**, where you might want to use remote **Ollama servers**. This script ensures that **SGPT** can connect to and interact with an Ollama server by automatically modifying the `.sgptrc` configuration file with the appropriate settings.

## Features:
- **Automates Installation**: Installs **Shell-GPT** along with its required dependencies (including Litellm for Ollama model usage).
- **Generates Initial Configuration**: Runs `sgpt` with a fake OpenAI key to generate the initial `.sgptrc` configuration file.
- **Configures Remote Ollama Server**: Updates the `.sgptrc` file with the provided Ollama server IP and model name, and sets related configuration values (e.g., API URL, model name, OpenAI key).
- **Preserves Existing Configurations**: Updates only necessary fields in the configuration file without altering pre-existing settings.
- **Verifies Setup**: Runs a test prompt to ensure SGPT is working correctly with the remote Ollama server.

## Usage:
1. To use this script, first initialize sgpt

```bash
sgpt
```
Provide any Fake key when prompted

2. Run it with the remote Ollama server's IP and the model name as arguments. For example:

```bash
python sgptefix.py <remote_ollama_ip> <model_name>
