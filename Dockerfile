FROM python:3.10-slim

WORKDIR /app

# System deps (NO inline comments after \)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libglib2.0-0 \
    libstdc++6 \
    libasound2 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY honest_stylist/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY honest_stylist/app /app/app
COPY honest_stylist/assets /app/assets

# Runtime dirs
RUN mkdir -p /app/rlhf_logs

# Env
ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8000 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

EXPOSE 8000

CMD ["streamlit", "run", "app/app.py", "--server.port=8000", "--server.address=0.0.0.0"]
