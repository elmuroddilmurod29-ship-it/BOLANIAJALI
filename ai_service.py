import asyncio
import logging
from typing import Optional
from google import genai
from google.genai import types
from bot.config import AI_API_KEY, AI_MODEL
from bot.database.db import db

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, api_key: str = AI_API_KEY, default_model: str = AI_MODEL):
        self.api_key = api_key
        self.default_model = default_model
        # Fallback modellari (agar asosiy modelda vaqtinchalik 503 xatosi bo'lsa)
        self.fallback_models = [default_model, "gemini-3.1-flash-lite", "gemini-2.5-pro"]
        self.client = genai.Client(api_key=self.api_key)

    async def generate_response(
        self,
        user_id: int,
        user_message: str,
        character: str = "female",
        session_id: Optional[int] = None
    ) -> str:
        """
        AI bilan xavfsiz va izolyatsiya qilingan suhbat:
        1. Faqat shu sessiya (user_id yoki group chat_id) xotirasi olinadi.
        2. DB dan Base Prompt + Extra Promptlar birlashtirilib tizim yo'riqnomasi tuziladi.
        3. Gemini API ga so'rov yuboriladi.
        4. Javob olingach, so'rov va javob DB xotirasiga yoziladi.
        """
        ctx_id = session_id if session_id is not None else user_id

        # 1. Tizim ko'rsatmasini (System Prompt) tayyorlash
        system_instruction = await db.build_full_system_prompt(character)

        # 2. Faqatgina ushbu kontekstning (user yoki guruh) oldingi xabarlarini olish (Memory Isolation)
        history = await db.get_chat_history(user_id=ctx_id, limit=10)

        # 3. Gemini formatidagi contents ro'yxatini shakllantirish
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        # Yangi xabarni qo'shish
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)]
            )
        )

        # 4. API so'rovini yuborish (bir necha model yoki urinish bilan)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=2048,
        )

        response_text: Optional[str] = None
        last_error = None

        for model_name in self.fallback_models:
            for attempt in range(2):
                try:
                    response = await self.client.aio.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config
                    )
                    if response and response.text:
                        response_text = response.text.strip()
                        break
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"AI generate_content xatoligi (model: {model_name}, urinish: {attempt+1}): {e}"
                    )
                    await asyncio.sleep(1)

            if response_text:
                break

        if not response_text:
            logger.error(f"AI javob bera olmadi. Oxirgi xatolik: {last_error}")
            return (
                "Kechirasiz, sun'iy intellekt xizmatida vaqtinchalik texnik yuklama kuzatilmoqda. "
                "Iltimos, bir necha daqiqadan so'ng qayta urinib ko'ring."
            )

        # 5. Xotirani bazaga yozish (Faqat muvaffaqiyatli javob bo'lganda)
        try:
            await db.add_message(user_id=ctx_id, role="user", content=user_message)
            await db.add_message(user_id=ctx_id, role="model", content=response_text)
        except Exception as e:
            logger.error(f"Xotirani bazaga saqlashda xatolik: {e}")

        return response_text

# Global yagona AIService instansiyasi
ai_service = AIService()
