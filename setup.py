from setuptools import setup, find_packages
import os

# Get current directory
here = os.path.abspath(os.path.dirname(__file__))

setup(
    name="remoto-ai",
    version="1.0.0",
    description="Voice-controlled remote computer access with AI",
    packages=find_packages(where=here, include=['cli', 'cli.*']),
    package_dir={'': '.'},
    install_requires=[
        "click>=8.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0",
        "psutil>=5.9",
        "requests>=2.31",
        "fastapi>=0.100",
        "uvicorn>=0.20",
        "pyautogui>=0.9",
        "opencv-python>=4.8",
        "pytesseract>=0.3",
        "gtts>=2.3",
        "anthropic>=0.18",
        "pillow>=10.0",
        "numpy>=1.24",
    ],
    entry_points={
        "console_scripts": [
            "remoto=cli.main:main",
        ],
    },
    python_requires=">=3.8",
)