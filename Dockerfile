FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY receptionist_ai/ ./receptionist_ai/

CMD ["fastapi", "run","receptionist_ai/make_call.py","--host","0.0.0.0","--port", "8000"]

