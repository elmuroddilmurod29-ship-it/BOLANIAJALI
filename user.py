import asyncio
import html
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from bot.config import ADMIN_IDS
from bot.database.db import db, get_now
from bot.services.ai_service import ai_service
from bot.services.moderation import detect_intimate_content
from bot.states.user_states import UserStates
from bot.keyboards.reply import main_menu_keyboard, chat_mode_keyboard
from bot.keyboards.inline import character_keyboard, force_sub_keyboard
from bot.middlewares.subscription import check_channel_subscription, check_all_subscriptions

logger = logging.getLogger(__name__)

router = Router()

def get_amina_asset(filename: str) -> Optional[Path]:
    """Asset faylini har qanday muhitda (Render, Linux, Windows) ishonchli topadi"""
    base_dir = Path(__file__).resolve().parent.parent.parent
    candidates = [
        base_dir / "bot" / "assets" / "amina" / filename,
        base_dir / "assets" / "amina" / filename,
        Path.cwd() / "bot" / "assets" / "amina" / filename,
        Path.cwd() / "assets" / "amina" / filename,
        Path(__file__).resolve().parent.parent / "assets" / "amina" / filename,
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None

PERSONAL_PHOTOS = [
    ("photo1.jpg", "bu mening rasmim 😊"),
    ("photo2.jpg", "bu boshqasi, o'zimga yoqqan rasmlarimdan biri 🙈"),
    ("photo3.jpg", "yana bittasi, dugonam tushirib bergandi 😊"),
    ("photo4.jpg", "mana eng oxirgisi, bo'ldi endi ko'p so'ramang 🙈"),
]

def is_asking_for_cat_photo(text: str) -> bool:
    t = text.lower().strip()
    cat_words = ["mushuk", "mushug", "mushugi", "mushugiz", "mushuging", "kot", "kiska"]
    ask_words = [
        "rasm", "surat", "foto", "korsat", "ko'rsat", "tashla", "tawla", "yubor", "jonat", "jo'nat",
        "ber", "bormi", "bomi", "qani", "koray", "ko'ray", "kore", "ko're", "tashavor", "jonatvor", "jo'natvor"
    ]
    has_cat = any(w in t for w in cat_words)
    has_ask = any(w in t for w in ask_words) or ("mushuk" in t and "qani" in t)
    return has_cat and (has_ask or "rasm" in t)

def is_asking_for_personal_photo(text: str) -> bool:
    t = text.lower().strip()
    if any(w in t for w in ["mushuk", "mushug", "kot", "kiska"]):
        return False

    # 1. To'g'ridan-to'g'ri bir yoki ikki so'zli aniq so'rovlar
    exact_triggers = [
        "rasm", "rasming", "rasmiz", "rasmingiz", "surat", "surating", "suratiz",
        "foto", "fota", "fotang", "rasm qani", "rasming qani", "rasmiz qani",
        "rasm bormi", "rasming bormi", "surat bormi", "foto bormi", "rasm tashla",
        "rasm yubor", "rasm jonat", "rasm jo'nat"
    ]
    if t in exact_triggers:
        return True

    # 2. Yana bitta rasm so'rash
    if any(phrase in t for phrase in [
        "boshqasi", "boshqasini", "yana bitta", "yana rasm", "boshqa rasm",
        "yana tashla", "yana bittasini", "yana bittasi", "yana yubor", "yana jonat", "yana jo'nat"
    ]):
        return True

    # 3. Rasmga tegishli so'zlar
    photo_words = [
        "rasm", "surat", "foto", "fota", "rasmiz", "rasming", "rasmizi", "rasmingni",
        "ozingni", "o'zingni", "suratiz", "surating", "suratingiz", "yuzing", "yuzingni",
        "ko'rinishing", "korinishing", "turqing", "chehrang"
    ]

    ask_words = [
        "tashla", "tawla", "tasla", "tashavor", "tashavol", "tashlasang", "tashab",
        "yubor", "yuboring", "yuborchi", "yuborvor", "yuborsang",
        "jonat", "jo'nat", "jonatvor", "jo'natvor", "jonating", "jo'nating", "jonatgin", "jo'natgin",
        "korsat", "ko'rsat", "korsating", "ko'rsating", "korsatvor", "ko'rsatvor",
        "ber", "bering", "bervor", "bersang",
        "bormi", "bomi", "qani", "qanisan", "bormikan",
        "koray", "ko'ray", "kore", "ko're", "koraylik", "ko'raylik", "kormoqchiman", "ko'rmoqchiman", "kuraylik"
    ]

    has_photo = any(w in t for w in photo_words)
    has_ask = any(w in t for w in ask_words)

    # Agar "o'zingni ko'rsat" desa (rasm so'zi bo'lmasa ham)
    if any(w in t for w in ["ozingni", "o'zingni", "yuzingni", "ko'rinishingni"]) and any(
        w in t for w in ["korsat", "ko'rsat", "koray", "ko'ray", "tashla", "yubor", "jonat", "jo'nat"]
    ):
        return True

    return has_photo and has_ask

async def send_admin_intimate_alert(bot, user: dict, user_message: str, character: str, trigger_word: str):
    """Adminlarga 18+ yoki ehtirosli xabar kelganda avtomatik ogohlantirish yuborish"""
    char_name = "Amina AI (Qiz bola)" if character == "female" else "Shohrux AI (O'g'il bola)"
    uname = f"@{user.get('username')}" if user.get('username') else "username yo'q"
    now_str = get_now()
    uid = user.get("user_id")

    alert_text = (
        "🚨 <b>DIQQAT: EHTIROSLI / 18+ XABAR ANIQLANDI!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> <b>{html.escape(user.get('full_name', 'Nomaʼlum'))}</b> ({uname})\n"
        f"🆔 <b>User ID:</b> <code>{uid}</code>\n"
        f"🎭 <b>Suhbatdoshi:</b> {char_name}\n"
        f"⏰ <b>Vaqt:</b> {now_str}\n"
        f"🔍 <b>Kalit so'z:</b> <code>{html.escape(trigger_word)}</code>\n\n"
        f"💬 <b>Foydalanuvchi yozgan xabar:</b>\n"
        f"<i>\"{html.escape(user_message)}\"</i>"
    )

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="👁 Ushbu suhbatni ko'rish",
                    callback_data=f"admin_user_chat:{uid}:0"
                )
            ]
        ]
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=alert_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Adminga ehtirosli xabar bildirishnomasini yuborishda xatolik ({admin_id}): {e}")

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
    channels_raw = await db.get_force_channel()
    if not channels_raw:
        await callback.answer("✅ Majburiy obuna o'chirilgan!", show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "🎉 Marhamat, botdan to'liq foydalanishingiz mumkin:",
            reply_markup=main_menu_keyboard()
        )
        return

    is_sub, missing = await check_all_subscriptions(callback.bot, callback.from_user.id, channels_raw)

    if is_sub:
        await callback.answer("✅ Obuna tasdiqlandi! Rahmat.", show_alert=True)
        user = await db.get_or_create_user(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.full_name
        )
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "🎉 <b>Obuna muvaffaqiyatli tekshirildi!</b>\n\nMarhamat, botdan to'liq foydalanishingiz mumkin:",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        missing_names = ", ".join([ch.get("display", "kanal") for ch in missing])
        await callback.answer(
            f"❌ Siz hali barcha homiy kanallarga a'zo bo'lmadingiz!\nQuyidagilarga a'zo bo'ling: {missing_names}",
            show_alert=True
        )

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
        if is_asking_for_cat_photo(clean_text):
            cat_path = get_amina_asset("cat.jpg")
            if cat_path and cat_path.exists():
                await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
                cat_caption = "mana mening qora mushugim 🐈‍⬛ qora mushuklarni yaxshi ko'raman 😊"
                photo = FSInputFile(str(cat_path))
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

            # Bizda 4 ta rasm bor: photo1.jpg, photo2.jpg, photo3.jpg, photo4.jpg
            # Har safar yangisini yuboradi, 4 tadan oshganda ham aylanma (cycle) qilib chiroyli javob bilan yuboradi
            photo_idx = personal_count % len(PERSONAL_PHOTOS)
            filename, default_caption = PERSONAL_PHOTOS[photo_idx]
            photo_path = get_amina_asset(filename)

            if photo_path and photo_path.exists():
                await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
                if personal_count >= len(PERSONAL_PHOTOS):
                    caption = "mayli yana bitta rasmimni yuboraman 😊 lekin ko'p so'ramang 🙈"
                else:
                    caption = default_caption

                photo = FSInputFile(str(photo_path))
                if is_group:
                    await message.reply_photo(photo=photo, caption=caption)
                else:
                    await message.answer_photo(photo=photo, caption=caption)

                await db.increment_user_photo(user_id, photo_type="personal", next_idx=(personal_count + 1))
                await db.add_message(user_id=session_id, role="user", content=user_message_formatted)
                await db.add_message(user_id=session_id, role="model", content=f"[Rasmini yubordi]: {caption}")
                return
            else:
                logger.warning(f"Amina photo file not found: {filename}")
                no_photo_text = "hozir rasmim yo'q edi telefonimda keyinroq yuboraman 😊"
                if is_group:
                    await message.reply(no_photo_text)
                else:
                    await message.answer(no_photo_text)
                await db.add_message(user_id=session_id, role="user", content=user_message_formatted)
                await db.add_message(user_id=session_id, role="model", content=no_photo_text)
                return

    # Shohrux (male) uchun rasm so'ralganda
    elif character == "male":
        if is_asking_for_personal_photo(clean_text) or is_asking_for_cat_photo(clean_text):
            shohrux_reply = "e rasmga tushishni yoqtirmayman bilasanu 😒 rulda edim ko'rishganda o'zimni ko'rasan"
            if is_group:
                await message.reply(shohrux_reply)
            else:
                await message.answer(shohrux_reply)
            await db.add_message(user_id=session_id, role="user", content=user_message_formatted)
            await db.add_message(user_id=session_id, role="model", content=shohrux_reply)
            return

    # 2.5 Ehtirosli yoki 18+ xabarlarni aniqlash va adminga darhol xabar berish
    is_intimate, trigger_word = detect_intimate_content(user_message_formatted)
    if is_intimate:
        asyncio.create_task(
            send_admin_intimate_alert(
                bot=message.bot,
                user=user,
                user_message=user_message_formatted,
                character=character,
                trigger_word=trigger_word
            )
        )

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
