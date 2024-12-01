import os
import subprocess
import sys

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

        # Write the modified lines back to the file
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

def main():
    # Check if script is run with sudo
    if os.geteuid() != 0:
        print("This script needs to be run with sudo privileges.")
        sys.exit(1)

    if len(sys.argv) != 3:
        print("Usage: sudo python3 setup_sgpt.py <IP> <MODEL>")
        print("Example: sudo python3 setup_sgpt.py 192.168.1.100 ollama/deepseek-coder-v2:latest")
        sys.exit(1)

    ip = sys.argv[1]
    model = sys.argv[2]

    # Check if shell-gpt with litellm is already installed
    if not is_litellm_installed():
        print("shell-gpt with litellm support not found. Installing...")
        run_command("pip uninstall shell-gpt -y", use_sudo=True)
        run_command("pip install shell-gpt[litellm]", use_sudo=True)
    else:
        print("shell-gpt with litellm support is already installed. Skipping installation.")

    # Check if config exists
    if not check_config_exists():
        print("Config file not found. Initializing sgpt...")
        initialize_sgpt()
    else:
        print("Config file already exists. Skipping initialization.")

    # Check if config is already modified as needed
    if not is_config_already_modified(ip, model):
        print("Updating config file with new settings...")
        update_sgptrc(ip, model)
    else:
        print("Config file is already properly configured. Skipping modification.")

    # Test sgpt with a sample prompt
    print("Testing sgpt with a sample prompt...")
    run_sgpt_command('"Hello, how are you?"')

if __name__ == "__main__":
    main()
