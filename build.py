import os
import sys
import shutil

print("Creating installation package...")

try:
    # Create installer directory
    if os.path.exists('LocalGPT-Installer'):
        shutil.rmtree('LocalGPT-Installer')
    os.makedirs('LocalGPT-Installer')
    
    # Copy the required files
    files_to_copy = ['app.py', 'requirements.txt']
    for file in files_to_copy:
        shutil.copy(file, 'LocalGPT-Installer/')
    
    # Create the launcher script with all models
    launcher_path = os.path.join('LocalGPT-Installer', 'Launch LocalGPT.command')
    with open(launcher_path, 'w') as f:
        f.write('''#!/bin/bash

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Xcode Command Line Tools
if ! command_exists xcode-select; then
    echo "Installing Xcode Command Line Tools..."
    xcode-select --install
    echo "After Xcode Command Line Tools installation completes, please run this script again."
    exit 1
fi

# Check for Homebrew
if ! command_exists brew; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Check for Ollama
if ! command_exists ollama; then
    echo "Installing Ollama..."
    brew install ollama
    brew services start ollama
fi

# Check for Python
if ! command_exists python3; then
    echo "Installing Python..."
    brew install python@3.11
fi

# Check for pip
if ! command_exists pip3; then
    echo "Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv venv
fi

# Function to check and pull models
check_and_pull_model() {
    local model=$1
    if ! ollama list | grep -q "$model"; then
        echo "Downloading $model model (this may take a few minutes)..."
        ollama pull $model
    else
        echo "$model model already installed"
    fi
}

# Start Ollama service if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    brew services start ollama
    # Give it a moment to start
    sleep 5
fi

# Install all required models
echo "Checking and installing required models..."
check_and_pull_model "mistral"
check_and_pull_model "llama2"
check_and_pull_model "codellama"
check_and_pull_model "neural-chat"
check_and_pull_model "starling-lm"
check_and_pull_model "dolphin-phi"
check_and_pull_model "phi"

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run the app
echo "Starting LocalGPT..."
python3 app.py
''')
    
    # Make launcher executable
    os.chmod(launcher_path, 0o755)
    
    # Create README
    with open(os.path.join('LocalGPT-Installer', 'README.txt'), 'w') as f:
        f.write('''LocalGPT Quick Start Guide

1. Double-click "Launch LocalGPT.command"
   (You may need to right-click and select "Open" the first time)
2. Wait for setup to complete
3. The chat interface will open in your browser

Requirements:
- macOS 10.15 or later
- Python 3.8 or later
- Internet connection for first-time setup

For support, visit: https://github.com/jpenzell/LocalGPT
''')
    
    # Create zip file
    if os.path.exists('LocalGPT-Mac.zip'):
        os.remove('LocalGPT-Mac.zip')
    shutil.make_archive('LocalGPT-Mac', 'zip', 'LocalGPT-Installer')
    
    print("\nPackaging complete!")
    print("Your distribution package is ready: LocalGPT-Mac.zip")
    
except Exception as e:
    print(f"Error during packaging: {str(e)}")
    sys.exit(1)
