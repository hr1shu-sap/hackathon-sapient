# Multi-stage build for Honest Stylist Streamlit app
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY honest_stylist/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY honest_stylist/app /app/app
COPY honest_stylist/assets /app/assets
COPY honest_stylist/*.json /app/ 2>/dev/null || true

# Create necessary directories
RUN mkdir -p /app/rlhf_logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8000
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false

# Expose port
EXPOSE 8000

# Run Streamlit app
CMD ["streamlit", "run", "app/app.py", "--server.port=8000", "--server.address=0.0.0.0", "--logger.level=info"]
