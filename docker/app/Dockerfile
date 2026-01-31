FROM python:3.14.2-slim-trixie

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
#一時的
CMD ["tail", "-f", "/dev/null"]