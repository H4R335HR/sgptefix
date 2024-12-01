#!/usr/bin/env python3

import os
import subprocess
import sys
import argparse

def get_real_user():
    """Get the actual user even when script is run with sudo"""
    return os.environ.get('SUDO_USER') or os.environ.get('USER')

def get_real_home():
    """Get the actual user's home directory even when script is run with sudo"""
    real_user = get_real_user()
    return os.path.expanduser(f'~{real_user}') if real_user else os.path.expanduser('~')

def is_litellm_installed():
    """Check if shell-gpt is installed with litellm support"""
    try:
        result = subprocess.run(
            "pip freeze",
            shell=True,
            text=True,
            capture_output=True,
            check=True
        )
        packages = result.stdout.lower()
        return "shell_gpt" in packages and "litellm" in packages
    except subprocess.CalledProcessError:
        return False

def check_config_exists():
    """Check if sgptrc config file exists"""
    real_home = get_real_home()
    sgptrc_path = os.path.join(real_home, '.config/shell_gpt/.sgptrc')
    return os.path.exists(sgptrc_path)

def is_config_already_modified(ip, model):
    """Check if config is already set up as needed"""
    real_home = get_real_home()
    sgptrc_path = os.path.join(real_home, '.config/shell_gpt/.sgptrc')
    try:
        with open(sgptrc_path, "r") as file:
            content = file.read()
            required_settings = [
                f"DEFAULT_MODEL={model}",
                f"API_BASE_URL=http://{ip}:11434",
                "OPENAI_USE_FUNCTIONS=false",
                "USE_LITELLM=true"
            ]
            return all(setting in content for setting in required_settings)
    except FileNotFoundError:
        return False
def update_sgptrc(ip, model):
    real_home = get_real_home()
    sgptrc_path = os.path.join(real_home, '.config/shell_gpt/.sgptrc')
    try:
        with open(sgptrc_path, "r") as file:
            lines = file.readlines()

        modified = False
        for i, line in enumerate(lines):
            if line.startswith("DEFAULT_MODEL="):
                lines[i] = f"DEFAULT_MODEL={model}\n"
                modified = True
            elif line.startswith("API_BASE_URL="):
                lines[i] = f"API_BASE_URL=http://{ip}:11434\n"
                modified = True
            elif line.startswith("OPENAI_USE_FUNCTIONS="):
                lines[i] = "OPENAI_USE_FUNCTIONS=false\n"
                modified = True
            elif line.startswith("USE_LITELLM="):
                lines[i] = "USE_LITELLM=true\n"
                modified = True

        if not modified:
            print("No changes were made to the config file.")
            return

        with open(sgptrc_path, "w") as file:
            file.writelines(lines)
        print(f"Updated {sgptrc_path} successfully.")

    except FileNotFoundError:
        print(f"Error: Config file {sgptrc_path} not found. Ensure sgpt was initialized properly.")
        sys.exit(1)

def run_command(command, input_text=None, use_sudo=False):
    try:
        if use_sudo:
            command = f"sudo {command}"
        result = subprocess.run(
            command,
            input=input_text,
            text=True,
            check=True,
            shell=True,
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}\n{e}")
        sys.exit(1)

