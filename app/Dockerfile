# ---------- base ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# instala dependências mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn docker && \
    apt-get purge -y gcc && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# ---------- app ----------
WORKDIR /app
COPY main.py .

EXPOSE 7070

# ---------- runtime ----------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7070"]
