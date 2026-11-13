import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from bot.config import PRIMARY_ADMIN_ID, ADMIN_IDS, TARIFFS
from bot.database.db import db, get_now
from bot.states.user_states import UserStates
from bot.keyboards.inline import (
    plans_keyboard,
    cancel_payment_keyboard,
    payment_verify_keyboard
)
from bot.keyboards.reply import main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text == "💳 Tariflar va To'lov")
async def handle_plans_menu(message: types.Message, state: FSMContext):
    """Tariflar ro'yxati va ma'lumot"""
    await state.clear()
    text = (
        "💳 **BOTNING TARIF REJALARI VA IMKONIYATLARI:**\n\n"
        "1️⃣ **Tekin (Free):**\n"
        "• Kuniga 50 ta xabar\n"
        "• Har 24 soatda yangilanadi\n"
        "• Narxi: **0 so'm**\n\n"
        "2️⃣ **Standart:**\n"
        "• Oyiga 3,000 ta xabar\n"
        "• 30 kunlik muddat\n"
        "• Tezkor javoblar\n"
        "• Narxi: **20,000 so'm**\n\n"
        "3️⃣ **Premium (Cheksiz 💎):**\n"
        "• 1 oy davomida **CHEKSIZ** xabarlar!\n"
        "• Eng yuqori tezlik va ustuvorlik\n"
        "• 30 kunlik to'liq kirish\n"
        "• Narxi: **50,000 so'm**\n\n"
        "Obuna sotib olish uchun quyidagi tugmalardan birini tanlang:"
    )
    await message.answer(text, reply_markup=plans_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("buy_plan:"))
