# Incisive Nova - Backend API (FastAPI orquestador)
# Imagen multi-stage: builder de dependencias + runtime slim.

# ---- Stage 1: builder ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Instala dependencias en un virtualenv aislado para copiarlo al runtime.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# ---- Stage 2: runtime ----
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Usuario no-root por seguridad.
RUN groupadd --system app && useradd --system --gid app --create-home appuser

# Copia el virtualenv con las dependencias desde el builder.
COPY --from=builder /opt/venv /opt/venv

# Copia el código de la aplicación.
COPY src ./src

USER appuser

EXPOSE 8000

# Healthcheck alineado con el endpoint /health de la app.
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
