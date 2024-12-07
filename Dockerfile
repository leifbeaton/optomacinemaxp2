# Use a lightweight base image
FROM python:3.9-slim

# Install ADB and other dependencies
RUN apt-get update && apt-get install -y adb && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app
WORKDIR /app

# Expose the API port
EXPOSE 8080

# Run the API server
CMD ["python", "server.py"]
