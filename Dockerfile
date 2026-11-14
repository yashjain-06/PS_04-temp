FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "gunicorn wsgi:app --worker-class gthread --workers 1 --threads 32 --timeout 0 --bind 0.0.0.0:${PORT}"]
