import subprocess
import os
import sys
from pathlib import Path

# Define relative paths to the server files
relative_paths = {
    "ml_server": r"ML_server/ml_server.py",
    "price_predictor": r"price_predictor/price_predictor.py"
}

# Get the base directory dynamically
base_dir = Path(__file__).parent.resolve()

# Define commands to run each server with environment activation
commands = {}
for key, relative_path in relative_paths.items():
    app_path = base_dir / Path(relative_path)
    print (app_path)
    venv_path = app_path.parent / "venv"  # Assuming each server has its own 'venv' directory
    command = f"{venv_path / 'Scripts' / 'activate.bat'} && python {app_path}" if sys.platform == "win32" else f"source {venv_path / 'bin' / 'activate'} && python {app_path}"
    commands[key] = {
        "command": command,
        "directory": app_path.parent  # Get the directory for each script
    }

# Function to run each app in a new terminal
def run_app_in_new_terminal(app_name, command, app_directory):
    if sys.platform == "win32":
        # On Windows, use 'start' to open a new terminal with environment activation
        subprocess.Popen(f'start cmd /K "cd /d {app_directory} && {command}"', shell=True)
    else:
        # On Mac/Linux, use 'gnome-terminal' or similar with environment activation
        subprocess.Popen(f'gnome-terminal -- bash -c "cd {app_directory} && {command}; exec bash"', shell=True)

if __name__ == "__main__":
    # Run each server in its own terminal and set the directory dynamically
    for app_name, details in commands.items():
        command = details["command"]
        app_directory = details["directory"]
        print(f"Starting {app_name} from {app_directory}...")
        run_app_in_new_terminal(app_name, command, app_directory)

    print("All apps are running in separate terminals.")
