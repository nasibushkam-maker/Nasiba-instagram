FROM python:3.12-slim

# Tizim paketlari (FFmpeg va Chromium) o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    chromium \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllarini ko'chirish
COPY . .

# Render standarti bo'yicha PORT
ENV PORT=10000

CMD ["python", "main.py"]
