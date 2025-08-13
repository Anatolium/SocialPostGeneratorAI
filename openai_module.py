import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
from google import genai
import logging

# Логирование в stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

load_dotenv()

PROXYAPI_KEY = os.getenv("PROXYAPI_KEY")
if not PROXYAPI_KEY:
    raise ValueError("PROXYAPI_KEY не найден в переменных окружения")


def get_base_url(model: str) -> str:
    if model.startswith("gpt"):
        return os.getenv("OPENAI_BASE_URL")
    elif model.startswith("claude"):
        return os.getenv("ANTHROPIC_BASE_URL")
    elif model.startswith("gemini"):
        return os.getenv("GOOGLE_BASE_URL")
    elif model.startswith("deepseek"):
        return os.getenv("DEEPSEEK_BASE_URL")
    return None


def ask_openai(system_prompt: str, user_message: str, model: str, temperature: float) -> str:
    base_url = get_base_url(model)
    if not base_url:
        raise ValueError(f"Неизвестная модель: {model}")

    logging.info(f"[{model}] base_url = {base_url}")

    # 🔹 Автоматическая фиксация температуры для gpt-5-mini
    if model == "gpt-5-mini":
        temperature = 1.0

    # --- OpenAI и DeepSeek (OpenAI API совместимый)
    if model.startswith(("gpt", "deepseek")):
        # Используем контекстный менеджер для клиента, чтобы исключить утечки соединений
        with httpx.Client() as http_client:
            client = OpenAI(
                api_key=PROXYAPI_KEY,
                base_url=base_url,
                http_client=http_client
            )
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
        return resp.choices[0].message.content.strip()

    # --- Anthropic (Claude)
    elif model.startswith("claude"):
        client = anthropic.Anthropic(
            api_key=PROXYAPI_KEY,
            base_url=base_url
        )
        resp = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=temperature,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{system_prompt}\n\n{user_message}"}
                ]
            }]
        )
        return "".join(block.text for block in resp.content if block.type == "text").strip()

    # --- Google Gemini
    elif model.startswith("gemini"):
        client = genai.Client(
            api_key=PROXYAPI_KEY,
            http_options={"base_url": base_url}
        )
        resp = client.models.generate_content(
            model=model,
            contents=[f"{system_prompt}\n\n{user_message}"],
            config={"temperature": temperature}
        )
        return resp.text.strip()

    raise ValueError(f"Модель {model} не поддерживается")