def run_sgpt_command(command):
    """Run sgpt command as the real user with proper path"""
    real_user = get_real_user()
    sgpt_path = subprocess.check_output(['which', 'sgpt']).decode().strip()
    try:
        if real_user:
            env = os.environ.copy()
            full_command = f'sudo -u {real_user} env PATH="{env["PATH"]}" HOME="{get_real_home()}" {sgpt_path} {command}'
            subprocess.run(full_command, check=True, shell=True)
        else:
            full_command = f'{sgpt_path} {command}'
            subprocess.run(full_command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running sgpt command: {e}")
        sys.exit(1)
def initialize_sgpt():
    print("Initializing sgpt to generate the config file...")
    print("Please enter a placeholder API key when prompted (e.g., 'testkey' or any gibberish):")
    try:
        run_sgpt_command("test")
        print("sgpt initialized successfully.")
    except Exception as e:
        print(f"Error initializing sgpt: {e}")
        sys.exit(1)

def format_model_name(model_name):
    """Add ollama/ prefix to model name"""
    return f"ollama/{model_name}"

def get_available_models(ip):
    """Fetch and return available models from the Ollama server"""
    try:
        result = subprocess.run(
            f"curl -s http://{ip}:11434/api/tags | jq -r '.models[].name'",
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        original_models = result.stdout.strip().split('\n')
        models_dict = {format_model_name(model): model for model in original_models}
        return models_dict
    except subprocess.CalledProcessError:
        print(f"Error: Unable to fetch models from {ip}")
        sys.exit(1)

def select_model(models_dict):
    """Display available models and let user select one"""
    display_models = list(models_dict.keys())
    print("\nAvailable models:")
    for i, model in enumerate(display_models, 1):
        print(f"{i}. {model}")
    
    while True:
        try:
            choice = int(input("\nSelect a model (enter number): "))
            if 1 <= choice <= len(display_models):
                selected_display_model = display_models[choice-1]
                return selected_display_model, models_dict[selected_display_model]
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
def main():
    parser = argparse.ArgumentParser(
        description='Setup shell-gpt (sgpt) with Ollama server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    sudo python3 setup_sgpt.py -i 192.168.1.100
    sudo python3 setup_sgpt.py --ip 192.168.1.100
    sudo python3 setup_sgpt.py -i 192.168.1.100 -m ollama/llama3.2:latest
    sudo python3 setup_sgpt.py --ip 192.168.1.100 --model ollama/deepseek-coder-v2:latest
    sudo python3 setup_sgpt.py -i 192.168.1.100 -p 11434
    
Note: This script requires sudo privileges to install and configure shell-gpt.
      If --model/-m is not specified, the script will fetch available models from the Ollama server 
      and let you select one.
        '''
    )
    
    parser.add_argument('-i', '--ip', required=True, 
                       help='IP address of the Ollama server')
    parser.add_argument('-p', '--port', default='11434', 
                       help='Port of the Ollama server (default: 11434)')
    parser.add_argument('-m', '--model', 
                       help='Specific model to use (format: ollama/<model_name>)')
    
    args = parser.parse_args()

    # Check if script is run with sudo
    if os.geteuid() != 0:
        parser.error("This script needs to be run with sudo privileges.")

    display_model = args.model
    original_model = None

    if not display_model:
        print(f"Fetching available models from {args.ip}...")
        models_dict = get_available_models(args.ip)
        
        if not models_dict:
            print("No models found on the server.")
            sys.exit(1)
        
        display_model, original_model = select_model(models_dict)
    else:
        if not display_model.startswith('ollama/'):
            print("Error: Model name should start with 'ollama/'. Example: ollama/llama3.2:latest")
            sys.exit(1)
        original_model = display_model.replace('ollama/', '', 1)

    print(f"\nUsing model: {display_model}")

    if not is_litellm_installed():
        print("shell-gpt with litellm support not found. Installing...")
        run_command("pip uninstall shell-gpt -y", use_sudo=True)
        run_command("pip install shell-gpt[litellm]", use_sudo=True)
    else:
        print("shell-gpt with litellm support is already installed. Skipping installation.")

    if not check_config_exists():
        print("Config file not found. Initializing sgpt...")
        initialize_sgpt()
    else:
        print("Config file already exists. Skipping initialization.")

    if not is_config_already_modified(args.ip, display_model):
        print("Updating config file with new settings...")
        update_sgptrc(args.ip, display_model)
    else:
        print("Config file is already properly configured. Skipping modification.")

    print("Testing sgpt with a sample prompt...")
    run_sgpt_command('"Hello, how are you?"')

if __name__ == "__main__":
    main()
