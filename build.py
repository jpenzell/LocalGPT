import PyInstaller.__main__
import os
import subprocess

# Try to find ollama binary
def find_ollama_path():
    try:
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    # Check common locations
    possible_paths = [
        '/usr/local/bin/ollama',
        '/opt/homebrew/bin/ollama',
        '/usr/bin/ollama'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

ollama_path = find_ollama_path()
build_args = [
    'app.py',
    '--name=LocalGPT',
    '--onefile',
    '--windowed',
    '--hidden-import=gradio',
    '--hidden-import=ollama',
    '--hidden-import=python-docx',
    '--hidden-import=PyPDF2',
    '--collect-all=gradio',
    '--noconfirm'
]

# Add ollama binary if found
if ollama_path:
    build_args.extend(['--add-binary', f'{ollama_path}:.'])

PyInstaller.__main__.run(build_args)
