FROM python:3.13-slim

ARG CONTAINER_NAME
ARG CONTAINER_PORT

ENV CONTAINER_PORT=${CONTAINER_PORT}

WORKDIR /api

COPY data-api.py config.py pyproject.toml ./

RUN mv config.py config.py_old \
    && grep -E '^from collections' config.py_old > config.py \
    && sed -n '/^# COLORS/,/^$/p' config.py_old >> config.py \
    && sed -n '/^ProviderProps =/,/^$/p' config.py_old >> config.py \
    && sed -n '/^PROVIDERS =/,/^$/p' config.py_old >> config.py \
    && sed -n '/^USER_AGENTS =/,/^$/p' config.py_old >> config.py \
    && grep -E '^LOG' config.py_old >> config.py \
    && rm config.py_old

RUN sed -i.bak "s/\${CONTAINER_NAME}/${CONTAINER_NAME}/g" pyproject.toml \
    && pip install --no-cache-dir . \
    && rm pyproject.toml*

RUN apt update \
    && apt install -y iputils-ping curl lsof \
    && ln -snf /usr/share/zoneinfo/Asia/Manila /etc/localtime \
    && echo Asia/Manila > /etc/timezone \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*
    
CMD [ "sh", "-c", "uvicorn data-api:app --host 0.0.0.0 --port ${CONTAINER_PORT}" ]
