# services/ocr_service.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Tuple, Optional
import easyocr
import numpy as np
import cv2
import logging
import os

from utils.textnorm import extract_name_block, clean_person_name, normalize_text
from utils.tckn import extract_tckn

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float

class EasyOCREngine:
    """SRP: sadece OCR'den sorumlu. OCP: başka motorlar için benzer arayüz yazılabilir."""
    def __init__(self, languages: Iterable[str] = ("tr","en")):
        logger.info(f"EasyOCR başlatılıyor - Diller: {languages}")
        try:
            self.reader = easyocr.Reader(list(languages), gpu=False, verbose=False)
            logger.info("EasyOCR başarıyla yüklendi")
        except Exception as e:
            logger.error(f"EasyOCR başlatma hatası: {e}", exc_info=True)
            raise

    def read_text(self, image_path: str) -> OcrResult:
        """Görsel dosyasından metin çıkarır."""
        try:
            logger.info(f"Görsel okunuyor: {image_path}")
            
            # Dosya varlığını kontrol et
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Dosya bulunamadı: {image_path}")
            
            # Dosyayı bytes olarak oku (Türkçe karakter sorununu çözer)
            with open(image_path, 'rb') as f:
                img_bytes = f.read()
            
            if not img_bytes:
                raise ValueError(f"Dosya boş: {image_path}")
            
            # Numpy array'e dönüştür
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError(f"Görsel decode edilemedi: {image_path}")
            
            logger.info(f"Görsel boyutu: {img.shape}")
            
            # Basit önişleme: gri + bilateral filtre
            try:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                gray = cv2.bilateralFilter(gray, 9, 75, 75)
            except Exception as e:
                logger.warning(f"Görsel önişleme hatası, orijinal kullanılıyor: {e}")
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # OCR işlemi
            logger.info("EasyOCR çalıştırılıyor...")
            try:
                # reader.readtext returns [ [bbox, text, conf], ... ]
                lines = self.reader.readtext(gray, detail=1, paragraph=False)
            except Exception as e:
                logger.error(f"EasyOCR readtext hatası: {e}", exc_info=True)
                # Boş sonuç dön
                return OcrResult(text="", confidence=0.0)
            
            texts, confs = [], []
            for item in lines:
                if len(item) >= 3:  # [bbox, text, conf] formatı kontrolü
                    bbox, t, c = item[0], item[1], item[2]
                    texts.append(str(t))
                    confs.append(float(c))
                    logger.debug(f"OCR satırı: {t} (güven: {c:.2f})")
            
            full_text = "\n".join(texts)
            conf = float(np.mean(confs)) if confs else 0.0
            
            logger.info(f"OCR tamamlandı - {len(texts)} satır, ortalama güven: {conf:.2f}")
            if full_text:
                logger.debug(f"Çıkarılan metin (ilk 200 karakter):\n{full_text[:200]}")
            else:
                logger.warning("OCR hiç metin çıkaramadı!")
            
            return OcrResult(text=full_text, confidence=conf)
            
        except Exception as e:
            logger.error(f"OCR hatası ({image_path}): {e}", exc_info=True)
            # Hata durumunda boş sonuç dön (crash yerine)
            return OcrResult(text="", confidence=0.0)

class DocumentExtractor:
    """Belgeden isim ve TCKN çıkarır."""
    def __init__(self, engine: EasyOCREngine):
        self.engine = engine

    def extract(self, image_path: str) -> Tuple[Optional[str], Optional[str], float]:
        """
        Belgeden isim ve TCKN çıkarır.
        Returns: (name, tckn, confidence)
        Her zaman 3 değer döner (None, None, 0.0 bile olsa)
        """
        try:
            logger.info(f"Belge işleniyor: {image_path}")
            
            # OCR çalıştır
            res = self.engine.read_text(image_path)
            
            if not res.text:
                logger.warning("OCR boş metin döndü")
                return None, None, 0.0
            
            # Metni normalize et
            t = normalize_text(res.text)
            logger.debug(f"Normalize edilmiş metin (ilk 200 karakter):\n{t[:200]}")
            
            # İsim bloğunu çıkar
            name_blk = extract_name_block(t)
            logger.info(f"İsim bloğu: {name_blk}")
            
            # İsmi temizle
            name = clean_person_name(name_blk)
            logger.info(f"Temizlenmiş isim: {name}")
            
            # TCKN çıkar
            tckn = extract_tckn(t)
            logger.info(f"TCKN: {tckn}")
            
            # Her zaman 3 değer dön
            return name, tckn, res.confidence
            
        except Exception as e:
            logger.error(f"Belge çıkarma hatası ({image_path}): {e}", exc_info=True)
            # Hata durumunda bile 3 değer dön
            return None, None, 0.0