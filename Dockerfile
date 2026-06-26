FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-${RAILWAY_PORT:-8000}}"]
