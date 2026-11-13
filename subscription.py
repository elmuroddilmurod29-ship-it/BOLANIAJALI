import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from bot.config import ADMIN_IDS
from bot.database.db import db
from bot.keyboards.inline import force_sub_keyboard

logger = logging.getLogger(__name__)

async def check_channel_subscription(bot, user_id: int, channel: str) -> bool:
    """Foydalanuvchining kanalga a'zoligini tekshiradi"""
    if not channel:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        if member.status in ("creator", "administrator", "member", "restricted"):
            return True
        return False
    except Exception as e:
        logger.warning(f"Kanal obunasini tekshirishda xatolik ({channel}): {e}")
        # Agar bot kanalda admin bo'lmasa yoki kanal topilmasa, foydalanuvchini to'xtatib qo'ymaslik
        return True

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        bot = data["bot"]
        user = data.get("event_from_user")

        if not user:
            return await handler(event, data)

        # Guruhlarga xalal bermaslik uchun faqat shaxsiy chatlarda (private) tekshiriladi
        if isinstance(event, Message) and event.chat.type != "private":
            return await handler(event, data)

        # Adminlar uchun majburiy obuna shart emas
        if user.id in ADMIN_IDS:
            return await handler(event, data)

        # Bazadagi majburiy kanalni tekshirish
        channel = await db.get_force_channel()
        if not channel:
            return await handler(event, data)

        # Agar bu obunani tekshirish callback'i bo'lsa, o'tkazamiz (handler o'zi tekshiradi)
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        is_sub = await check_channel_subscription(bot, user.id, channel)
        if not is_sub:
            warning_text = (
                "⚠️ **Botdan foydalanish uchun homiy kanalimizga a'zo bo'lishingiz shart!**\n\n"
                "Iltimos, pastdagi tugma orqali kanalga a'zo bo'ling va so'ng "
                "**'✅ Obunani tekshirish'** tugmasini bosing."
            )
            keyboard = force_sub_keyboard(channel)

            if isinstance(event, Message):
                await event.answer(warning_text, reply_markup=keyboard, parse_mode="Markdown")
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ Botdan foydalanish uchun kanalga a'zo bo'ling!", show_alert=True)
                if event.message:
                    await event.message.answer(warning_text, reply_markup=keyboard, parse_mode="Markdown")
            return

        return await handler(event, data)
