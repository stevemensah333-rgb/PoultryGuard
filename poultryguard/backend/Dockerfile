# Backend image. NOTE: this base image is CPU-only for portability.
# For AMD GPU (ROCm) inference, see README.md "Running on an AMD GPU" --
# you'll run the backend directly on the ROCm host rather than in this
# generic container, or build a ROCm-base variant of this Dockerfile.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY backend ./backend
COPY poultryguard_cli.py .

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
