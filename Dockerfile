FROM python:3.9.18-slim

RUN apt-get update && apt-get install -y \
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

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --timeout=300 \
    fastapi uvicorn[standard] python-multipart pillow requests numpy pandas \
    scikit-learn beautifulsoup4 aiohttp python-jose[cryptography] \
    python-dotenv jinja2 pytesseract opencv-python-headless && \
    pip install --no-cache-dir --timeout=300 transformers torch && \
    pip install --no-cache-dir --timeout=300 easyocr

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]

