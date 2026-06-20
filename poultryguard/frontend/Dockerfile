FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir gradio==4.44.0 requests==2.32.3 Pillow==10.4.0

COPY frontend ./frontend

ENV POULTRYGUARD_BACKEND_URL=http://backend:8000

EXPOSE 7860
CMD ["python", "frontend/app.py"]
