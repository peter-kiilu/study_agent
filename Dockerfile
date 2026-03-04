# Use official Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Set working directory
WORKDIR /app

# Install minimal system dependencies
# build-essential is often not needed if wheels are available for all deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port (Cloud Run sets PORT env var at runtime)
EXPOSE 8080

# Steamlit configuration for Cloud Run
# 1. Use the PORT environment variable provided by Cloud Run
# 2. Disable CORS and XSRF protection as Cloud Run handles the public interface
# 3. Enable headless mode
ENTRYPOINT ["sh", "-c", "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false --server.headless=true"]
