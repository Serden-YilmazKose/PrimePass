FROM python:3.11-slim

# Install system dependencies for MariaDB Python connector
RUN apt-get update && apt-get install -y \
    gcc \
    libmariadb-dev \
    libmariadb3 \
    mariadb-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application, including entrypoint.sh
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose Flask port
EXPOSE 5000

# Default entrypoint
ENTRYPOINT ["./entrypoint.sh"]