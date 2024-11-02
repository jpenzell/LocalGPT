from setuptools import setup, find_packages

setup(
    name="localgpt",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'gradio',
        'ollama',
        'python-docx',
        'PyPDF2',
    ],
    entry_points={
        'console_scripts': [
            'localgpt=app:main',
        ],
    },
)
