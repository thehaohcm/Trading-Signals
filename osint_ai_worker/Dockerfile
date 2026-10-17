FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tạm thời: bản sửa lỗi 403 của edge-tts (Microsoft đổi endpoint từ 10/10/2026 — rany2/edge-tts PR #491),
# ghim theo commit. Không cài được thì build vẫn tiếp tục và podcast tự dùng gTTS.
# Gỡ bước này khi edge-tts ra bản chính thức sửa lỗi (theo dõi rany2/edge-tts#490).
RUN pip install --no-cache-dir --no-deps --force-reinstall \
    https://github.com/jonata/edge-tts/archive/8a5844c3a1d33e4e8f2f3e14535542c0d75d4248.zip \
    || echo "⚠️ Không cài được bản sửa edge-tts — dùng bản chính thức + gTTS dự phòng"

# Copy the rest of the application code
COPY . .

# Run the python worker
CMD ["python", "osint_ai_worker.py"]
