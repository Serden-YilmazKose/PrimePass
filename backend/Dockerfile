FROM python:3.11-slim

# Install system dependencies required for mariadb Python connector
RUN apt-get update && apt-get install -y \
    gcc \
    libmariadb-dev \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY app/ .

# Expose Flask port
EXPOSE 5000

# Run the Flask app
CMD ["python", "server.py"]