async def handle_buy_plan(callback: types.CallbackQuery, state: FSMContext):
    """Tarif tanlanganda to'lov ma'lumotlarini ko'rsatish"""
    plan_key = callback.data.split(":")[1]
    tariff = TARIFFS.get(plan_key)

    if not tariff:
        await callback.answer("Noto'g'ri tarif tanlandi!", show_alert=True)
        return

    card_number, card_holder = await db.get_card_details()

    await state.set_state(UserStates.waiting_payment_check)
    await state.update_data(plan=plan_key, amount=tariff["price"])

    text = (
        f"💳 **{tariff['name']} tarifi uchun to'lov:**\n\n"
        f"💰 To'lov summasi: **{tariff['price']:,} so'm**\n"
        f"💳 Karta raqami: `{card_number}`\n"
        f"👤 Karta egasi: **{card_holder}**\n\n"
        f"📌 **Yo'riqnoma:**\n"
        f"1. Yuqoridagi kartaga to'lovni amalga oshiring.\n"
        f"2. To'lov chekini (skrinshot yoki rasmini) botga yuboring.\n"
        f"3. Admin tekshirib tasdiqlashi bilan tarifingiz avtomatik ishga tushadi."
    )

    await callback.message.edit_text(
        text,
        reply_markup=cancel_payment_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_payment")
async def handle_cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    """To'lov jarayonini bekor qilish"""
    await state.clear()
    await callback.answer("To'lov jarayoni bekor qilindi.")
    await callback.message.delete()
    await callback.message.answer(
        "To'lov bekor qilindi. Asosiy menyudasiz:",
        reply_markup=main_menu_keyboard()
    )

@router.message(UserStates.waiting_payment_check, F.photo)
async def handle_payment_receipt(message: types.Message, state: FSMContext):
    """Foydalanuvchi to'lov cheki (rasmini) yuborganda"""
    data = await state.get_data()
    plan_key = data.get("plan", "standard")
    amount = data.get("amount", 20000)
    plan_name = TARIFFS.get(plan_key, {}).get("name", plan_key)

    photo_file_id = message.photo[-1].file_id
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Username yo'q"

    # 1. To'lovni DB ga yozish
    payment_id = await db.create_payment(
        user_id=user_id,
        plan=plan_key,
        amount=amount,
        photo_file_id=photo_file_id
    )

    await state.clear()

    # 2. Foydalanuvchiga tasdiq xabari
    await message.answer(
        "✅ **To'lov chekingiz qabul qilindi!**\n\n"
        "Admin chekni ko'rib chiqib tasdiqlashi bilan tarifingiz avtomatik faollashadi.\n"
        "Bu odatda 5-15 daqiqa vaqt oladi. Tasdiqlanganda sizga alohida xabar yuboriladi.",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

    # 3. Adminga chekni yuborish
    admin_caption = (
        f"🔔 **Yangi to'lov cheki qabul qilindi!**\n\n"
        f"🆔 To'lov ID: `#{payment_id}`\n"
        f"👤 Foydalanuvchi: {user_full_name} ({username})\n"
        f"🔢 Foydalanuvchi ID: `{user_id}`\n"
        f"📦 Tanlangan tarif: **{plan_name}**\n"
        f"💰 To'langan summa: **{amount:,} so'm**\n"
        f"🕒 Vaqt: {get_now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Barcha adminlarga yuboramiz
    targets = ADMIN_IDS if ADMIN_IDS else ([PRIMARY_ADMIN_ID] if PRIMARY_ADMIN_ID else [])
    for admin_id in targets:
        try:
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=photo_file_id,
                caption=admin_caption,
                reply_markup=payment_verify_keyboard(payment_id),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Adminga ({admin_id}) chek yuborishda xatolik: {e}")

@router.message(UserStates.waiting_payment_check)
async def handle_non_photo_receipt(message: types.Message):
    """Foydalanuvchi rasm o'rniga matn yuborsa ogohlantirish"""
    await message.answer(
        "⚠️ Iltimos, to'lov chekini **rasm (skrinshot)** ko'rinishida yuboring!\n"
        "Jarayonni bekor qilish uchun pastdagi tugmani bosing.",
        reply_markup=cancel_payment_keyboard()
    )

@router.callback_query(F.data.startswith("pay_approve:"))
async def handle_payment_approve(callback: types.CallbackQuery):
    """Admin to'lovni tasdiqlaganda"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Bu amal faqat admin uchun!", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[1])
    payment = await db.get_payment(payment_id)

    if not payment:
        await callback.answer("To'lov topilmadi!", show_alert=True)
        return

    if payment["status"] != "pending":
        await callback.answer(f"Bu to'lov allaqachon ko'rib chiqilgan ({payment['status']})!", show_alert=True)
        return

    # 1. DB dagi to'lov holatini yangilash
    await db.update_payment_status(payment_id, "approved")

    # 2. Foydalanuvchi tarifini yangilash
    plan_key = payment["plan"]
    user_id = payment["user_id"]
    tariff = TARIFFS.get(plan_key, {})
    duration = tariff.get("duration_days", 30) or 30
    monthly_limit = tariff.get("monthly_limit", 3000) or 3000

    await db.update_user_plan(
        user_id=user_id,
        plan=plan_key,
        duration_days=duration,
        monthly_limit=monthly_limit
    )

    # 3. Foydalanuvchiga xushxabar yuborish
    plan_name = tariff.get("name", plan_key)
    try:
        user_msg = (
            f"🎉 **XUSHXABAR! To'lovingiz muvaffaqiyatli tasdiqlandi!**\n\n"
            f"Sizga **{plan_name}** tarifi faollashtirildi.\n"
            f"📅 Amal qilish muddati: **30 kun**\n\n"
            f"Endi bemalol **'🗣 Suhbatlashish'** bo'limiga o'tib, botdan to'liq foydalanishingiz mumkin!"
        )
        await callback.bot.send_message(chat_id=user_id, text=user_msg, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Foydalanuvchiga tasdiq xabari yuborishda xatolik: {e}")

    # 4. Admin xabarini yangilash
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n✅ **TO'LOV TASDIQLANDI!** (Admin: {callback.from_user.full_name})",
        reply_markup=None,
        parse_mode="Markdown"
    )
    await callback.answer("✅ To'lov tasdiqlandi!", show_alert=True)

@router.callback_query(F.data.startswith("pay_reject:"))
async def handle_payment_reject(callback: types.CallbackQuery):
    """Admin to'lovni rad etganda"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Bu amal faqat admin uchun!", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[1])
    payment = await db.get_payment(payment_id)

    if not payment:
        await callback.answer("To'lov topilmadi!", show_alert=True)
        return

    if payment["status"] != "pending":
        await callback.answer(f"Bu to'lov allaqachon ko'rib chiqilgan ({payment['status']})!", show_alert=True)
        return

    # 1. DB holatini yangilash
    await db.update_payment_status(payment_id, "rejected")

    # 2. Foydalanuvchiga xabar yuborish
    try:
        user_msg = (
            "❌ **To'lovingiz rad etildi.**\n\n"
            "Sababi: Chek tasdiqlanmadi yoki summa mos kelmadi. "
            "Iltimos, to'lov ma'lumotlarini tekshirib qayta urinib ko'ring yoki adminga murojaat qiling."
        )
        await callback.bot.send_message(chat_id=payment["user_id"], text=user_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Foydalanuvchiga rad etish xabari yuborishda xatolik: {e}")

    # 3. Admin xabarini yangilash
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n❌ **TO'LOV RAD ETILDI!** (Admin: {callback.from_user.full_name})",
        reply_markup=None,
        parse_mode="Markdown"
    )
    await callback.answer("❌ To'lov rad etildi!", show_alert=True)
