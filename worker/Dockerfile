FROM python:3.11-slim
WORKDIR /app
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api /app/api
COPY worker /app/worker
ENV PYTHONPATH=/app
CMD ["python", "worker/main.py"]
