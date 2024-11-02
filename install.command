#!/bin/bash

# Color codes for prettier output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check system requirements
check_system_requirements() {
    echo -e "${BLUE}Checking system requirements...${NC}"
    
    # Check disk space (need at least 20GB free)
    free_space=$(df -h / | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( $(echo "$free_space < 20" | bc -l) )); then
        echo -e "${RED}Error: You need at least 20GB of free disk space. Current free space: ${free_space}GB${NC}"
        exit 1
    }
    
    # Check memory (need at least 8GB)
    total_mem=$(sysctl hw.memsize | awk '{print $2}')
    total_mem_gb=$((total_mem / 1024 / 1024 / 1024))
    if [ $total_mem_gb -lt 8 ]; then
        echo -e "${RED}Error: You need at least 8GB of RAM. Current RAM: ${total_mem_gb}GB${NC}"
        exit 1
    }
    
    # Check internet connection
    if ! ping -c 1 google.com &> /dev/null; then
        echo -e "${RED}Error: No internet connection detected${NC}"
        exit 1
    }
    
    echo -e "${GREEN}System requirements met!${NC}"
}

# Function to install Ollama
install_ollama() {
    if ! command -v ollama &> /dev/null; then
        echo -e "${BLUE}Installing Ollama...${NC}"
        curl https://ollama.ai/install.sh | sh
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install Ollama${NC}"
            exit 1
        }
    else
        echo -e "${GREEN}Ollama is already installed${NC}"
    fi
}

# Function to start Ollama service
start_ollama_service() {
    echo -e "${BLUE}Starting Ollama service...${NC}"
    ollama serve &
    sleep 5  # Give ollama time to start
}

# Function to let user choose models
choose_models() {
    echo -e "${YELLOW}Which models would you like to install?${NC}"
    
    models=("mistral" "codellama" "llama2" "neural-chat" "phi")
    selected_models=()
    
    for model in "${models[@]}"; do
        read -p "Install $model? (y/n): " choice
        case "$choice" in 
            y|Y ) selected_models+=("$model");;
            * ) echo "Skipping $model";;
        esac
    done
    
    return 0
}

# Function to download models with progress
download_models() {
    total_models=${#selected_models[@]}
    current_model=1
    
    for model in "${selected_models[@]}"; do
        echo -e "${BLUE}Downloading $model (Model $current_model of $total_models)${NC}"
        ollama pull $model
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to download $model${NC}"
            read -p "Continue with remaining models? (y/n): " continue_choice
            if [[ $continue_choice != "y" ]]; then
                exit 1
            fi
        else
            echo -e "${GREEN}Successfully downloaded $model${NC}"
        fi
        
        ((current_model++))
    done
}

# Main installation process
main() {
    echo -e "${BLUE}Welcome to LocalGPT Installer${NC}"
    
    # Check if this is a first-time installation
    if [ ! -f ~/.localgpt_installed ]; then
        check_system_requirements
        install_ollama
        choose_models
        start_ollama_service
        download_models
        touch ~/.localgpt_installed
    else
        echo -e "${GREEN}LocalGPT is already installed${NC}"
        read -p "Would you like to install additional models? (y/n): " install_more
        if [[ $install_more == "y" ]]; then
            choose_models
            start_ollama_service
            download_models
        fi
    fi
    
    echo -e "${GREEN}Starting LocalGPT...${NC}"
    open LocalGPT.app
}

# Error handling wrapper
set -e
trap 'echo -e "${RED}An error occurred during installation${NC}"; exit 1' ERR

# Run main installation
main
