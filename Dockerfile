FROM python:3.10-slim

WORKDIR /app

# Ensure standard build tools are available for chromadb / sentence-transformers
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files (including chromadb, json, keys)
COPY . .

# Ensure start.sh is executable
RUN chmod +x start.sh

# Render or Railway typically expose their listening port as $PORT
EXPOSE 8000

# Run our start.sh subscript
CMD ["./start.sh"]
