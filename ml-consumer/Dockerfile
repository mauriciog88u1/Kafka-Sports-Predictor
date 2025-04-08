FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#get .env creds
COPY . .
EXPOSE 8080

CMD ["python", "-u", "server.py"]
