# Etapa de build: compila dependencias sem levar compiladores para a imagem final.
FROM python:3.11-slim AS builder

WORKDIR /app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Etapa de runtime: apenas bibliotecas necessarias para executar a API.
FROM python:3.11-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system taskflow \
    && useradd --system --gid taskflow --home-dir /app --shell /usr/sbin/nologin taskflow

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=taskflow:taskflow . .
RUN chmod 755 /app/entrypoint.sh && chown taskflow:taskflow /app

USER taskflow
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
