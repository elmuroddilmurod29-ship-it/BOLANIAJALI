from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy foydalanuvchi menyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🗣 Suhbatlashish"),
                KeyboardButton(text="🎭 Personajni tanlash"),
            ],
            [
                KeyboardButton(text="💳 Tariflar va To'lov"),
                KeyboardButton(text="👤 Profilim"),
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

def chat_mode_keyboard() -> ReplyKeyboardMarkup:
    """Suhbat rejimida chiqadigan qulay boshqaruv tugmalari"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🗑 Suhbatni tozalash"),
                KeyboardButton(text="🔙 Asosiy menyu"),
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Amalni bekor qilish tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
