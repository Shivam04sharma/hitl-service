FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and credentials
COPY src/ ./src/
COPY .env.local ./.env.local
COPY google-credentials.json ./google-credentials.json

EXPOSE 8003

ENV PORT=8003
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json

CMD ["python", "src/main.py"]
