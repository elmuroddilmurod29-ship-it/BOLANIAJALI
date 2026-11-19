from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    chatting = State()              # AI bilan bevosita suhbatlashish holati
    waiting_payment_check = State() # To'lov chekini (rasm/skrinshot) kutish holati

class AdminStates(StatesGroup):
    waiting_broadcast_message = State() # Barcha foydalanuvchilarga xabar yuborish
    waiting_card_number = State()       # Yangi karta raqamini kiritish
    waiting_card_holder = State()       # Yangi karta egasi ismini kiritish
    waiting_extra_prompt = State()      # Yangi qo'shimcha prompt matnini kiritish
    waiting_channel = State()           # Majburiy obuna kanalini kiritish
    waiting_chat_search = State()       # Foydalanuvchi ID yoki username bo'yicha suhbat qidirish
