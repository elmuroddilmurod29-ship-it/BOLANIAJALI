import asyncio
import html
import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.config import ADMIN_IDS
from bot.database.db import db
from bot.states.user_states import AdminStates
from bot.keyboards.inline import (
    admin_main_keyboard,
    admin_prompts_keyboard,
    confirm_clear_prompts_keyboard,
    force_sub_keyboard,
    admin_chats_keyboard,
    admin_user_chat_keyboard
)
from bot.keyboards.reply import main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def handle_admin_command(message: types.Message, state: FSMContext):
    """Admin panelini ochish (/admin)"""
    if not is_admin(message.from_user.id):
        await message.reply("⛔️ Kechirasiz, bu buyruq faqat bot ma'murlari (admin) uchun!")
        return

    await state.clear()
    text = (
        "👑 **AI CHATBOT SAAS — ADMIN BOSHQARUV PANELI**\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    await message.answer(text, reply_markup=admin_main_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_back")
async def handle_admin_back(callback: types.CallbackQuery, state: FSMContext):
    """Admin bosh menyusiga qaytish"""
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    text = (
        "👑 **AI CHATBOT SAAS — ADMIN BOSHQARUV PANELI**\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=admin_main_keyboard(), parse_mode="Markdown")
    await callback.answer()

# ==================== 1. STATISTIKA ====================

@router.callback_query(F.data == "admin_stat")
async def handle_admin_stats(callback: types.CallbackQuery):
    """Statistika ko'rsatish"""
    if not is_admin(callback.from_user.id):
        return

    stats = await db.get_statistics()

    text = (
        "📊 **BOT STATISTIKASI VA MOLIYAVIY HISOBOT:**\n\n"
        f"👥 **Foydalanuvchilar:**\n"
        f"• Jami a'zolar: **{stats['total_users']:,} ta**\n"
        f"• Bugun qo'shilganlar: **{stats['today_users']:,} ta**\n\n"
        f"💳 **Tariflar bo'yicha taqsimot:**\n"
        f"• 🆓 Tekin (Free): **{stats['free_users']:,} ta**\n"
        f"• 🥈 Standart: **{stats['standard_users']:,} ta**\n"
        f"• 👑 Premium: **{stats['premium_users']:,} ta**\n\n"
        f"💰 **To'lovlar va Daromad:**\n"
        f"• Bugungi to'lovlar soni: **{stats['today_payments_count']} ta**\n"
        f"• Bugungi tushum: **{stats['today_revenue']:,} so'm**\n"
        f"• Jami tasdiqlangan to'lovlar: **{stats['total_payments_count']} ta**\n"
        f"• Jami tushum: **{stats['total_revenue']:,} so'm**\n"
        f"• Kutilayotgan to'lovlar: **{stats['pending_payments_count']} ta**\n"
    )

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stat")],
            [types.InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_back")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# ==================== 2. XABAR YUBORISH (BROADCAST) ====================

@router.callback_query(F.data == "admin_broadcast")
async def handle_admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    """Barcha foydalanuvchilarga xabar yuborishni boshlash"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_broadcast_message)

    text = (
        "📢 **BARCHA FOYDALANUVCHILARGA XABAR YUBORISH (BROADCAST):**\n\n"
        "Yubormoqchi bo'lgan xabaringizni (matn, rasm, video yoki fayl) shu yerga yuboring.\n\n"
        "Bekor qilish uchun pastdagi tugmani bosing."
    )
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_back")]
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_broadcast_message)
async def handle_admin_broadcast_send(message: types.Message, state: FSMContext):
    """Xabarni barcha foydalanuvchilarga tarqatish"""
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    status_msg = await message.answer("🚀 Xabar yuborish boshlandi, iltimos kuting...")

    user_ids = await db.get_all_user_ids()
    total = len(user_ids)
    success = 0
    failed = 0

    for uid in user_ids:
        try:
            await message.copy_to(chat_id=uid)
            success += 1
            await asyncio.sleep(0.04)  # Telegram limitlariga tushmaslik uchun
        except Exception:
            failed += 1

    report = (
        "📢 **Xabar tarqatish yakunlandi!**\n\n"
        f"👥 Jami foydalanuvchilar: **{total} ta**\n"
        f"✅ Muvaffaqiyatli yetkazildi: **{success} ta**\n"
        f"❌ Yetib bormadi (bloklagan): **{failed} ta**"
    )
    await status_msg.edit_text(report, parse_mode="Markdown")
    await message.answer("Admin bosh menyusi:", reply_markup=admin_main_keyboard())

# ==================== 3. REKVIZITLARNI O'ZGARTIRISH ====================

@router.callback_query(F.data == "admin_requisites")
async def handle_admin_requisites(callback: types.CallbackQuery, state: FSMContext):
    """Rekvizitlarni ko'rish va o'zgartirishni boshlash"""
    if not is_admin(callback.from_user.id):
        return

    card_num, card_holder = await db.get_card_details()

    text = (
        "💳 **TO'LOV REKVIZITLARI:**\n\n"
        f"💳 Karta raqami: `{card_num}`\n"
        f"👤 Karta egasi: **{card_holder}**\n\n"
        "O'zgartirish uchun yangi **Karta raqamini** (16 xonali) yuboring:"
    )
    await state.set_state(AdminStates.waiting_card_number)

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_back")]
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_card_number, F.text)
async def handle_admin_save_card_number(message: types.Message, state: FSMContext):
    """Karta raqamini qabul qilib, egasining ismini so'rash"""
    if not is_admin(message.from_user.id):
        return

    card_num = message.text.strip()
    await state.update_data(new_card_number=card_num)
    await state.set_state(AdminStates.waiting_card_holder)

    await message.answer(
        f"✅ Karta raqami qabul qilindi: `{card_num}`\n\n"
        f"Endi ushbu kartaning **Egasining Ism-Familiyasini** kiriting:"
    )

@router.message(AdminStates.waiting_card_holder, F.text)
async def handle_admin_save_card_holder(message: types.Message, state: FSMContext):
    """Karta egasi ismini qabul qilib, DB ga saqlash"""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    card_num = data.get("new_card_number", "8600 0000 0000 0000")
    card_holder = message.text.strip()

    await db.set_card_details(card_num, card_holder)
    await state.clear()

    await message.answer(
        "🎉 **Rekvizitlar muvaffaqiyatli saqlandi!**\n\n"
        f"💳 Yangi karta: `{card_num}`\n"
        f"👤 Karta egasi: **{card_holder}**\n\n"
        "Endi barcha to'lov qiluvchilarga ushbu rekvizitlar ko'rsatiladi.",
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown"
    )

# ==================== 4. AI PROMPT QO'SHISH VA BOSHQARISH ====================

@router.callback_query(F.data == "admin_prompts")
async def handle_admin_prompts_menu(callback: types.CallbackQuery, state: FSMContext):
    """AI Prompt boshqaruvi menyusi"""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    extra_prompts = await db.get_extra_prompts()
    count = len(extra_prompts)

    text = (
        "📝 <b>AI PROMPT BOSHQARUV TIZIMI:</b>\n\n"
        "⚙️ <b>Arxitektura qoidasi:</b>\n"
        "• <code>Base_Prompt</code> (Qiz va O'g'il bola personajlarining asosiy xarakteri) bazada doim alohida turadi.\n"
        "• Siz kiritgan har bir yangi prompt <code>Extra_Prompt</code> sifatida saqlanib, <b>eski promptlarni O'CHIRMAYDI</b>.\n"
        "• Har safar AI ga murojaat qilinganda siz qo'shgan yangi promptlar <b>ENG YUQORI USTUVORLIK</b> bilan yuboriladi!\n\n"
        f"📌 Hozirda faol qo'shimcha promptlar soni: <b>{count} ta</b>"
    )
    await callback.message.edit_text(text, reply_markup=admin_prompts_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_prompt_add")
async def handle_admin_prompt_add_start(callback: types.CallbackQuery, state: FSMContext):
    """Yangi qo'shimcha prompt kiritishni boshlash"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_extra_prompt)

    text = (
        "➕ <b>YANGI PROMPT / QAT'IY QOIDA QO'SHISH:</b>\n\n"
        "AI ga qo'shmoqchi bo'lgan yangi qoida, xislat yoki ko'rsatmani yozib yuboring.\n"
        "<i>(Bu yangi ko'rsatma eng yuqori ustuvorlik bilan AI ga ulanadi va eski xarakter saqlanib qoladi)</i>\n\n"
        "Masalan:\n"
        "<code>FAQAT KICHIK HARFLAR: barcha gaplaring kichik harfda boshlansin. Nuqta va so'roq umuman ishlatilmasin.</code>"
    )
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_prompts")]
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.message(AdminStates.waiting_extra_prompt, F.text)
async def handle_admin_prompt_add_save(message: types.Message, state: FSMContext):
    """Yangi qo'shimcha promptni DB ga saqlash"""
    if not is_admin(message.from_user.id):
        return

    new_prompt = message.text.strip()
    prompt_id = await db.add_extra_prompt(new_prompt)
    await state.clear()

    escaped_prompt = html.escape(new_prompt)
    await message.answer(
        f"✅ <b>Yangi prompt muvaffaqiyatli qo'shildi!</b> (ID: #{prompt_id})\n\n"
        f"📌 Qo'shilgan ko'rsatma:\n<code>{escaped_prompt}</code>\n\n"
        f"Ushbu qoida sun'iy intellektga eng yuqori ustuvorlik (override) bilan ulandi!",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_prompt_view")
async def handle_admin_prompt_view(callback: types.CallbackQuery):
    """Mavjud qo'shimcha promptlarni ko'rish va boshqarish"""
    if not is_admin(callback.from_user.id):
        return

    extra_prompts = await db.get_extra_prompts()
    keyboard_buttons = []

    if extra_prompts:
        lines = ["📋 <b>ADMINNING QO'SHIMCHA PROMPTLARI RO'YXATI:</b>\n"]
        for idx, p in enumerate(extra_prompts):
            p_text = html.escape(p['prompt_text'])
            # Matn juda uzun bo'lsa qisqartirish
            display_text = p_text if len(p_text) <= 300 else p_text[:300] + "..."
            lines.append(f"<b>#{idx+1} (ID: {p['id']}):</b>\n<code>{display_text}</code>\n")
            keyboard_buttons.append([
                types.InlineKeyboardButton(
                    text=f"🗑 #{idx+1} (ID: {p['id']}) ni o'chirish",
                    callback_data=f"admin_pdel_{p['id']}"
                )
            ])
        text = "\n".join(lines)
    else:
        text = (
            "📋 <b>QO'SHIMCHA PROMPTLAR:</b>\n\n"
            "<i>Hozircha admin tomonidan kiritilgan qo'shimcha promptlar yo'q. "
            "Asosiy 'Amina' va 'Shohrux' bazaviy personajlari to'liq faol!</i>\n\n"
            "Yangi xislat yoki qat'iy qoida qo'shish uchun quyidagi tugmani bosing:"
        )

    keyboard_buttons.append([
        types.InlineKeyboardButton(text="➕ Yangi Prompt qo'shish", callback_data="admin_prompt_add")
    ])
    keyboard_buttons.append([
        types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_prompts")
    ])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_pdel_"))
async def handle_admin_prompt_delete_single(callback: types.CallbackQuery):
    """Aynan bitta qo'shimcha promptni o'chirish"""
    if not is_admin(callback.from_user.id):
        return

    try:
        prompt_id = int(callback.data.split("_")[-1])
        await db.delete_extra_prompt(prompt_id)
        await callback.answer(f"#{prompt_id} raqamli prompt o'chirildi!", show_alert=True)
    except Exception as e:
        logger.error(f"Promptni o'chirishda xatolik: {e}")
        await callback.answer("O'chirishda xatolik!", show_alert=True)

    await handle_admin_prompt_view(callback)

@router.callback_query(F.data == "admin_prompt_clear_confirm")
async def handle_admin_prompt_clear_confirm(callback: types.CallbackQuery):
    """Extra promptlarni tozalashdan oldin ogohlantirish"""
    if not is_admin(callback.from_user.id):
        return

    text = (
        "⚠️ <b>DIQQAT!</b>\n\n"
        "Siz haqiqatan ham admin tomonidan kiritilgan barcha qo'shimcha (extra) promptlarni tozalab tashlamoqchimisiz?\n"
        "<i>(Asosiy Base Promptlarga tegilmaydi)</i>"
    )
    await callback.message.edit_text(text, reply_markup=confirm_clear_prompts_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_prompt_clear_yes")
async def handle_admin_prompt_clear_yes(callback: types.CallbackQuery):
    """Extra promptlarni tozalash"""
    if not is_admin(callback.from_user.id):
        return

    await db.clear_all_extra_prompts()
    await callback.answer("Barcha qo'shimcha promptlar tozalandi!", show_alert=True)
    await callback.message.edit_text(
        "✅ <b>Barcha qo'shimcha (extra) promptlar tozalandi!</b>\n\n"
        "Endi AI faqat asosiy Base Promptlar asosida ishlaydi.",
        reply_markup=admin_prompts_keyboard(),
        parse_mode="HTML"
    )

# ==================== 5. MAJBURIY OBUNA KANALLARI ====================

@router.callback_query(F.data == "admin_channel")
async def handle_admin_channel_menu(callback: types.CallbackQuery, state: FSMContext):
    """Majburiy obuna kanallarini sozlash menyusi"""
    if not is_admin(callback.from_user.id):
        return

    from bot.middlewares.subscription import parse_channels
    await state.clear()
    current_ch = await db.get_force_channel()
    parsed = parse_channels(current_ch) if current_ch else []

    if parsed:
        ch_display = "\n".join([f"• <b>{c.get('display')}</b>" for c in parsed])
    else:
        ch_display = "<i>(Belgilanmagan — Majburiy obuna hozirda o'chiq)</i>"

    text = (
        "📢 <b>MAJBURIY OBUNA KANALLARI SOZLAMASI:</b>\n\n"
        f"<b>Hozirgi kanallar:</b>\n{ch_display}\n\n"
        "Yangi kanal qo'shish uchun kanal linkini yoki usernamesini yuboring.\n"
        "<i>Bir nechta kanal bo'lsa, vergul yoki yangi qatordan yozib yuboring.</i>\n\n"
        "Masalan:\n"
        "<code>@kanal1, @kanal2</code>\n"
        "yoki <code>https://t.me/kanal1</code>\n\n"
        "⚠️ <b>ENG MUHIM QOIDA:</b>\n"
        "Kanalni kiritishdan oldin botni (@xadechabot) o'sha kanallarga <b>Administrator</b> qilib qo'shishingiz shart! Aks holda bot foydalanuvchilarning obunasini tekshira olmaydi.\n\n"
        "Tekshiruvni butunlay o'chirib qo'yish uchun <code>none</code> yoki <code>off</code> deb yozing:"
    )
    await state.set_state(AdminStates.waiting_channel)

    buttons = []
    if parsed:
        buttons.append([types.InlineKeyboardButton(text="👁 Obuna oynasini sinab ko'rish", callback_data="admin_channel_test")])
        buttons.append([types.InlineKeyboardButton(text="🗑 Majburiy obunani o'chirish", callback_data="admin_channel_clear")])
    buttons.append([types.InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_back")])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_channel_clear")
async def handle_admin_channel_clear(callback: types.CallbackQuery, state: FSMContext):
    """Majburiy obunani tozalash"""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    await db.set_force_channel("")
    await callback.answer("✅ Majburiy obuna o'chirildi!", show_alert=True)
    await handle_admin_channel_menu(callback, state)

@router.callback_query(F.data == "admin_channel_test")
async def handle_admin_channel_test(callback: types.CallbackQuery):
    """Admin uchun obuna oynasini sinovdan o'tkazish"""
    if not is_admin(callback.from_user.id):
        return

    from bot.middlewares.subscription import parse_channels, check_all_subscriptions
    channels_raw = await db.get_force_channel()
    if not channels_raw:
        await callback.answer("Majburiy obuna kanallari belgilanmagan!", show_alert=True)
        return

    is_sub, missing = await check_all_subscriptions(callback.bot, callback.from_user.id, channels_raw)
    parsed = parse_channels(channels_raw)
    keyboard = force_sub_keyboard(parsed)

    sub_status = "✅ Barcha kanallarga a'zosiz!" if is_sub else "❌ Siz hali kanallarga to'liq a'zo emassiz!"
    text = (
        "👁 <b>OBUNA OYNASI SINOVI (ADMIN TEST):</b>\n\n"
        "Oddiy foydalanuvchilar botga yozganda aynan mana shu oynani ko'rishadi:\n"
        "----------------------------------------\n"
        "⚠️ <b>Botdan foydalanish uchun homiy kanalimizga a'zo bo'lishingiz shart!</b>\n\n"
        "Iltimos, pastdagi tugma(lar) orqali kanalga a'zo bo'ling va so'ng "
        "<b>'✅ Obunani tekshirish'</b> tugmasini bosing.\n"
        "----------------------------------------\n\n"
        f"📊 <b>Sizning profilingiz holati:</b> {sub_status}"
    )

    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.message(AdminStates.waiting_channel, F.text)
async def handle_admin_save_channel(message: types.Message, state: FSMContext):
    """Kanalni DB ga saqlash va bot admin huquqini tekshirish"""
    if not is_admin(message.from_user.id):
        return

    from bot.middlewares.subscription import parse_channels
    val = message.text.strip()
    if val.lower() in ("none", "off", "ochir", "yoq", "0"):
        await db.set_force_channel("")
        await state.clear()
        await message.answer(
            "✅ <b>Majburiy obuna o'chirildi!</b> Endi barcha foydalanuvchilar to'siqsiz kiradi.",
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML"
        )
        return

    parsed = parse_channels(val)
    if not parsed:
        await message.answer(
            "❌ <b>Noto'g'ri format!</b> Iltimos, kanal username (masalan: <code>@kanal</code>) yoki havolasini yuboring.",
            parse_mode="HTML"
        )
        return

    status_report = []
    valid_channels = []
    has_warning = False

    for ch in parsed:
        chat_id = ch["chat_id"]
        display = ch.get("display", str(chat_id))
        try:
            chat = await message.bot.get_chat(chat_id)
            ch_title = html.escape(chat.title or display)
            ch["title"] = ch_title

            bot_member = await message.bot.get_chat_member(chat_id, message.bot.id)
            if bot_member.status in ("administrator", "creator"):
                status_report.append(f"✅ <b>{ch_title}</b> (<code>{display}</code>) — Bot kanalda <b>Administrator</b>!")
                valid_channels.append(ch)
            else:
                has_warning = True
                status_report.append(f"⚠️ <b>{ch_title}</b> (<code>{display}</code>) — Bot kanalda bor, lekin <b>administrator emas</b>!")
                valid_channels.append(ch)
        except Exception as e:
            has_warning = True
            logger.warning(f"Kanalni tekshirishda xatolik ({chat_id}): {e}")
            err_text = html.escape(str(e))
            status_report.append(f"⚠️ <code>{display}</code> — Bot bu kanalni tekshira olmadi (<i>{err_text}</i>)")
            valid_channels.append(ch)

    # Saqlash (chat_id larni vergul bilan ajratilgan holda)
    channels_str = ", ".join([str(c["chat_id"]) for c in valid_channels])
    await db.set_force_channel(channels_str)
    await state.clear()

    report_text = "\n".join(status_report)
    warning_advice = (
        "\n\n⚠️ <b>DIQQAT:</b> Bot administrator bo'lmagan kanallarda foydalanuvchilarning obunasini tekshira olmaydi! "
        "Iltimos, botni (@xadechabot) o'sha kanalga <b>Administrator</b> qilib qo'shing."
    ) if has_warning else ""

    await message.answer(
        f"🎉 <b>Majburiy obuna kanallari muvaffaqiyatli saqlandi!</b>\n\n"
        f"{report_text}"
        f"{warning_advice}\n\n"
        "💡 <i>Pastdagi tugma orqali oddiy foydalanuvchilar qanday ko'rishini sinab ko'rishingiz mumkin:</i>",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="👁 Obunani sinab ko'rish", callback_data="admin_channel_test")],
                [types.InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_back")]
            ]
        ),
        parse_mode="HTML"
    )

# ==================== 6. FOYDALANUVCHILAR YOZISHMALARI VA HISOBOTLAR ====================

@router.callback_query(F.data.startswith("admin_chats"))
async def handle_admin_chats_menu(callback: types.CallbackQuery, state: FSMContext):
    """Foydalanuvchilarning bot bilan yozishmalari hisoboti"""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    data = callback.data
    offset = 0
    if ":" in data:
        try:
            offset = int(data.split(":")[1])
        except ValueError:
            offset = 0

    limit = 8
    users = await db.get_active_chat_users(limit=limit, offset=offset)
    total_count = await db.get_chat_users_count()

    if not users:
        text = (
            "📋 <b>YOZISHMALAR VA HISOBOT:</b>\n\n"
            "Hozircha botda foydalanuvchilar suhbati mavjud emas yoki xotira bo'sh."
        )
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔍 User ID orqali qidirish", callback_data="admin_search_chat")],
                [types.InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_back")]
            ]
        )
        if callback.message.text:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        return

    start_num = offset + 1
    end_num = min(offset + limit, total_count)
    text = (
        "📋 <b>FOYDALANUVCHILAR YOZISHMALARI VA HISOBOTI:</b>\n\n"
        f"📊 Jami faol suhbatlashganlar: <b>{total_count} ta</b>\n"
        f"Ko'rsatilmoqda: <b>{start_num}-{end_num}</b>\n\n"
        "💡 <i>Suhbat tarixini o'qish uchun pastdagi foydalanuvchilardan birini tanlang yoki ID bo'yicha qidiring:</i>"
    )
    keyboard = admin_chats_keyboard(users, total_count, offset=offset, limit=limit)
    if callback.message.text:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_chat:"))
async def handle_admin_user_chat(callback: types.CallbackQuery, state: FSMContext):
    """Aynan bitta foydalanuvchining bot bilan yozishgan chat tarixini ko'rish"""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    parts = callback.data.split(":")
    target_uid = int(parts[1])
    offset = int(parts[2]) if len(parts) > 2 else 0

    limit = 10
    messages, total_msgs = await db.get_user_chat_messages(target_uid, limit=limit, offset=offset)
    target_user = await db.get_user(target_uid)

    uname = f"@{target_user.get('username')}" if target_user and target_user.get("username") else "yo'q"
    full_name = html.escape(target_user.get("full_name") or "Foydalanuvchi") if target_user else "Nomaʼlum"
    char_code = target_user.get("character", "female") if target_user else "female"
    char_label = "Amina (Qiz bola AI)" if char_code == "female" else "Shohrux (O'g'il bola AI)"

    if not messages:
        text = (
            f"💬 <b>SUHBAT TARIXI:</b> {full_name} ({uname})\n"
            f"🆔 <b>ID:</b> <code>{target_uid}</code> | 🎭 <b>Personaj:</b> {char_label}\n\n"
            "<i>Ushbu foydalanuvchi bilan yozishmalar mavjud emas yoki tozalangan.</i>"
        )
        keyboard = admin_user_chat_keyboard(target_uid, total_msgs=0, offset=0, limit=limit)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        return

    start_idx = max(1, total_msgs - offset - len(messages) + 1)
    end_idx = total_msgs - offset
    header = (
        f"💬 <b>SUHBAT TARIXI:</b> {full_name} ({uname})\n"
        f"🆔 <b>ID:</b> <code>{target_uid}</code> | 🎭 <b>Personaj:</b> {char_label}\n"
        f"📊 Jami xabarlar: <b>{total_msgs} ta</b> (Ko'rsatilmoqda: <b>{start_idx}-{end_idx}</b>)\n"
        "----------------------------------------\n\n"
    )

    body_lines = []
    for m in messages:
        role_label = f"👤 <b>{full_name}</b>" if m["role"] == "user" else f"🤖 <b>{char_label}</b>"
        time_part = f" <i>({m.get('created_at', '')[:16]})</i>" if m.get("created_at") else ""
        content_escaped = html.escape(m["content"])
        body_lines.append(f"{role_label}{time_part}:\n{content_escaped}\n")

    full_text = header + "\n".join(body_lines)
    if len(full_text) > 4000:
        full_text = full_text[:3990] + "\n... <i>(qisqartirildi)</i>"

    keyboard = admin_user_chat_keyboard(target_uid, total_msgs=total_msgs, offset=offset, limit=limit)
    if callback.message.text:
        await callback.message.edit_text(full_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.message.answer(full_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_clear_chat:"))
async def handle_admin_clear_user_chat(callback: types.CallbackQuery):
    """Admin tomonidan foydalanuvchining chat tarixini tozalash"""
    if not is_admin(callback.from_user.id):
        return

    target_uid = int(callback.data.split(":")[1])
    await db.clear_chat_history(target_uid)
    await callback.answer("✅ Foydalanuvchi suhbat tarixi tozalandi!", show_alert=True)
    await handle_admin_chats_menu(callback, None)

@router.callback_query(F.data == "admin_search_chat")
async def handle_admin_search_chat_start(callback: types.CallbackQuery, state: FSMContext):
    """User ID yoki username bo'yicha suhbat qidirish"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_chat_search)
    text = (
        "🔍 <b>FOYDALANUVCHINI QIDIRISH:</b>\n\n"
        "Qidirmoqchi bo'lgan foydalanuvchining <b>Telegram ID</b> raqamini yuboring.\n"
        "(Masalan: <code>6125160021</code>)"
    )
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_chats")]
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.message(AdminStates.waiting_chat_search, F.text)
async def handle_admin_search_chat_result(message: types.Message, state: FSMContext):
    """Qidiruv natijasini ko'rsatish"""
    if not is_admin(message.from_user.id):
        return

    query = message.text.strip().lstrip('@')
    target_uid = None
    if query.isdigit() or (query.startswith("-") and query[1:].isdigit()):
        target_uid = int(query)
    else:
        # Username bo'yicha qidirish
        user_data = await db.get_user_by_username(query)
        if user_data:
            target_uid = user_data["user_id"]

    if not target_uid:
        await message.answer(
            "❌ <b>Foydalanuvchi topilmadi!</b>\nIltimos, to'g'ri Telegram ID raqam yuboring.",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_chats")]]
            ),
            parse_mode="HTML"
        )
        return

    await state.clear()
    limit = 10
    messages, total_msgs = await db.get_user_chat_messages(target_uid, limit=limit, offset=0)
    target_user = await db.get_user(target_uid)

    uname = f"@{target_user.get('username')}" if target_user and target_user.get("username") else "yo'q"
    full_name = html.escape(target_user.get("full_name") or "Foydalanuvchi") if target_user else "Nomaʼlum"
    char_code = target_user.get("character", "female") if target_user else "female"
    char_label = "Amina (Qiz bola AI)" if char_code == "female" else "Shohrux (O'g'il bola AI)"

    if not messages:
        text = (
            f"💬 <b>SUHBAT TARIXI:</b> {full_name} ({uname})\n"
            f"🆔 <b>ID:</b> <code>{target_uid}</code> | 🎭 <b>Personaj:</b> {char_label}\n\n"
            "<i>Ushbu foydalanuvchi bilan yozishmalar mavjud emas yoki tozalangan.</i>"
        )
        keyboard = admin_user_chat_keyboard(target_uid, total_msgs=0, offset=0, limit=limit)
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        return

    header = (
        f"💬 <b>SUHBAT TARIXI:</b> {full_name} ({uname})\n"
        f"🆔 <b>ID:</b> <code>{target_uid}</code> | 🎭 <b>Personaj:</b> {char_label}\n"
        f"📊 Jami xabarlar: <b>{total_msgs} ta</b>\n"
        "----------------------------------------\n\n"
    )

    body_lines = []
    for m in messages:
        role_label = f"👤 <b>{full_name}</b>" if m["role"] == "user" else f"🤖 <b>{char_label}</b>"
        time_part = f" <i>({m.get('created_at', '')[:16]})</i>" if m.get("created_at") else ""
        content_escaped = html.escape(m["content"])
        body_lines.append(f"{role_label}{time_part}:\n{content_escaped}\n")

    full_text = header + "\n".join(body_lines)
    if len(full_text) > 4000:
        full_text = full_text[:3990] + "\n... <i>(qisqartirildi)</i>"

    keyboard = admin_user_chat_keyboard(target_uid, total_msgs=total_msgs, offset=0, limit=limit)
    await message.answer(full_text, reply_markup=keyboard, parse_mode="HTML")
