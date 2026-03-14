FROM python:3.14.2-slim-trixie

RUN apt update && \
apt install -y sqlite3 && \
rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]