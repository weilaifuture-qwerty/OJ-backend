FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/static /app/media /app/test_cases /app/logs

# Set permissions
RUN chmod +x /app/manage.py

EXPOSE 8000

CMD ["gunicorn", "oj.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "300"]