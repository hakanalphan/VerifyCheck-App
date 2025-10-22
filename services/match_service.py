from rapidfuzz import fuzz
import logging

logger = logging.getLogger(__name__)

class Matcher:
    """AD-SOYAD ve TCKN için eşleştirme skoru üretir."""
    def __init__(self, min_name_similarity: int = 80):
        self.min_name_similarity = min_name_similarity
        logger.info(f"Matcher başlatıldı - Minimum benzerlik: {min_name_similarity}")

    def compare(self, id_name: str|None, form_name: str|None, id_tckn: str|None, form_tckn: str|None):
        """
        İki belgedeki isim ve TCKN'yi karşılaştırır.
        Returns: (name_similarity_score, tckn_match, is_valid)
        """
        logger.info(f"Eşleştirme yapılıyor:")
        logger.info(f"  Kimlik - İsim: {id_name}, TCKN: {id_tckn}")
        logger.info(f"  Form - İsim: {form_name}, TCKN: {form_tckn}")
        
        # İsim benzerliği için
        name_sim = fuzz.token_set_ratio(id_name or "", form_name or "")
        logger.info(f"İsim benzerlik skoru: {name_sim}")
        
        # TCKN 
        tckn_ok = (id_tckn is not None and form_tckn is not None and id_tckn == form_tckn)
        logger.info(f"TCKN eşleşmesi: {tckn_ok}")
        
        #  geçerlilik için
        is_valid = (name_sim >= self.min_name_similarity) and tckn_ok
        logger.info(f"Sonuç: {'✓ GEÇERLİ' if is_valid else '✗ GEÇERSİZ'}")
        
        return int(name_sim), bool(tckn_ok), bool(is_valid)
