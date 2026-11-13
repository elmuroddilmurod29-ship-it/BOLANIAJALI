import asyncio
import logging
import os
import sys
import types
from pathlib import Path

# Windows va Linux konsollarida xatoliklarni oldini olish
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Render / Linux muhitida 'bot' modulini avtomatik topish
CURRENT_DIR = Path(__file__).resolve().parent
for p in [CURRENT_DIR, CURRENT_DIR / "bot", CURRENT_DIR.parent]:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Agar GitHub-ga fayllar 'bot' papkasisiz to'g'ridan-to'g'ri tashlangan bo'lsa
if not (CURRENT_DIR / "bot").exists() and (CURRENT_DIR / "config.py").exists():
    bot_pkg = types.ModuleType("bot")
    bot_pkg.__path__ = [str(CURRENT_DIR)]
    sys.modules["bot"] = bot_pkg

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN, PRIMARY_ADMIN_ID
from bot.database.db import db
from bot.handlers import main_router
from bot.middlewares.subscription import SubscriptionMiddleware

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("bot")

async def main():
    logger.info("Bot ishga tushirilmoqda...")

    # 1. Ma'lumotlar bazasini ishga tushirish
    await db.init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    # 2. Bot va Dispatcherni yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 3. Middleware larni ro'yxatdan o'tkazish
    subscription_middleware = SubscriptionMiddleware()
    dp.message.outer_middleware(subscription_middleware)
    dp.callback_query.outer_middleware(subscription_middleware)

    # 4. Handler routerlarini ulash
    dp.include_router(main_router)

    # 5. Eski to'planib qolgan xabarlarni tozalash (drop pending updates)
    await bot.delete_webhook(drop_pending_updates=True)

    # 6. Adminga bot ishga tushganligi haqida xabar yuborish
    if PRIMARY_ADMIN_ID:
        try:
            await bot.send_message(
                chat_id=PRIMARY_ADMIN_ID,
                text="🚀 <b>AI CHATBOT SAAS</b> boti muvaffaqiyatli ishga tushirildi va xizmat ko'rsatishga tayyor!"
            )
        except Exception as e:
            logger.warning(f"Adminga start xabarini yuborishda xatolik: {e}")

    logger.info("Bot polling rejimida ish boshladi.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot to'xtatildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot qo'lda to'xtatildi.")
