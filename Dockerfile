FROM python:3.13-slim

ARG CONTAINER_NAME
ARG CONTAINER_PORT

ENV CONTAINER_NAME=${CONTAINER_NAME}
ENV CONTAINER_PORT=${CONTAINER_PORT}

WORKDIR /api

COPY ${CONTAINER_NAME}.py config.py pyproject.toml ./

RUN mv config.py config.py_old \
    && grep -E '^from collections' config.py_old > config.py \
    && sed -n '/^# COLORS/,/^$/p' config.py_old >> config.py \
    && sed -n '/^ProviderProps =/,/^$/p' config.py_old >> config.py \
    && sed -n '/^PROVIDERS =/,/^$/p' config.py_old >> config.py \
    && sed -n '/^USER_AGENTS =/,/^$/p' config.py_old >> config.py \
    && grep -E '^LOG|^URLS|^REQ' config.py_old >> config.py \
    && rm config.py_old

RUN sed -i.bak "s/\${CONTAINER_NAME}/${CONTAINER_NAME}/g" pyproject.toml \
    && pip install --upgrade pip \
    && pip install --no-cache-dir . \
    && rm pyproject.toml*

RUN apt update \
    && apt install -y iputils-ping curl lsof \
    && ln -snf /usr/share/zoneinfo/Asia/Manila /etc/localtime \
    && echo Asia/Manila > /etc/timezone \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# RUN sudo certbot --apache -d scatter.goldenarbitrage.net
    
CMD [ "sh", "-c", "uvicorn ${CONTAINER_NAME}:app --host 0.0.0.0 --port ${CONTAINER_PORT}" ]
