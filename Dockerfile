# syntax=docker/dockerfile:1

########################################
# Этап 1 — установка зависимостей
########################################
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Обновим pip сразу
RUN pip install --upgrade pip

# Установим системные зависимости для сборки пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Скопируем только requirements.txt для кеширования
COPY requirements.txt ./

# Устанавливаем зависимости в отдельную папку (чтобы потом перенести)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

########################################
# Этап 2 — финальный образ
########################################
FROM python:3.11-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Минимальный набор системных пакетов для рантайма
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные зависимости из builder
COPY --from=builder /install /usr/local

# Копируем проект
COPY . .

# Экспортируем порт
EXPOSE 8000

# Переменные окружения
ENV PORT=8000 \
    HOST=0.0.0.0

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/ >/dev/null || exit 1

# Запуск через gunicorn
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-t", "60", "-b", "0.0.0.0:8000", "agent:app"]
