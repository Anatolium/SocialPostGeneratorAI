## Генератор постов для соцсетей (ИИ‑агент)

Этот ИИ‑агент по указанному URL извлекает текст страницы и генерирует пост для соцсетей. Можно выбрать один из 6 стилей, одну из 6 моделей (OpenAI, Anthropic, Google, DeepSeek), а также настроить температуру и максимальную длину ответа.

### Основные возможности
- **Стили**: информативный, ироничный, дерзкий, позитивный, официальный, юмористический.
- **Модели**:
  - OpenAI: `gpt-4o-mini`, `gpt-4.1-mini`, `gpt-5-mini`
  - Anthropic: `claude-3-haiku-20240307`
  - Google: `gemini-2.5-flash`
  - DeepSeek: `deepseek-chat`
- **Настройки генерации**:
  - **Температура** промпта (0.0–1.0). Для `gpt-5-mini` температура автоматически фиксируется на 1.0.
  - **Лимит символов без пробелов**. Агент строго укладывается в заданный предел: при превышении перегенерирует/ужимает текст, сохраняя целостность предложений.
- **Формат поста**: минимум два абзаца, абзацы разделяются пустой строкой.

### Структура проекта
- `agent.py` — веб‑приложение Flask: формы, обработка запроса, получение контента по URL, вызовы модели, контроль лимита длины.
- `openai_module.py` — единая обёртка для вызова моделей (OpenAI/Anthropic/Google/DeepSeek) через Proxy API.
- `templates/index.html` — минимальный UI: выбор стиля, модели, температуры и лимита символов, отправка URL.

### Требования
- Python 3.11+
- Рекомендуется Docker (опционально)
- Proxy API‑ключ и базовые URL провайдеров (см. Переменные окружения)

### Переменные окружения (.env)
- `PROXYAPI_KEY` — ключ доступа к Proxy API (используется для всех провайдеров)
- `OPENAI_BASE_URL` — базовый URL для моделей OpenAI
- `ANTHROPIC_BASE_URL` — базовый URL для моделей Anthropic
- `GOOGLE_BASE_URL` — базовый URL для моделей Google (Gemini)
- `DEEPSEEK_BASE_URL` — базовый URL для моделей DeepSeek
- `FLASK_DEBUG` — опционально, включает debug‑режим Flask при локальном запуске (`1/true/yes/y`)

Пример `.env`:
```bash
PROXYAPI_KEY=your_proxy_api_key
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1
GOOGLE_BASE_URL=https://api.proxyapi.ru/google
ANTHROPIC_BASE_URL=https://api.proxyapi.ru/anthropic
DEEPSEEK_BASE_URL=https://api.proxyapi.ru/deepseek
FLASK_DEBUG=0
```

### Локальный запуск (без Docker)
1) Установите зависимости:
```bash
pip install -r requirements.txt
```
2) Создайте `.env` (см. пример выше).
3) Запустите приложение:
```bash
python agent.py
```
По умолчанию Flask поднимется на `http://127.0.0.1:5000/`. Для dev‑режима выставьте `FLASK_DEBUG=1`.

### Запуск в Docker
- Сборка и запуск контейнера напрямую:
```bash
docker build -t post-generator-ai:latest .
docker run --rm -p 8000:8000 --env-file .env --name post-generator-ai post-generator-ai:latest
```
Откройте `http://localhost:8000/`.

- Запуск через docker‑compose:
```bash
docker compose up -d --build
```
Контейнер будет иметь имя `post-generator-ai`, порт по умолчанию — `8000`.

### Примечания по безопасности и надёжности
- Выполняется базовая SSRF‑гигиена: допустимы только публичные `http/https` URL, локальные/приватные диапазоны отклоняются.
- В продакшне приложение запускается через Gunicorn (см. `Dockerfile`), healthcheck настроен на `GET /`.
- Для модели `gpt-5-mini` температура принудительно устанавливается в 1.0 (UI также блокирует изменение температуры для неё).

### Лицензия
MIT
