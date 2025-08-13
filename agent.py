from flask import Flask, render_template, request
import os
import re
import requests
from bs4 import BeautifulSoup
from openai_module import ask_openai

from urllib.parse import urlparse

app = Flask(__name__)

STYLES = [
    "информативный",
    "ироничный",
    "дерзкий",
    "позитивный",
    "официальный",
    "юмористический"
]

MODELS = [
    "gpt-4o-mini",
    "gpt-4.1-mini",
    "gpt-5-mini",
    "claude-3-haiku-20240307",
    "gemini-2.5-flash",
    "deepseek-chat",
]

TEMPERATURE = 0.7
MAX_LENGTH = 800


@app.route("/", methods=["GET", "POST"])
def index():
    models = MODELS
    temps = [round(x * 0.1, 1) for x in range(0, 11)]  # 0.0 ... 1.0
    post = error = None
    url = ""

    # Дефолты
    style = "информативный"
    model = "gpt-4o-mini"
    temperature = TEMPERATURE
    max_length = MAX_LENGTH

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        style = request.form.get("style", style)  # дефолт информативный
        model = request.form.get("model", model)
        try:
            temperature = float(request.form.get("temperature", temperature))
        except ValueError:
            temperature = TEMPERATURE
        try:
            max_length = int(request.form.get("max_length", max_length))
        except ValueError:
            max_length = MAX_LENGTH

        try:
            post = generate_post(url, style, max_length, model=model, temperature=temperature)
        except Exception as e:
            error = str(e)

    return render_template(
        "index.html",
        styles=STYLES,
        style=style,
        post=post,
        error=error,
        models=models,
        model=model,
        temps=temps,
        temperature=temperature,
        url=url,
        max_length=max_length
    )


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def extract_clean_text_from_url(url: str, max_input_chars: int = 10000) -> str:
    try:
        # response = requests.get(url, timeout=10)
        headers = {"User-Agent": "Mozilla/5.0 (compatible; PostGenerator/1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Ошибка загрузки страницы: {e}")

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = " ".join(soup.stripped_strings)
    return text[:max_input_chars]


def length_without_spaces(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def finish_sentence(text: str) -> str:
    """Обрезает текст по последнему знаку окончания предложения."""
    # end_index = max(text.rfind("."), text.rfind("!"), text.rfind("?"))
    end_index = max((text.rfind(p) for p in ".!?"), default=-1)
    if end_index != -1:
        return text[:end_index + 1].strip()
    return text.strip() + "."


def generate_post(url: str, style: str = "ироничный", max_length: int = 800,
                  model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    page_text = extract_clean_text_from_url(url)

    style_examples = {
        "ироничный": {
            "desc": "Сарказм, насмешка, лёгкий цинизм, преувеличения.",
            "good": "Учёные выяснили, что кофе бодрит. Браво! Осталось открыть, что снег холодный.",
            "bad": "Кофе помогает проснуться."
        },
        "информативный": {
            "desc": "Факты, краткость, отсутствие эмоций.",
            "good": "Кофе содержит кофеин, который стимулирует нервную систему и повышает бодрость.",
            "bad": "Кофе — лучший друг любого студента."
        },
        "дерзкий": {
            "desc": "Скепсис, цинизм, сарказм, мизантропия, вызов.",
            "good": "Всё ещё пьёшь растворимый кофе? Ты живёшь в прошлом. Исправляйся. Хотя тебе уже вряд ли что-то поможет.",
            "bad": "Кофе вкусный напиток."
        },
        "позитивный": {
            "desc": "Воодушевляющий, доброжелательный тон.",
            "good": "Кофе — маленькая чашка счастья, которая заряжает на весь день!",
            "bad": "Кофе иногда помогает."
        },
        "официальный": {
            "desc": "Нейтральный, деловой стиль.",
            "good": "Кофе — напиток, содержащий кофеин, употребляется для повышения работоспособности.",
            "bad": "Кофе — это супернапиток!"
        },
        "юмористический": {
            "desc": "Шутки, игра слов, лёгкость.",
            "good": "Кофе — как пароль от Wi-Fi: без него утром жизнь не подключается.",
            "bad": "Кофе — тёплый напиток."
        }
    }

    style_data = style_examples.get(style, style_examples["ироничный"])

    system_prompt = (
        f"Ты — популярный автор постов для соцсетей с миллионами подписчиков. "
        "Напиши пост для соцсети с обзором текста на данной веб-странице. "
        "Пост должен начинаться с яркого утверждения, затем краткое пояснение, и завершаться выводом. "
        f"Всегда пиши строго в стиле '{style}': {style_data['desc']} "
        "Если стиль не соблюдается, перепиши до соответствия. "
        "Не используй нейтральный тон. "
        f"Длина поста — не более {max_length} знаков без пробелов. "
        "Это абсолютный предел, превышение недопустимо. "
        "Если текст не умещается — сокращай, убирай детали, перефразируй. "
        "Заверши пост чётким финальным предложением. "
        "Никаких продолжений или намёков на незавершённость. "
        "Разбивай текст на абзацы - не больше 3-4 предложений в каждом. "
        "Текст должен состоять как минимум из двух абзацев. "
        "Каждый абзац отделяй пустой строкой."
    )

    few_shot_examples = (
        f"Пример хорошего поста в стиле '{style}':\n{style_data['good']}\n\n"
        f"Пример плохого поста (не в стиле):\n{style_data['bad']}\n\n"
    )

    try:
        # Первая генерация
        result_text = ask_openai(
            system_prompt,
            f"{few_shot_examples}Текст статьи:\n{page_text}\n\nНапиши пост.",
            model=model,
            temperature=temperature
        ).strip()

        # Проверка и перегенерация, если превышен лимит > 10%
        if length_without_spaces(result_text) > max_length * 1.1:
            result_text = ask_openai(
                system_prompt + " Ты превысил лимит в прошлый раз, сократи текст.",
                f"{few_shot_examples}Текст статьи:\n{page_text}\n\nНапиши пост.",
                model=model,
                temperature=temperature
            ).strip()

        # Финальная подрезка до окончания предложения
        result_text = finish_sentence(result_text)

        return result_text

    except Exception as e:
        raise RuntimeError(f"Ошибка при обращении к OpenAI API: {e}")


if __name__ == "__main__":
    debug_env = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes", "y"}
    app.run(debug=debug_env)
