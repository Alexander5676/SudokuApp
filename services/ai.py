"""OpenAI service for marketplace product description generation."""

import logging

from openai import AsyncOpenAI, OpenAIError

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Raised when the AI provider cannot generate a response."""


class AIService:
    """Generates Wildberries/Ozon-ready product descriptions."""

    def __init__(self, api_key: str, model: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_product_description(self, product_name: str) -> str:
        """Generate a selling description and SEO keyword list for a product."""
        logger.info("Generating marketplace description for product: %s", product_name)

        prompt = f"""
Сгенерируй текст для карточки товара на Wildberries и Ozon.

Название товара: {product_name}

Требования к ответу:
1. Продающее описание на русском языке до 1000 символов.
2. SEO-ключевые слова списком через запятую.
3. Не выдумывай точные характеристики, если их нет в названии товара.
4. Не используй Markdown-таблицы.
5. Верни результат строго в формате:
🔥 Продающее описание
<текст описания>

🔎 SEO-ключевые слова
<ключевые слова через запятую>
""".strip()

        try:
            # The Responses API returns the generated text in output_text.
            response = await self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "Ты опытный копирайтер для маркетплейсов Wildberries и Ozon. "
                            "Пиши убедительно, конкретно и без недостоверных обещаний."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_output_tokens=700,
            )
        except OpenAIError as exc:
            logger.exception("OpenAI API error")
            raise AIServiceError("Не удалось получить ответ от AI-сервиса.") from exc
        except Exception as exc:
            logger.exception("Unexpected AI generation error")
            raise AIServiceError("Произошла непредвиденная ошибка генерации.") from exc

        text = (response.output_text or "").strip()
        if not text:
            logger.error("OpenAI returned an empty response")
            raise AIServiceError("AI-сервис вернул пустой ответ.")

        return text
