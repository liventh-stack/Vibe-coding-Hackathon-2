# Simple production Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Set environment (override in platform settings)
ENV PORT=5000
EXPOSE 5000

CMD ["python", "app.py"]
