# Use an official Python runtime as the base image
FROM python:3.10

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./
COPY service_account.json ../

EXPOSE 80

CMD ["python", "BX-Telegram.py"]
