FROM python:3.13-slim

WORKDIR /api

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN apt update && \
    apt install -y iputils-ping lsof && \
    rm -rf /var/lib/apt/lists/*

COPY data.py config.py ./

CMD [ "uvicorn", "data:app", "--host", "0.0.0.0", "--port", "8080" ]
