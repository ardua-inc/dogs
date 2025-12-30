FROM python:3.11-slim

# Build arg for version tracking
ARG GIT_COMMIT=dev

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_VERSION=$GIT_COMMIT \
    FLASK_CONFIG=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directories
RUN mkdir -p /app/uploads/dog_photos /app/uploads/medical_records

EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "wsgi:app", "--config", "gunicorn.conf.py"]
