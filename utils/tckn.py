import re
import logging

logger = logging.getLogger(__name__)

TCKN_RE = re.compile(r"\b[1-9]\d{10}\b")

def extract_tckn(text: str) -> str | None:
    """
    Metinden TCKN çıkarır.
    TCKN formatı: 11 haneli, ilk hane 0 olamaz.
    """
    if not text:
        return None
    
    m = TCKN_RE.search(text)
    if m:
        tckn = m.group(0)
        logger.debug(f"TCKN bulundu: {tckn}")
        return tckn
    
    logger.debug("TCKN bulunamadı")
    return None

def is_valid_tckn(num: str) -> bool:
    """
    TCKN algoritmik doğrulaması.
    Kurallar:
    - 11 haneli olmalı
    - İlk hane 0 olamaz
    - 10. hane: ((1+3+5+7+9) * 7 - (2+4+6+8)) mod 10
    - 11. hane: (1+2+3+4+5+6+7+8+9+10) mod 10
    """
    try:
       
        if not num or not isinstance(num, str):
            logger.debug(f"TCKN geçersiz: boş veya string değil")
            return False
        
        if not num.isdigit():
            logger.debug(f"TCKN geçersiz: sayısal değil - {num}")
            return False
        
        if len(num) != 11:
            logger.debug(f"TCKN geçersiz: 11 haneli değil - {num} (uzunluk: {len(num)})")
            return False
        
        if num[0] == "0":
            logger.debug(f"TCKN geçersiz: ilk hane 0 - {num}")
            return False
        
        # Algoritmik doğrulama
        digits = [int(c) for c in num]
        
        # 10. hane kontrolü
        d10 = ((sum(digits[0:9:2]) * 7) - sum(digits[1:8:2])) % 10
        if d10 != digits[9]:
            logger.debug(f"TCKN geçersiz: 10. hane uyumsuz - {num} (beklenen: {d10}, mevcut: {digits[9]})")
            return False
        
        # 11. hane kontrolü
        d11 = sum(digits[:10]) % 10
        if d11 != digits[10]:
            logger.debug(f"TCKN geçersiz: 11. hane uyumsuz - {num} (beklenen: {d11}, mevcut: {digits[10]})")
            return False
        
        logger.debug(f"TCKN geçerli: {num}")
        return True
        
    except Exception as e:
        logger.error(f"TCKN doğrulama hatası: {e}")
        return False
