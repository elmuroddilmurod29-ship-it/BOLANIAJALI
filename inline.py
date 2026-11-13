from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

def character_keyboard(current_character: str = "female") -> InlineKeyboardMarkup:
    """Personaj tanlash tugmalari"""
    female_mark = " (Hozirgi)" if current_character == "female" else ""
    male_mark = " (Hozirgi)" if current_character == "male" else ""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"👩 Amina AI (Qiz bola){female_mark}",
                    callback_data="set_char:female"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"👨 Shohrux AI (O'g'il bola){male_mark}",
                    callback_data="set_char:male"
                )
            ]
        ]
    )

def plans_keyboard() -> InlineKeyboardMarkup:
    """Tariflar ro'yxati tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🥈 Standart — 20,000 so'm (3,000 xabar)",
                    callback_data="buy_plan:standard"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👑 Premium — 50,000 so'm (Cheksiz 💎)",
                    callback_data="buy_plan:premium"
                )
            ]
        ]
    )

def cancel_payment_keyboard() -> InlineKeyboardMarkup:
    """To'lov jarayonini bekor qilish tugmasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ To'lovni bekor qilish",
                    callback_data="cancel_payment"
                )
            ]
        ]
    )

def payment_verify_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    """Admin uchun to'lov chekini tasdiqlash yoki rad etish tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"pay_approve:{payment_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"pay_reject:{payment_id}"
                )
            ]
        ]
    )

def force_sub_keyboard(channel: str) -> InlineKeyboardMarkup:
    """Majburiy obuna tugmasi"""
    # Agar kanal @ bilan boshlansa t.me link yasaymiz
    if channel.startswith("@"):
        url = f"https://t.me/{channel.lstrip('@')}"
    elif channel.startswith("https://"):
        url = channel
    else:
        url = f"https://t.me/{channel}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=url)
            ],
            [
                InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")
            ]
        ]
    )

def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Admin boshqaruv paneli menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stat"),
                InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="💳 Rekvizitni o'zgartirish", callback_data="admin_requisites"),
                InlineKeyboardButton(text="📝 AI Prompt boshqaruvi", callback_data="admin_prompts")
            ],
            [
                InlineKeyboardButton(text="📢 Majburiy obuna kanali", callback_data="admin_channel")
            ]
        ]
    )

def admin_prompts_keyboard() -> InlineKeyboardMarkup:
    """Admin AI Promptlar menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yangi Prompt qo'shish", callback_data="admin_prompt_add")
            ],
            [
                InlineKeyboardButton(text="📋 Barcha Promptlarni ko'rish", callback_data="admin_prompt_view")
            ],
            [
                InlineKeyboardButton(text="🗑 Qo'shimcha promptlarni tozalash", callback_data="admin_prompt_clear_confirm")
            ],
            [
                InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_back")
            ]
        ]
    )

def confirm_clear_prompts_keyboard() -> InlineKeyboardMarkup:
    """Extra promptlarni tozalashni tasdiqlash"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚠️ Ha, tozalansin", callback_data="admin_prompt_clear_yes"),
                InlineKeyboardButton(text="❌ Yo'q, bekor qilish", callback_data="admin_prompts")
            ]
        ]
    )
