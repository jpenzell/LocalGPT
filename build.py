import PyInstaller.__main__

PyInstaller.__main__.run([
    'app.py',
    '--onefile',
    '--name=LocalGPT',
    '--hidden-import=gradio',
    '--hidden-import=ollama',
    '--hidden-import=python-docx',
    '--hidden-import=PyPDF2',
    '--collect-all=gradio',
    '--noconfirm'
])
