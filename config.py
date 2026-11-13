import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylni yuklash
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi!")

# ADMIN_ID bir nechta bo'lishi mumkin: "12345,67890" yoki bitta "12345"
admin_raw = os.getenv("ADMIN_ID", "0").strip()
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in admin_raw.split(",") if x.strip().isdigit()
]
PRIMARY_ADMIN_ID: int = ADMIN_IDS[0] if ADMIN_IDS else 0

AI_API_KEY: str = os.getenv("AI_API_KEY", "").strip()
if not AI_API_KEY:
    raise ValueError("AI_API_KEY .env faylida topilmadi!")

AI_MODEL: str = os.getenv("AI_MODEL", "gemini-3.5-flash-lite").strip()
FORCE_CHANNEL: str = os.getenv("FORCE_CHANNEL", "").strip()
DATABASE_PATH: str = str(BASE_DIR / os.getenv("DATABASE_PATH", "database.sqlite3"))

# Tarif sozlamalari
TARIFFS = {
    "free": {
        "name": "Tekin (Free)",
        "price": 0,
        "daily_limit": 50,
        "monthly_limit": None,
        "duration_days": None,
        "description": "Kuniga 50 ta bepul xabar (Har 24 soatda avtomatik yangilanadi)."
    },
    "standard": {
        "name": "Standart",
        "price": 20000,
        "daily_limit": None,
        "monthly_limit": 3000,
        "duration_days": 30,
        "description": "Oyiga 3000 ta xabar (30 kunlik muddat)."
    },
    "premium": {
        "name": "Premium",
        "price": 50000,
        "daily_limit": None,
        "monthly_limit": None,  # Cheksiz
        "duration_days": 30,
        "description": "1 oy davomida CHEKSIZ xabarlar va eng yuqori tezlik!"
    }
}
