"""User-facing Telegram bot handlers."""

import logging
from contextlib import suppress

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from database.db import Database
from services.ai import AIService, AIServiceError

logger = logging.getLogger(__name__)

# The product requirement gives every Telegram user 3 free successful generations.
FREE_REQUEST_LIMIT = 3
CREATE_DESCRIPTION_BUTTON = "📝 Создать описание товара"

router = Router()


class ProductDescriptionForm(StatesGroup):
    """FSM state for waiting for a product name from the user."""

    waiting_for_product_name = State()


def main_keyboard() -> ReplyKeyboardMarkup:
    """Build the main reply keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CREATE_DESCRIPTION_BUTTON)]],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


@router.message(CommandStart())
async def start_handler(message: Message, db: Database) -> None:
    """Handle /start and show a welcome message."""
    user_id = message.from_user.id
    await db.add_user(user_id)
    logger.info("User %s started the bot", user_id)

    await message.answer(
        "👋 Привет! Я помогу создать продающее описание товара для Wildberries и Ozon.\n\n"
        "🎁 У вас есть 3 бесплатных запроса.\n"
        "Нажмите кнопку ниже, чтобы начать.",
        reply_markup=main_keyboard(),
    )


@router.message(F.text == CREATE_DESCRIPTION_BUTTON)
async def create_description_handler(message: Message, state: FSMContext, db: Database) -> None:
    """Ask the user for a product name if the free limit is not exhausted."""
    user_id = message.from_user.id
    requests_count = await db.get_requests_count(user_id)

    # Stop before asking for product data when the free quota is already spent.
    if requests_count >= FREE_REQUEST_LIMIT:
        await message.answer("🚫 Лимит исчерпан")
        return

    remaining = FREE_REQUEST_LIMIT - requests_count
    await state.set_state(ProductDescriptionForm.waiting_for_product_name)
    await message.answer(
        "✍️ Введите название товара.\n"
        f"Например: «Женский хлопковый костюм»\n\n"
        f"Осталось бесплатных запросов: {remaining}"
    )


@router.message(ProductDescriptionForm.waiting_for_product_name)
async def product_name_handler(message: Message, state: FSMContext, db: Database, ai_service: AIService) -> None:
    """Generate and send a marketplace description for the entered product."""
    user_id = message.from_user.id
    product_name = (message.text or "").strip()

    if not product_name:
        await message.answer("⚠️ Пожалуйста, отправьте название товара текстом.")
        return

    requests_count = await db.get_requests_count(user_id)
    if requests_count >= FREE_REQUEST_LIMIT:
        await state.clear()
        await message.answer("🚫 Лимит исчерпан", reply_markup=main_keyboard())
        return

    processing_message = await message.answer("⏳ Генерирую описание, пожалуйста подождите...")

    try:
        # Count only successful generations, so provider failures do not burn quota.
        generated_text = await ai_service.generate_product_description(product_name)
    except AIServiceError as exc:
        logger.warning("AI generation failed for user %s: %s", user_id, exc)
        with suppress(TelegramBadRequest):
            await processing_message.delete()
        await message.answer(
            "😔 Не удалось сгенерировать описание. Попробуйте ещё раз позже.",
            reply_markup=main_keyboard(),
        )
        return
    except Exception:
        logger.exception("Unhandled error while processing user %s", user_id)
        with suppress(TelegramBadRequest):
            await processing_message.delete()
        await message.answer(
            "⚠️ Произошла ошибка. Попробуйте ещё раз.",
            reply_markup=main_keyboard(),
        )
        return

    new_count = await db.increment_requests_count(user_id)
    remaining = max(FREE_REQUEST_LIMIT - new_count, 0)
    await state.clear()
    with suppress(TelegramBadRequest):
        await processing_message.delete()

    await message.answer(
        "✅ Готово!\n\n"
        f"🏷 Товар: {product_name}\n\n"
        f"{generated_text}\n\n"
        f"🎁 Осталось бесплатных запросов: {remaining}",
        reply_markup=main_keyboard(),
    )


@router.message()
async def fallback_handler(message: Message) -> None:
    """Handle unknown messages and guide the user to the main action."""
    await message.answer(
        "Нажмите кнопку «Создать описание товара», чтобы начать генерацию. 👇",
        reply_markup=main_keyboard(),
    )
