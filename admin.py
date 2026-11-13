import asyncio
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
    confirm_clear_prompts_keyboard
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
        "📝 **AI PROMPT BOSHQARUV TIZIMI:**\n\n"
        "⚙️ **Arxitektura qoidasi:**\n"
        "• `Base_Prompt` (Qiz va O'g'il bola personajlarining asosiy xarakteri) bazada doim alohida turadi.\n"
        "• Siz kiritgan har bir yangi prompt `Extra_Prompt` sifatida saqlanib, **eski promptlarni O'CHIRMAYDI**.\n"
        "• Har safar AI ga murojaat qilinganda: `Base Prompt` + `Barcha Extra Promptlar` birgalikda yuboriladi!\n\n"
        f"📌 Hozirda faol qo'shimcha promptlar soni: **{count} ta**"
    )
    await callback.message.edit_text(text, reply_markup=admin_prompts_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_prompt_add")
async def handle_admin_prompt_add_start(callback: types.CallbackQuery, state: FSMContext):
    """Yangi qo'shimcha prompt kiritishni boshlash"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_extra_prompt)

    text = (
        "➕ **YANGI PROMPT / XISLAT QO'SHISH:**\n\n"
        "AI ga qo'shmoqchi bo'lgan yangi qoida, xislat yoki ko'rsatmani yozib yuboring.\n"
        "*(Bu yangi xislat avvalgi promptlar ustiga qo'shiladi va eskilari saqlanib qoladi)*\n\n"
        "Masalan: _'Foydalanuvchilarga doimo xushmuomala bo'l va javobing oxirida pozitiv ibora qo'sh'_"
    )
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_prompts")]
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_extra_prompt, F.text)
async def handle_admin_prompt_add_save(message: types.Message, state: FSMContext):
    """Yangi qo'shimcha promptni DB ga saqlash"""
    if not is_admin(message.from_user.id):
        return

    new_prompt = message.text.strip()
    prompt_id = await db.add_extra_prompt(new_prompt)
    await state.clear()

    await message.answer(
        f"✅ **Yangi prompt muvaffaqiyatli qo'shildi!** (ID: #{prompt_id})\n\n"
        f"📌 Qo'shilgan ko'rsatma:\n_{new_prompt}_\n\n"
        f"Eski xarakter va oldingi promptlar to'liq saqlanib qoldi. "
        f"Endi AI har ikkalasini inobatga olgan holda javob beradi.",
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_prompt_view")
async def handle_admin_prompt_view(callback: types.CallbackQuery):
    """Mavjud barcha promptlarni to'liq ko'rish"""
    if not is_admin(callback.from_user.id):
        return

    female_base = await db.get_base_prompt("female")
    male_base = await db.get_base_prompt("male")
    extra_prompts = await db.get_extra_prompts()

    extras_text = ""
    if extra_prompts:
        extras_text = "\n".join(
            f"**#{idx+1} (ID: {p['id']}):** {p['prompt_text']}"
            for idx, p in enumerate(extra_prompts)
        )
    else:
        extras_text = "*(Hozircha qo'shimcha promptlar yo'q)*"

    text = (
        "📋 **BAZADAGI BARCHA AI PROMPTLARI:**\n\n"
        f"👩 **Qiz bola AI Base Prompt:**\n_{female_base}_\n\n"
        f"👨 **O'g'il bola AI Base Prompt:**\n_{male_base}_\n\n"
        f"➕ **Faol Extra Promptlar ({len(extra_prompts)} ta):**\n"
        f"{extras_text}\n\n"
        "💡 Har bir suhbatda ushbu barcha ma'lumotlar AI ga tizim yo'riqnomasi sifatida birgalikda uzatiladi."
    )

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_prompts")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_prompt_clear_confirm")
async def handle_admin_prompt_clear_confirm(callback: types.CallbackQuery):
    """Extra promptlarni tozalashdan oldin ogohlantirish"""
    if not is_admin(callback.from_user.id):
        return

    text = (
        "⚠️ **DIQQAT!**\n\n"
        "Siz haqiqatan ham admin tomonidan kiritilgan barcha qo'shimcha (extra) promptlarni tozalab tashlamoqchimisiz?\n"
        "*(Asosiy Base Promptlarga tegilmaydi)*"
    )
    await callback.message.edit_text(text, reply_markup=confirm_clear_prompts_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_prompt_clear_yes")
async def handle_admin_prompt_clear_yes(callback: types.CallbackQuery):
    """Extra promptlarni tozalash"""
    if not is_admin(callback.from_user.id):
        return

    await db.clear_all_extra_prompts()
    await callback.answer("Barcha qo'shimcha promptlar tozalandi!", show_alert=True)
    await callback.message.edit_text(
        "✅ **Barcha qo'shimcha (extra) promptlar tozalandi!**\n\n"
        "Endi AI faqat asosiy Base Promptlar asosida ishlaydi.",
        reply_markup=admin_prompts_keyboard(),
        parse_mode="Markdown"
    )

# ==================== 5. MAJBURIY OBUNA KANALI ====================

@router.callback_query(F.data == "admin_channel")
async def handle_admin_channel_menu(callback: types.CallbackQuery, state: FSMContext):
    """Majburiy obuna kanalini sozlash"""
    if not is_admin(callback.from_user.id):
        return

    current_ch = await db.get_force_channel()
    ch_display = f"`{current_ch}`" if current_ch else "*(Belgilanmagan - Tekshiruv o'chiq)*"

    text = (
        "📢 **MAJBURIY OBUNA KANALI SOZLAMASI:**\n\n"
        f"Hozirgi kanal: {ch_display}\n\n"
        "Yangi kanal username yoki ID sini yuboring (masalan: `@kanal_nomi` yoki `-1001234567890`).\n"
        "Tekshiruvni o'chirib qo'yish uchun `none` yoki `off` deb yozing:"
    )
    await state.set_state(AdminStates.waiting_channel)

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_back")]
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_channel, F.text)
async def handle_admin_save_channel(message: types.Message, state: FSMContext):
    """Kanalni DB ga saqlash"""
    if not is_admin(message.from_user.id):
        return

    val = message.text.strip()
    if val.lower() in ("none", "off", "ochir", "yoq"):
        await db.set_force_channel("")
        await state.clear()
        await message.answer(
            "✅ Majburiy obuna kanali o'chirildi. Endi barcha foydalanuvchilar to'siqsiz kiradi.",
            reply_markup=admin_main_keyboard()
        )
    else:
        await db.set_force_channel(val)
        await state.clear()
        await message.answer(
            f"✅ Majburiy obuna kanali saqlandi: `{val}`\n\n"
            f"⚠️ **Eslatma:** Bot ushbu kanalda administrator (admin) bo'lishi shart!",
            reply_markup=admin_main_keyboard(),
            parse_mode="Markdown"
        )
