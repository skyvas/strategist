FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST_PIN=1515

COPY . /app

EXPOSE 8080

CMD ["python3", "app.py", "--port", "8080"]
