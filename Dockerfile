FROM python:3.12 AS builder
WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

FROM python:3.12
WORKDIR /app

COPY --from=builder /usr/local/ /usr/local/
COPY . .

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    DJANGO_DEBUG=True

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
