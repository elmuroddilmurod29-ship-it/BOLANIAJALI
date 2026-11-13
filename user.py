import logging
from pathlib import Path
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from bot.database.db import db, get_now
from bot.services.ai_service import ai_service
from bot.states.user_states import UserStates
from bot.keyboards.reply import main_menu_keyboard, chat_mode_keyboard
from bot.keyboards.inline import character_keyboard, force_sub_keyboard
from bot.middlewares.subscription import check_channel_subscription

logger = logging.getLogger(__name__)

router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
AMINA_ASSETS_DIR = BASE_DIR / "bot" / "assets" / "amina"

CAT_PHOTO_PATH = AMINA_ASSETS_DIR / "cat.jpg"
PHOTO_1_PATH = AMINA_ASSETS_DIR / "photo1.jpg"
PHOTO_2_PATH = AMINA_ASSETS_DIR / "photo2.jpg"

def is_asking_for_cat_photo(text: str) -> bool:
    t = text.lower()
    cat_words = ["mushuk", "mushug", "mushugi", "mushugiz", "mushuging", "kot", "kiska"]
    ask_words = ["rasm", "surat", "foto", "korsat", "ko'rsat", "tashla", "yubor", "ber", "bormi"]
    has_cat = any(w in t for w in cat_words)
    has_ask = any(w in t for w in ask_words) or ("mushuk" in t and "qani" in t)
    return has_cat and (has_ask or "rasm" in t or "ko'rsat" in t or "korsat" in t)

def is_asking_for_personal_photo(text: str) -> bool:
    t = text.lower()
    if any(w in t for w in ["mushuk", "mushug", "kot"]):
        return False

    if any(phrase in t for phrase in ["boshqasi", "boshqasini", "yana bitta rasm", "boshqa rasm"]):
        return True

    photo_words = ["rasm", "surat", "foto", "rasmiz", "rasming", "rasmizi", "rasmingni", "ozingni", "o'zingni", "suratiz"]
    ask_words = ["tashla", "yubor", "korsat", "ko'rsat", "ber", "bormi", "yana", "koray", "ko'ray"]

    has_photo = any(w in t for w in photo_words)
    has_ask = any(w in t for w in ask_words)
    return has_photo and has_ask

CHARACTER_NAMES = {
    "female": "👩 Amina (Qiz bola AI)",
    "male": "👨 Shohrux (O'g'il bola AI)"
}

PLAN_NAMES = {
    "free": "Tekin (Free) 🆓",
    "standard": "Standart 🥈",
    "premium": "Premium 👑 (Cheksiz)"
}

@router.message(CommandStart())
async def handle_start(message: types.Message, state: FSMContext):
    """/start komandasi - Ro'yxatdan o'tkazish va asosiy menyuni chiqarish"""
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    user = await db.get_or_create_user(user_id, username, full_name)
    char_name = CHARACTER_NAMES.get(user.get("character", "female"), "👩 Qiz bola AI")

    welcome_text = (
        f"Assalomu alaykum, **{full_name}**! Xush kelibsiz 👋\n\n"
        f"🤖 Men sun'iy intellekt asosida ishlovchi aqlli yordamchingizman.\n"
        f"🎭 Hozirgi tanlangan personaj: **{char_name}**\n\n"
        f"Quyidagi menyudan kerakli bo'limni tanlang:"
    )

    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "check_subscription")
async def handle_check_subscription(callback: types.CallbackQuery, state: FSMContext):
    """Majburiy obunani qayta tekshirish tugmasi"""
    channel = await db.get_force_channel()
    is_sub = await check_channel_subscription(callback.bot, callback.from_user.id, channel)

    if is_sub:
        await callback.answer("✅ Obuna tasdiqlandi! Rahmat.", show_alert=True)
        user = await db.get_or_create_user(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.full_name
        )
        await callback.message.delete()
        await callback.message.answer(
            "🎉 Obuna muvaffaqiyatli tekshirildi! Marhamat, botdan to'liq foydalanishingiz mumkin:",
            reply_markup=main_menu_keyboard()
        )
    else:
        await callback.answer("❌ Siz hali ham kanalga a'zo bo'lmadingiz. Iltimos, avval a'zo bo'ling!", show_alert=True)

@router.message(F.text == "🔙 Asosiy menyu")
@router.message(F.text == "❌ Bekor qilish")
async def handle_back_to_menu(message: types.Message, state: FSMContext):
    """Asosiy menyuga qaytish"""
    await state.clear()
    await message.answer(
        "Asosiy menyudasiz. Kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard()
    )

