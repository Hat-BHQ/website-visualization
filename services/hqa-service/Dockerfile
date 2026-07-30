FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Cài:
# - build-essential: dùng khi package Python cần compile.
# - libpq-dev: hỗ trợ PostgreSQL/psycopg.
# - fonts-dejavu-core: font Unicode hỗ trợ tiếng Việt cho PDF.
# - fontconfig: cung cấp lệnh fc-list, fc-match để kiểm tra font.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        fonts-dejavu-core \
        fontconfig \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
COPY app /app/app
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

RUN pip install --upgrade pip \
    && pip install -e .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]