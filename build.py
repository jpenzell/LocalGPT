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
    
    # Create the launcher script with dynamic model loading
    launcher_path = os.path.join('LocalGPT-Installer', 'Launch LocalGPT.command')
    with open(launcher_path, 'w') as f:
        f.write('''#!/bin/bash

# Function to fetch latest models from Ollama
fetch_latest_models() {
    echo "Fetching available models from Ollama..."
    # Get list of all available models from Ollama
    available_models=$(curl -s https://ollama.ai/library)
    
    # Update our models.json with new information
    python3 -c '
import json
import sys
import requests

def update_models_file():
    try:
        # Load current models file
        with open("models.json", "r") as f:
            current_models = json.load(f)
        
        # Fetch latest models from Ollama API
        response = requests.get("https://ollama.ai/api/tags")
        latest_models = response.json()
        
        # Update existing models with latest info
        for category in current_models:
            for model_name in current_models[category]:
                if model_name in latest_models:
                    current_models[category][model_name]["size"] = latest_models[model_name]["size"]
                    current_models[category][model_name]["last_updated"] = latest_models[model_name]["updated"]
        
        # Add new models to "new" category
        current_models.setdefault("new", {})
        for model_name, info in latest_models.items():
            found = False
            for category in current_models:
                if model_name in current_models[category]:
                    found = True
                    break
            if not found:
                current_models["new"][model_name] = {
                    "size": info["size"],
                    "description": "New model from Ollama",
                    "priority": 5,
                    "last_updated": info["updated"]
                }
        
        # Save updated models file
        with open("models.json", "w") as f:
            json.dump(current_models, f, indent=4)
            
        return "Models updated successfully!"
    except Exception as e:
        return f"Error updating models: {str(e)}"

print(update_models_file())
'
}

# Function to manage models
manage_models() {
    while true; do
        clear
        echo "=== LocalGPT Model Management ==="
        echo "1. List installed models"
        echo "2. Install new models"
        echo "3. Remove models"
        echo "4. Update existing models"
        echo "5. Check for new models"
        echo "6. Start LocalGPT"
        echo "7. Exit"
        echo ""
        read -p "Select an option (1-7): " choice

        case $choice in
            1)
                echo "Installed models:"
                ollama list
                read -p "Press Enter to continue..."
                ;;
            2)
                python3 -c '
import json
with open("models.json") as f:
    models = json.load(f)
print("\\nAvailable models:\\n")
for category, model_group in models.items():
    print(f"=== {category.title()} ===")
    for model, details in model_group.items():
        print(f"{model} ({details[\"size\"]}): {details[\"description\"]}")
'
                read -p "Enter model name to install (or Enter to cancel): " model
                if [ ! -z "$model" ]; then
                    check_and_pull_model "$model"
                fi
                ;;
            3)
                echo "Select model to remove:"
                ollama list
                read -p "Enter model name to remove (or Enter to cancel): " model
                if [ ! -z "$model" ]; then
                    ollama rm "$model"
                fi
                ;;
            4)
                echo "Updating installed models..."
                ollama list | while read model rest; do
                    if [ ! -z "$model" ]; then
                        echo "Updating $model..."
                        ollama pull "$model"
                    fi
                done
                read -p "Press Enter to continue..."
                ;;
            5)
                fetch_latest_models
                read -p "Press Enter to continue..."
                ;;
            6)
                return
                ;;
            7)
                exit 0
                ;;
            *)
                echo "Invalid option"
                sleep 1
                ;;
        esac
    done
}

# Start Ollama service if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    brew services start ollama
    sleep 5
fi

# Show model management interface
manage_models

# Activate virtual environment and run app
source venv/bin/activate
python3 app.py
''')

    # Copy models.json to the installer package
    shutil.copy('models.json', 'LocalGPT-Installer/')
    
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