@router.message(F.text == "🗣 Suhbatlashish")
async def handle_start_chat(message: types.Message, state: FSMContext):
    """AI bilan suhbat rejimini yoqish"""
    if message.chat.type != "private":
        await message.reply("⚠️ AI faqat bot bilan shaxsiy muloqotda (lichkada) ishlaydi.")
        return

    user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    char_name = CHARACTER_NAMES.get(user.get("character", "female"), "👩 Qiz bola AI")

    await state.set_state(UserStates.chatting)

    text = (
        f"🗣 **Suhbat rejimi yoqildi!**\n\n"
        f"🎭 Suhbatdosh: **{char_name}**\n"
        f"💡 Menga istalgan savol, mavzu yoki topshiriq yozishingiz mumkin. "
        f"Muloqotimiz to'liq maxfiy va faqat siz uchun izolyatsiya qilingan.\n\n"
        f"Suhbatni to'xtatish uchun pastdagi **'🔙 Asosiy menyu'** tugmasini bosing."
    )
    await message.answer(text, reply_markup=chat_mode_keyboard(), parse_mode="Markdown")

@router.message(F.text == "🎭 Personajni tanlash")
async def handle_choose_character(message: types.Message):
    """Personajni tanlash menyusi"""
    user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    current_char = user.get("character", "female")

    text = (
        "🎭 **AI Personajini tanlang:**\n\n"
        "👩 **Amina (Qiz bola AI)** — 22 yoshli toshkentlik qiz. O'ziga xos xarakter, realistik muloqot.\n"
        "👨 **Shohrux (O'g'il bola AI)** — 24 yoshli toshkentlik yigit. Mashinalar, ko'cha slengi va o'ziga ishongan xarakter.\n\n"
        "O'zingizga qulay personajni tanlang:"
    )
    await message.answer(
        text,
        reply_markup=character_keyboard(current_char),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("set_char:"))
async def handle_character_callback(callback: types.CallbackQuery):
    """Personaj o'zgarganda ishlaydi"""
    new_char = callback.data.split(":")[1]
    await db.set_character(callback.from_user.id, new_char)

    char_name = CHARACTER_NAMES.get(new_char, "AI")
    await callback.answer(f"✅ Personaj o'zgartirildi: {char_name}", show_alert=True)

    text = (
        f"🎭 **AI Personaji muvaffaqiyatli tanlandi!**\n\n"
        f"Hozirgi personaj: **{char_name}**\n\n"
        f"Endi suhbatlashish bo'limiga o'tib, yangi personaj bilan muloqot qilishingiz mumkin!"
    )
    await callback.message.edit_text(
        text,
        reply_markup=character_keyboard(new_char),
        parse_mode="Markdown"
    )

