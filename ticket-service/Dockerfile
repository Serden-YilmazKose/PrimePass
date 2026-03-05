FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libmariadb-dev \
    libmariadb3 \
    mariadb-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 5003

ENTRYPOINT ["./entrypoint.sh"]