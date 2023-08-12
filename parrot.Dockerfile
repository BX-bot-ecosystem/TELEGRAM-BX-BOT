# Use an official Python runtime as the base image
FROM python:3.10

WORKDIR /app

COPY src/parrot_bot/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/parrot_bot ./
COPY src/utils ./utils
COPY src/data ./data
COPY credentials.json ../


EXPOSE 80

# Run your application
CMD ["python", "BX-Telegram.py"]