@router.message(F.text == "👤 Profilim")
async def handle_profile(message: types.Message):
    """Foydalanuvchi profili ma'lumotlari"""
    user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    user_id = user["user_id"]
    char_name = CHARACTER_NAMES.get(user.get("character", "female"), "Qiz bola AI")
    plan = user.get("plan", "free")
    plan_name = PLAN_NAMES.get(plan, plan)

    daily_count = user.get("daily_messages_count", 0)
    monthly_left = user.get("monthly_messages_left", 0)
    expiry = user.get("plan_expiry")

    # Qolgan xabarlar matni
    if plan == "free":
        left = max(0, 50 - daily_count)
        quota_text = f"- Bugun ishlatilgan: {daily_count} / 50 ta\n- Qolgan bepul xabarlar: **{left} ta** (Har 24 soatda yangilanadi)"
        expiry_text = "Cheklanmagan (Tekin rejim)"
    elif plan == "standard":
        quota_text = f"- Standart tarif bo'yicha qolgan xabarlar: **{monthly_left} ta**"
        expiry_text = expiry[:16].replace("T", " ") if expiry else "30 kun"
    elif plan == "premium":
        quota_text = "- Xabarlar: **CHEKSIZ (Limitsiz 💎)**"
        expiry_text = expiry[:16].replace("T", " ") if expiry else "30 kun"
    else:
        quota_text = "Ma'lumot yo'q"
        expiry_text = "Noma'lum"

    text = (
        "👤 **Sizning Profilingiz:**\n\n"
        f"🆔 **ID raqamingiz:** `{user_id}`\n"
        f"🎭 **Tanlangan personaj:** {char_name}\n"
        f"💳 **Tarif turi:** {plan_name}\n\n"
        f"📊 **Xabarlar balansi:**\n{quota_text}\n\n"
        f"📅 **Obuna muddati:** {expiry_text}\n"
    )

    await message.answer(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

@router.message(F.text == "🗑 Suhbatni tozalash")
@router.message(Command("clear"))
async def handle_clear_chat(message: types.Message):
    """Suhbat tarixini tozalash"""
    await db.clear_chat_history(message.from_user.id)
    await message.answer(
        "🧹 **Sizning suhbat tarixingiz va xotirangiz to'liq tozalandi!**\n\n"
        "AI siz bilan yangi, toza sahifadan suhbatlashishga tayyor.",
        reply_markup=chat_mode_keyboard(),
        parse_mode="Markdown"
    )

@router.my_chat_member()
async def handle_bot_added_to_chat(event: types.ChatMemberUpdated):
    """Bot guruhga qo'shilganda salomlashish"""
    if event.new_chat_member.status in ("member", "administrator"):
        welcome = (
            "Salom hammaga! 👋 Men shu guruhdaman.\n\n"
            "Menga savolingiz bo'lsa yoki shunchaki gaplashmoqchi bo'lsangiz:\n"
            "• Xabarimga **Reply** qilib yozing\n"
            "• Yoki ismimni ayting (**Amina** yoki **Shohrux**)!\n\n"
            "Marhamat, bemalol gaplashishingiz mumkin 😊"
        )
        try:
            await event.bot.send_message(chat_id=event.chat.id, text=welcome)
        except Exception as e:
            logger.warning(f"Guruhga salom xabari yuborishda xatolik: {e}")

@router.message(F.text & ~F.text.startswith("/"))
async def handle_ai_chat_message(message: types.Message, state: FSMContext):
    """AI bilan xabarlashish xizmati (Lichkada va Guruhlarga qo'shilganda)"""
    # Maxsus menyu tugmalarini ushlab qolmaslik
    if message.text in [
        "🗣 Suhbatlashish", "🎭 Personajni tanlash", "💳 Tariflar va To'lov",
        "👤 Profilim", "🔙 Asosiy menyu", "🗑 Suhbatni tozalash", "❌ Bekor qilish"
    ]:
        return

    is_private = message.chat.type == "private"
    is_group = message.chat.type in ("group", "supergroup")

    user_id = message.from_user.id
    user = await db.get_or_create_user(user_id, message.from_user.username, message.from_user.full_name)
    character = user.get("character", "female")

    clean_text = message.text.strip()
    session_id = None

    if is_group:
        # Guruhda bot qachon javob beradi:
        # 1. Bot xabariga reply qilinganda
        # 2. Bot username'i tilga olinganda (@bot)
        # 3. Personaj ismi aytilganda (Amina yoki Shohrux)
        bot_user = await message.bot.get_me()
        bot_username = (bot_user.username or "").lower()
        bot_mention = f"@{bot_username}"

        text_lower = clean_text.lower()
        is_reply_to_bot = bool(
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.id == bot_user.id
        )
        is_mentioned = bool(bot_username and bot_mention in text_lower)
        is_shohrux = "shohrux" in text_lower
        is_amina = "amina" in text_lower

        # Agar botga hech qanday murojaat bo'lmasa, guruh a'zolarining o'zaro gapiga aralashmaydi
        if not (is_reply_to_bot or is_mentioned or is_shohrux or is_amina):
            return

        # Guruhda personajni aniqlash
        if is_shohrux:
            character = "male"
        elif is_amina:
            character = "female"

        # Matndan @bot_username ni tozalash
        if bot_mention in text_lower:
            clean_text = clean_text.replace(bot_mention, "").replace(f"@{bot_user.username}", "").strip()

        # Guruh chat xotirasi (barcha a'zolar uchun umumiy chat_id xotirasi)
        session_id = message.chat.id
        user_message_formatted = f"[{message.from_user.full_name}]: {clean_text}"
    else:
        # Shaxsiy lichkada
        session_id = user_id
        user_message_formatted = clean_text

    # 1. Kvotani tekshirish va yechish
    allowed, reason, remaining = await db.check_and_deduct_quota(user_id)

    if not allowed:
        if is_group:
            await message.reply(
                "⚠️ Sizning xabarlar limitingiz tugagan. Ertaga yana gaplashamiz yoki bot lichkasida tarif xarid qiling!"
            )
            return

        if reason == "free_limit_reached":
            limit_msg = (
                "⚠️ **Bugungi bepul limitingiz tugadi!**\n\n"
                "Tekin tarifda kuniga 50 ta xabar beriladi. Yangi xabarlar 24 soatdan so'ng ochiladi.\n\n"
                "Cheksiz yoki kengaytirilgan imkoniyatlardan foydalanish uchun "
                "**'💳 Tariflar va To'lov'** bo'limidan Standart yoki Premium obunani xarid qilishingiz mumkin!"
            )
        elif reason == "monthly_limit_reached":
            limit_msg = (
                "⚠️ **Standart tarifingizdagi xabarlar (3,000 ta) tugadi!**\n\n"
                "Suhbatni davom ettirish uchun **'💳 Tariflar va To'lov'** bo'limidan yangi tarif xarid qilishingiz mumkin."
            )
        else:
            limit_msg = (
                "⚠️ Xabarlar limitingiz tugagan. Iltimos, yangi tarif xarid qiling!"
            )

        await message.answer(limit_msg, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        await state.clear()
        return

    # 2. Amina uchun Rasm so'rash mantiqi (Personal va Mushuk rasmi)
    if character == "female":
        # A) Mushuk rasmi so'ralganda
        if is_asking_for_cat_photo(clean_text) and CAT_PHOTO_PATH.exists():
            await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
            cat_caption = "mana mening qora mushugim 🐈‍⬛ qora mushuklarni yaxshi ko'raman 😊"
            photo = FSInputFile(str(CAT_PHOTO_PATH))
            if is_group:
                await message.reply_photo(photo=photo, caption=cat_caption)
            else:
                await message.answer_photo(photo=photo, caption=cat_caption)

            await db.increment_user_photo(user_id, photo_type="cat")
            await db.add_message(user_id=session_id, role="user", content=user_message_formatted)
            await db.add_message(user_id=session_id, role="model", content=f"[Qora mushugi bilan tushgan rasmini yubordi]: {cat_caption}")
            return

        # B) Aminaning o'z shaxsiy rasmi so'ralganda
        if is_asking_for_personal_photo(clean_text):
            photo_stats = await db.get_user_photo_stats(user_id)
            personal_count = photo_stats.get("personal_photos_sent", 0)

            # 2 martadan keyin rad etish
            if personal_count >= 2:
                refusal_text = "bo'ladi boshqa yubormayman 😒 rasm albomi emas bu yer 🙄"
                if is_group:
                    await message.reply(refusal_text)
                else:
                    await message.answer(refusal_text)

                await db.add_message(user_id=session_id, role="user", content=user_message_formatted)
                await db.add_message(user_id=session_id, role="model", content=refusal_text)
                return

            # 1-rasm (ko'chada plashda)
            elif personal_count == 0 and PHOTO_1_PATH.exists():
                await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
                caption = "bu mening rasmim 😊"
                photo = FSInputFile(str(PHOTO_1_PATH))
                if is_group:
                    await message.reply_photo(photo=photo, caption=caption)
                else:
                    await message.answer_photo(photo=photo, caption=caption)

                await db.increment_user_photo(user_id, photo_type="personal", next_idx=1)
                await db.add_message(user_id=session_id, role="user", content=user_message_formatted)
                await db.add_message(user_id=session_id, role="model", content=f"[O'zining rasmini yubordi]: {caption}")
                return

            # 2-rasm (kafeda qahva bilan)
            elif personal_count == 1 and PHOTO_2_PATH.exists():
                await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
                caption = "bu boshqasi, lekin bo'ldi boshqa so'ramang 🙈"
                photo = FSInputFile(str(PHOTO_2_PATH))
                if is_group:
                    await message.reply_photo(photo=photo, caption=caption)
                else:
                    await message.answer_photo(photo=photo, caption=caption)

                await db.increment_user_photo(user_id, photo_type="personal", next_idx=2)
                await db.add_message(user_id=session_id, role="user", content=user_message_formatted)
                await db.add_message(user_id=session_id, role="model", content=f"[O'zining 2-rasmini yubordi]: {caption}")
                return

    # 3. Telegramda 'typing' animatsiyasini chiqarish
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # 4. AI ga xavfsiz so'rov yuborish
    ai_response = await ai_service.generate_response(
        user_id=user_id,
        user_message=user_message_formatted,
        character=character,
        session_id=session_id
    )

    # 4. Javobni foydalanuvchiga yuborish (Telegram 4096 belgi chegarasini hisobga olgan holda)
    chunks = [ai_response[i:i+4000] for i in range(0, len(ai_response), 4000)] if len(ai_response) > 4000 else [ai_response]
    for chunk in chunks:
        if is_group:
            await message.reply(chunk)
        else:
            await message.answer(chunk)
