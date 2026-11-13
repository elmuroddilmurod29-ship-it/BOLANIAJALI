# 🤖 AI CHATBOT SAAS - Telegram Bot Arxitekturasi

Ushbu loyiha zamonaviy va yuqori yuklamalarga chidamli **Python (Aiogram 3.x)**, asinxron SQLite (**aiosqlite**) hamda **Google Gemini AI** texnologiyalari asosida yaratilgan **Telegram Bot SAAS platformasi** hisoblanadi.

---

## 🚀 Loyiha Imkoniyatlari va Texnik Xususiyatlari

### 1. 👥 Foydalanuvchi Interfeysi (UI)
* **Majburiy Obuna (Force Subscribe):** Homiy kanalga a'zo bo'lmaguncha bot ishlamaydi (Admin paneldan kanalni osongina sozlash yoki o'chirish mumkin).
* **Asosiy Menyu:**
  * 🗣 **Suhbatlashish:** Maxfiy va izolyatsiya qilingan AI suhbat rejimini ishga tushirish.
  * 🎭 **Personajni tanlash:**
    * 👩 **Amina (Qiz bola AI - V.100 MAX)** — 22 yoshli toshkentlik qiz. O'tmish travmasi, o'ziga xos xarakter, realistik muloqot va his-tuyg'ular.
    * 👨 **Shohrux (O'g'il bola AI - V.100 MAX)** — 24 yoshli toshkentlik yigit. Avtosalon, mashinalar, ko'cha slengi, rashkchi va o'ziga ishongan xarakter.
  * 💳 **Tariflar va To'lov:** Obunalar va to'lov rekvizitlari.
  * 👤 **Profilim:** Tanlangan personaj, ID, tarif turi, bugungi/oylik qolgan xabarlar soni va obuna muddati.

---

### 2. 💳 Monetizatsiya va Tariflar Tizimi
Botda 3 xil tarif rejasi mavjud:
1. 🆓 **Tekin (Free):** Kuniga **50 ta** xabar (Har 24 soatda avtomatik yangilanadi).
2. 🥈 **Standart (20,000 so'm):** Oyiga **3,000 ta** xabar (30 kunlik muddat).
3. 👑 **Premium (50,000 so'm):** 1 oy davomida **CHEKSIZ** xabar yozish!

#### 📸 To'lov Jarayoni (Manual Verification):
1. Foydalanuvchi tarifni tanlaganda, bot unga bazadagi joriy karta raqami, karta egasi ismi va summani ko'rsatadi.
2. Foydalanuvchi to'lovni amalga oshirib, chek rasmini botga yuboradi.
3. Bot chekni va to'lovchi ma'lumotlarini darhol Adminning lichkasiga yuboradi (`[✅ Tasdiqlash]` va `[❌ Rad etish]` tugmalari bilan).
4. Admin tasdiqlasa:
   - Foydalanuvchining tarifi avtomatik yangilanadi.
   - Foydalanuvchiga xushxabar yuboriladi.
5. Admin rad etsa, foydalanuvchiga rad etilganligi haqida xabar boradi.

---

### 3. 👑 Admin Panel (Faqat `ADMIN_ID` uchun)
`/admin` komandasi orqali ochiladi:
* 📊 **Statistika:** Jami a'zolar, bugun qo'shilganlar, Free/Standart/Premium foydalanuvchilar taqsimoti, bugungi to'lovlar va jami daromad.
* 📢 **Xabar yuborish (Broadcast):** Barcha foydalanuvchilarga reklama yoki xabar yuborish (Telegram limitlariga mos xavfsiz tezlikda).
* 💳 **Rekvizitni o'zgartirish:** Karta raqami va karta egasi ismini bevosita bot orqali o'zgartirish (ma'lumotlar bazasida saqlanadi, hardcode qilinmagan).
* 📝 **AI Prompt boshqaruvi (O'ta muhim!):**
  - Baza (DB) da `Base_Prompt` (Asosiy xarakter) alohida saqlanadi.
  - Admin yangi prompt/xislat kiritganda, u **eski promptlarni o'chirib tashlamaydi**, balki `Extra_Prompt` sifatida saqlanib, to'planib boradi.
  - Har safar AI ga murojaat qilinganda: `Base_Prompt + Barcha Extra Promptlar` birgalikda yuboriladi.
* 📢 **Majburiy Obuna Kanali:** Kanalni bot orqali istalgan paytda kiritish yoki o'chirib qo'yish.

---

### 4. 🧠 AI va Xotira Izolyatsiyasi (Memory Management)
* **Faqat Lichkada Muloqot:** AI foydalanuvchilar bilan faqat botning o'zida (private chat) muloqot qiladi, guruhlarda shaxsiy ma'lumotlar aralashmaydi.
* **Qat'iy Xotira Izolyatsiyasi (No Memory Leaks):** Har bir foydalanuvchining suhbati ma'lumotlar bazasida uning `user_id` si bilan qat'iy bog'langan. AI faqat o'sha `user_id` ga tegishli xabarlar tarixini oladi. Boshqa foydalanuvchilarning ismi, xabarlari yoki savollari mutlaqo aralashmaydi!
* **Kontekst:**
  $$\text{System Instruction} = \text{Base Prompt (Qiz/O'g'il)} + \sum \text{Admin Extra Prompts}$$

---

## 📁 Loyiha Strukturasi

```text
BOLANI AJALI AI/
├── bot/
│   ├── __init__.py
│   ├── config.py              # .env va tizim konfiguratsiyasi
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py              # Asinxron SQLite (aiosqlite) to'liq DB qatlami
│   ├── services/
│   │   ├── __init__.py
│   │   └── ai_service.py      # Google Gemini 3.5 Flash-lite / 3.8 Flash, Xotira izolyatsiyasi
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── subscription.py    # Majburiy obunani tekshirish middleware
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── user.py            # Start, suhbat, personaj, profil, tarixni tozalash
│   │   ├── payment.py         # Tariflar, to'lov cheki qabul qilish, admin tasdiqlash
│   │   └── admin.py           # Statistika, broadcast, rekvizit, extra promptlar boshqaruvi
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── reply.py           # Asosiy menyu va suhbat menyusi reply tugmalari
│   │   └── inline.py          # Personaj, tarif, to'lov, admin inline tugmalari
│   └── states/
│       ├── __init__.py
│       └── user_states.py     # FSM holatlari
├── .env                       # API kalitlar va sozlamalar
├── .env.example               # Namuna sozlamalar fayli
├── main.py                    # Botni ishga tushiruvchi asosiy kirish nuqtasi
├── requirements.txt           # Kerakli Python kutubxonalari
└── README.md                  # Loyiha hujjatlari
```

---

## ⚙️ O'rnatish va Ishga Tushirish

### 1. Kutubxonalarni o'rnatish
```bash
python -m pip install -r requirements.txt
```

### 2. Sozlamalarni tekshirish (.env)
`.env` faylida barcha kalitlaringiz kiritilgan:
```env
BOT_TOKEN=9054501543:AAG0RdoLZoAVPIMCVIb3zIQW33267wswYM8
ADMIN_ID=6125160021
AI_API_KEY=AQ.Ab8RN6JmnwbEaHokQXAKNohZKpuloWqts4VVOIaC69mALo15MQ
AI_MODEL=gemini-3.5-flash-lite
FORCE_CHANNEL=
DATABASE_PATH=database.sqlite3
```

### 3. Botni ishga tushirish
```bash
python main.py
```

---

## 🐙 GitHub ga Yuklanadigan Zarur Fayllar

GitHub-ga quyidagi asosiy fayllar yuklanadi:
1. `bot/` (barcha Python kodlari, papkalari bilan)
2. `main.py`
3. `requirements.txt`
4. `.env.example`
5. `.gitignore`
6. `README.md`

> [!CAUTION]
> `.env` va `database.sqlite3` fayllarini hech qachon GitHub-ga yuklamang! Ular `.gitignore` ga kiritilgan.

---

## 🌐 Render.com ga Joylash (Deploy) Ko'rsatmasi

1. Render.com ga kiring va **New +** -> **Background Worker** tanlang (chunki bot Web Service emas, polling rejimida 24/7 ishlashi kerak).
2. GitHub repozitoriyangizni ulang.
3. Sozlamalar:
   * **Name:** `ai-chatbot-saas`
   * **Environment:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `python main.py`
4. **Environment Variables (Environment bo'limidagi Key va Value lar):**
   * `BOT_TOKEN`: `9054501543:AAG0RdoLZoAVPIMCVIb3zIQW33267wswYM8`
   * `ADMIN_ID`: `6125160021`
   * `AI_API_KEY`: `AQ.Ab8RN6JmnwbEaHokQXAKNohZKpuloWqts4VVOIaC69mALo15MQ`
   * `AI_MODEL`: `gemini-3.5-flash-lite`
   * `FORCE_CHANNEL`: `` (bo'sh yoki kanalingiz username'i)
   * `DATABASE_PATH`: `database.sqlite3`
5. **Create Background Worker** tugmasini bosing. Bot Renderda 24/7 rejimda ishga tushadi!
