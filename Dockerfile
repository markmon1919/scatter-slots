FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt update && \
    apt install -y iputils-ping lsof vim

COPY api.py .

COPY config.py .

EXPOSE 8080

CMD [ "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080" ]
