import PyInstaller.__main__

PyInstaller.__main__.run([
    'app.py',
    '--name=LocalGPT',
    '--onefile',
    '--windowed',
    '--add-binary=/usr/local/bin/ollama:.',
    '--hidden-import=gradio',
    '--hidden-import=ollama',
    '--hidden-import=python-docx',
    '--hidden-import=PyPDF2',
    '--collect-all=gradio',
    '--icon=app_icon.icns',
    '--noconfirm'
])
