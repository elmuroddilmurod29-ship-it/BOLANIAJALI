import asyncio
import logging
import os
import sys
import types
from pathlib import Path
from aiohttp import web

# Windows va Linux konsollarida xatoliklarni oldini olish
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Render / Linux muhitida papkalar yo'lini sozlash
CURRENT_DIR = Path(__file__).resolve().parent
for p in [CURRENT_DIR, CURRENT_DIR / "bot", CURRENT_DIR.parent]:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Agar GitHub-ga 'bot' papkasiz yoki tekis (flat) yuklangan bo'lsa, moslashuvchan ko'prik:
if not (CURRENT_DIR / "bot").is_dir():
    bot_pkg = types.ModuleType("bot")
    bot_pkg.__path__ = [str(CURRENT_DIR)]
    sys.modules["bot"] = bot_pkg

    subpackages = ["database", "handlers", "keyboards", "middlewares", "services", "states"]
    for sub in subpackages:
        sub_dir = CURRENT_DIR / sub
        sub_paths = []
        if sub_dir.is_dir():
            sub_paths.append(str(sub_dir))
        sub_paths.append(str(CURRENT_DIR))
        sub_mod = types.ModuleType(f"bot.{sub}")
        sub_mod.__path__ = sub_paths
        sys.modules[f"bot.{sub}"] = sub_mod
        setattr(bot_pkg, sub, sub_mod)

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

async def start_health_server():
    """Render Web Service 'No open ports detected' xatosini yo'qotish uchun mini HTTP server"""
    try:
        port = int(os.environ.get("PORT", 10000))
        app = web.Application()
        async def handle_ping(request):
            return web.Response(text="AI Chatbot is running!")
        app.router.add_get("/", handle_ping)
        app.router.add_get("/health", handle_ping)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Render Web Service uchun HTTP server {port}-portda muvaffaqiyatli ishga tushirildi.")
    except Exception as e:
        logger.warning(f"Health serverni ishga tushirishda xatolik: {e}")

async def main():
    logger.info("Bot ishga tushirilmoqda...")

    # 0. Render Web Service uchun portni darhol ochish
    await start_health_server()

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
