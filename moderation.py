import re
from typing import Tuple, Optional

INTIMATE_PATTERNS = [
    r'\b(seks|sex|intim|ehtiros|ehtirosli|quchoq|quchoqla|quchoqlay|quchoqlash|quchoqlaylik)\b',
    r'\b(o[\'ʼ`]?pish|o[\'ʼ`]?p|o[\'ʼ`]?pay|labing|labingdan|lablar|bo[\'ʼ`]?sa|bosa)\b',
    r'\b(yechin|yechintir|yechintiray|yechintirish|kiyimsiz|yalang[\'ʼ`]?och)\b',
    r'\b(yotish|yotaylik|yotvolaylik|to[\'ʼ`]?shak|karavot|bed)\b',
    r'\b(qizdir|qizdirish|issiqroq|qizib|qizit)\b',
    r'\b(ko[\'ʼ`]?krak|kokrak|ko[\'ʼ`]?kraklar|badan|tanang|tanangni)\b',
    r'\b(18\+|shaxvat|shahvat|erotik|erotika|seksual|porno)\b',
    r'\b(xohlayapman|xohlisanmi|xohlaysanmi|istayapman|istaysanmi)\b',
    r'\b(sik|am|qotoq|toshog[\'ʼ`]?|jalap|kutingga|sikish|sikaylik)\b',
    r'\b(nomer ber|raqamingni ber|uchrashaylik|ko[\'ʼ`]?rishaylik|uyingga boray)\b'
]

INTIMATE_REGEX = re.compile('|'.join(INTIMATE_PATTERNS), flags=re.IGNORECASE)

def detect_intimate_content(text: str) -> Tuple[bool, Optional[str]]:
    """
    Foydalanuvchi xabarida ehtirosli yoki 18+ kontent borligini tekshiradi.
    (topildi: bool, topilgan_soz: str)
    """
    if not text:
        return False, None
    match = INTIMATE_REGEX.search(text)
    if match:
        return True, match.group(0)
    return False, None
