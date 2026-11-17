import logging
import re
from typing import Callable, Dict, Any, Awaitable, List, Tuple
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from bot.config import ADMIN_IDS
from bot.database.db import db
from bot.keyboards.inline import force_sub_keyboard

logger = logging.getLogger(__name__)

def parse_channels(raw_channels: Any) -> List[Dict[str, Any]]:
    """
    Kanal matnini tahlil qiladi va har bir kanal uchun chat_id, url va nom qaytaradi.
    Qo'llab-quvvatlanadigan formatlar:
    - @kanal_nomi
    - https://t.me/kanal_nomi yoki t.me/kanal_nomi
    - kanal_nomi (avtomatik @ qo'shiladi)
    - -1001234567890 (ID)
    - vergul, yangi qator yoki probel bilan ajratilgan bir nechta kanallar
    """
    if not raw_channels:
        return []

    # Agar allaqachon list bo'lsa
    if isinstance(raw_channels, list):
        parsed_list = []
        for item in raw_channels:
            if isinstance(item, dict):
                parsed_list.append(item)
            elif isinstance(item, str):
                parsed_list.extend(parse_channels(item))
        return parsed_list

    raw_str = str(raw_channels).strip()
    if not raw_str or raw_str.lower() in ("none", "off", "yoq", "ochir", "0"):
        return []

    # Vergul yoki yangi qator bo'yicha ajratamiz
    tokens = re.split(r'[\n,]+', raw_str)
    channels = []

    for token in tokens:
        item = token.strip()
        if not item or item.lower() in ("none", "off", "yoq", "ochir", "0"):
            continue

        # Maxsus format: chat_id|invite_url
        if "|" in item:
            parts = item.split("|", 1)
            cid = parts[0].strip()
            curl = parts[1].strip()
            channels.append({
                "chat_id": int(cid) if cid.lstrip("-").isdigit() else cid,
                "url": curl,
                "display": cid
            })
            continue

        # URL format: https://t.me/... yoki t.me/...
        clean_url = re.sub(r'^https?://', '', item).strip()
        if clean_url.startswith("t.me/"):
            slug = clean_url[5:].strip().rstrip('/')
            if slug.startswith("+") or slug.startswith("joinchat/"):
                channels.append({
                    "chat_id": item,
                    "url": f"https://t.me/{slug}",
                    "display": f"https://t.me/{slug}"
                })
            else:
                uname = slug.lstrip('@')
                channels.append({
                    "chat_id": f"@{uname}",
                    "url": f"https://t.me/{uname}",
                    "display": f"@{uname}"
                })
            continue

        # Raqamli Telegram Chat ID (-100...)
        if item.startswith("-") and item[1:].isdigit():
            channels.append({
                "chat_id": int(item),
                "url": f"https://t.me/c/{item[4:]}/1" if item.startswith("-100") else f"https://t.me/",
                "display": item
            })
            continue

        # Oddiy username
        uname = item.lstrip('@')
        channels.append({
            "chat_id": f"@{uname}",
            "url": f"https://t.me/{uname}",
            "display": f"@{uname}"
        })

    return channels

async def check_channel_subscription(bot, user_id: int, chat_id: Any) -> bool:
    """Bitta kanal bo'yicha a'zolikni tekshiradi"""
    if not chat_id:
        return True
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member.status in ("creator", "administrator", "member", "restricted"):
            return True
        return False
    except Exception as e:
        err_msg = str(e).lower()
        # Agar user kanalda bo'lmasa, Telegram shunday xatolik beradi
        if "user not found" in err_msg or "participant" in err_msg or "member list is inaccessible" in err_msg:
            return False

        # Agar kanal mavjud bo'lmasa yoki bot admin bo'lmasa
        logger.warning(f"Kanal obunasini tekshirishda xatolik ({chat_id}): {e}")
        # Bot admin bo'lmaganda False qaytaramiz (admin panelda bu haqida ogohlantiriladi)
        return False

async def check_all_subscriptions(bot, user_id: int, channels_raw: Any) -> Tuple[bool, List[Dict[str, Any]]]:
    """Barcha majburiy kanallarga a'zolikni tekshiradi. (barchasi_azo, azo_bolmagan_kanallar) qaytaradi"""
    parsed = parse_channels(channels_raw)
    if not parsed:
        return True, []

    missing = []
    for ch in parsed:
        chat_id = ch["chat_id"]
        is_sub = await check_channel_subscription(bot, user_id, chat_id)
        if not is_sub:
            missing.append(ch)

    return (len(missing) == 0), missing

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

        # Adminlar uchun majburiy obuna to'siq bo'lmaydi (admin panelda 'Obunani sinab ko'rish' tugmasi bor)
        if user.id in ADMIN_IDS:
            return await handler(event, data)

        # Bazadagi majburiy kanallarni tekshirish
        channels_raw = await db.get_force_channel()
        if not channels_raw:
            return await handler(event, data)

        # Agar bu obunani tekshirish callback'i bo'lsa, o'tkazamiz (handler o'zi tekshiradi)
        if isinstance(event, CallbackQuery) and event.data in ("check_subscription", "admin_channel_test"):
            return await handler(event, data)

        is_all_sub, missing = await check_all_subscriptions(bot, user.id, channels_raw)
        if not is_all_sub:
            keyboard = force_sub_keyboard(missing if missing else channels_raw)

            bullets = "\n".join([f"• <b>{ch.get('display', 'Kanal')}</b>" for ch in missing])
            warning_text = (
                "⚠️ <b>Botdan foydalanish uchun homiy kanalimizga a'zo bo'lishingiz shart!</b>\n\n"
                f"{bullets}\n\n"
                "Iltimos, yuqoridagi kanal(lar)ga a'zo bo'ling va so'ng "
                "<b>'✅ Obunani tekshirish'</b> tugmasini bosing."
            )

            if isinstance(event, Message):
                await event.answer(warning_text, reply_markup=keyboard, parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ Botdan foydalanish uchun kanallarga a'zo bo'ling!", show_alert=True)
                if event.message:
                    await event.message.answer(warning_text, reply_markup=keyboard, parse_mode="HTML")
            return

        return await handler(event, data)
