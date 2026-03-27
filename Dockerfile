FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run sets PORT environment variable
ENV PORT=8080

# Run the FastAPI server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
