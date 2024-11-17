import os
import subprocess
import sys

def update_sgptrc(ip, model):
    sgptrc_path = os.path.expanduser("~/.config/shell_gpt/.sgptrc")
    
    try:
        with open(sgptrc_path, "r") as file:
            lines = file.readlines()

        # Modify the lines as needed
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

        # Write the modified lines back to the file
        with open(sgptrc_path, "w") as file:
            file.writelines(lines)

        print(f"Updated {sgptrc_path} successfully.")
        
    except FileNotFoundError:
        print(f"Error: Config file {sgptrc_path} not found. Ensure sgpt was initialized properly.")
        sys.exit(1)

def run_command(command, input_text=None):
    try:
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
        
def main():
    if len(sys.argv) != 3:
        print("Usage: python3 setup_sgpt.py <IP> <MODEL>")
        print("Example: python3 setup_sgpt.py 192.168.1.100 ollama/deepseek-coder-v2:latest")
        sys.exit(1)

    ip = sys.argv[1]
    model = sys.argv[2]

    # Step 1: Uninstall shell-gpt
    print("Uninstalling shell-gpt...")
    run_command("pip uninstall shell-gpt -y")

    # Step 2: Install shell-gpt with litellm support
    print("Installing shell-gpt with litellm support...")
    run_command("pip install shell-gpt[litellm]")

    # Step 3: Run sgpt to generate the config file
    print("Initializing sgpt to generate the config file...")
    run_command("echo 'gibberish' | sgpt")

    # Step 4: Update the sgptrc config file
    print("Updating sgptrc config file...")
    update_sgptrc(ip, model)

    # Step 5: Test sgpt with a sample prompt
    print("Testing sgpt with a sample prompt...")
    run_command('sgpt "Hello, how are you?"')

if __name__ == "__main__":
    main()
