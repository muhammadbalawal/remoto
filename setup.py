from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="remoto-ai",
    version="1.0.0",
    description="Voice-controlled remote computer access with AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Muhammad Balawal",
    url="https://github.com/muhammadbalawal/remoto",
    license="MIT",
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
        "backboard-sdk>=1.4.0",
        "pillow>=10.0",
        "numpy>=1.24",
        "httpx>=0.27.0",
    ],
    entry_points={
        "console_scripts": [
            "remoto=cli.main:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
