FROM python:3.9.18-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV TESSERACT_CMD=/usr/bin/tesseract
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DEFAULT_TIMEOUT=600
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel

RUN pip install --timeout=600 \
    fastapi uvicorn[standard] python-multipart pillow requests numpy \
    beautifulsoup4 aiohttp python-jose[cryptography] \
    python-dotenv jinja2 pytesseract opencv-python-headless

RUN pip install --timeout=600 torch torchvision --index-url https://download.pytorch.org/whl/cpu

RUN pip install --timeout=600 transformers

RUN pip install --timeout=600 easyocr || true

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]

