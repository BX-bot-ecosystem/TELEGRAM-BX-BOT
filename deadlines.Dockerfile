FROM python:3.10

WORKDIR /app

COPY src/deadlines_bot/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/deadlines_bot ./
COPY src/utils ./utils
COPY src/data ./data
COPY credentials.json ../


EXPOSE 80

# Run your application
CMD ["python", "BX-Telegram.py"]