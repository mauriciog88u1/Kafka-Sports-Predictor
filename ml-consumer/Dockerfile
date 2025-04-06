FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#get .env creds
COPY . .

CMD ["python", "-u", "server.py"]
