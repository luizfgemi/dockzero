# ---------- base ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl && \
    pip install --no-cache-dir --upgrade pip

# ---------- app ----------
WORKDIR /code
COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt && \
    apt-get purge -y gcc && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY app /code/app
ENV PYTHONPATH=/code

WORKDIR /code/app
EXPOSE 7070

# ---------- runtime ----------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7070"]
