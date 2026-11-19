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

def force_sub_keyboard(channel_data: Any) -> InlineKeyboardMarkup:
    """Majburiy obuna tugmalari (bitta yoki bir nechta kanal uchun)"""
    from bot.middlewares.subscription import parse_channels

    channels = parse_channels(channel_data)

    inline_keyboard = []

    if len(channels) == 1:
        ch = channels[0]
        url = ch.get("url") or f"https://t.me/{str(ch.get('chat_id', '')).lstrip('@')}"
        inline_keyboard.append([
            InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=url)
        ])
    elif len(channels) > 1:
        for idx, ch in enumerate(channels, 1):
            url = ch.get("url") or f"https://t.me/{str(ch.get('chat_id', '')).lstrip('@')}"
            inline_keyboard.append([
                InlineKeyboardButton(text=f"📢 {idx}-Kanalga a'zo bo'lish", url=url)
            ])
    else:
        inline_keyboard.append([
            InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url="https://t.me/")
        ])

    inline_keyboard.append([
        InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Admin boshqaruv paneli menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stat"),
                InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="💬 Yozishmalar va Hisobot", callback_data="admin_chats"),
                InlineKeyboardButton(text="📝 AI Prompt boshqaruvi", callback_data="admin_prompts")
            ],
            [
                InlineKeyboardButton(text="💳 Rekvizitni o'zgartirish", callback_data="admin_requisites"),
                InlineKeyboardButton(text="📢 Majburiy obuna kanali", callback_data="admin_channel")
            ]
        ]
    )

def admin_chats_keyboard(users: list, total_count: int, offset: int = 0, limit: int = 8) -> InlineKeyboardMarkup:
    """Foydalanuvchilarning suhbatlar ro'yxati tugmalari"""
    buttons = []
    for u in users:
        uid = u["user_id"]
        uname = f"@{u['username']}" if u.get("username") else str(uid)
        name = u.get("full_name") or uname
        name_short = (name[:14] + '..') if len(name) > 16 else name
        msg_count = u.get("msg_count", 0)
        btn_text = f"👤 {name_short} ({msg_count} ta)"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"admin_user_chat:{uid}:0")])

    nav_row = []
    if offset > 0:
        prev_offset = max(0, offset - limit)
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin_chats:{prev_offset}"))
    if offset + limit < total_count:
        next_offset = offset + limit
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin_chats:{next_offset}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🔍 User ID orqali qidirish", callback_data="admin_search_chat")])
    buttons.append([InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_back")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_user_chat_keyboard(user_id: int, total_msgs: int, offset: int = 0, limit: int = 10) -> InlineKeyboardMarkup:
    """Aynan bitta foydalanuvchining suhbati ichidagi tugmalar"""
    buttons = []
    nav_row = []

    # offset ko'payganda eskilariga o'tadi
    if offset + limit < total_msgs:
        next_offset = offset + limit
        nav_row.append(InlineKeyboardButton(text="⬅️ Eskiroq xabarlar", callback_data=f"admin_user_chat:{user_id}:{next_offset}"))

    if offset > 0:
        prev_offset = max(0, offset - limit)
        nav_row.append(InlineKeyboardButton(text="Yangi xabarlar ➡️", callback_data=f"admin_user_chat:{user_id}:{prev_offset}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🗑 Suhbat tarixini tozalash", callback_data=f"admin_clear_chat:{user_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Barcha suhbatlar ro'yxati", callback_data="admin_chats:0")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_prompts_keyboard() -> InlineKeyboardMarkup:
    """Admin AI Promptlar menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yangi Prompt qo'shish", callback_data="admin_prompt_add")
            ],
            [
                InlineKeyboardButton(text="📋 Qo'shimcha Promptlarni ko'rish", callback_data="admin_prompt_view")
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
