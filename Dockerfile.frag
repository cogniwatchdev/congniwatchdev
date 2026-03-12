FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y nmap curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi uvicorn jinja2 python-multipart sqlalchemy python-jose passlib aiofiles
COPY backend/ /app/backend/
COPY webui/ /app/webui/
ENV PYTHONPATH=/app
RUN chmod -R 755 /app
EXPOSE 9000
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "9000"]
