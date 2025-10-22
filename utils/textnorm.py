# utils/textnorm.py
import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

NAME_RE = re.compile(r"(?:(?:ADI|AD|AD SOYAD|AD SOYADI|SOYADI|SOYAD|AD-SOYAD)\s*[:\-]?\s*)?([A-ZÇĞİÖŞÜ\s]{3,})")

def normalize_text(s: str) -> str:
    """
    OCR çıktısını normalize eder:
    - Unicode normalizasyonu
    - Yaygın OCR hatalarını düzeltir
    """
    if not s:
        return ""
    
    # Unicode normalizasyonu (NFC - Türkçe karakterler için uygun)
    s = unicodedata.normalize("NFC", s)
    
    # Sadece kritik OCR hatalarını düzelt
    # Türkçe karakterleri KORU!
    replacements = {
        "Ø": "Ö",
        "€": "E",
    }
    
    for old, new in replacements.items():
        s = s.replace(old, new)
    
    logger.debug(f"Metin normalize edildi: {len(s)} karakter")
    return s


def extract_name_block(text: str) -> str:
    """
    Kimlik OCR çıktısından ad ve soyadı birleştirerek çıkarır.
    Kimlik kartında etiket ve değer farklı satırlarda olabilir.
    """
    lines = text.splitlines()
    name = ""
    surname = ""

    for i, line in enumerate(lines):
        line_clean = normalize_text(line.strip().upper())

        # ADI/ADİ etiketi bulundu, sonraki satırlarda isim ara
        if ("ADI" in line_clean or "ADİ" in line_clean) and not ("SOYADI" in line_clean or "SOYADİ" in line_clean):
            # Aynı satırda isim var mı?
            match = re.search(r"(?:ADI|ADİ)[:\-]?\s*([A-ZÇĞİÖŞÜ\s]+)", line_clean)
            if match and match.group(1).strip():
                name = match.group(1).strip()
            else:
                # Sonraki satırlarda isim ara - sadece ADI etiketinden sonraki kısa satırları al
                name_parts = []
                for j in range(i+1, min(i+4, len(lines))):
                    next_line = normalize_text(lines[j].strip().upper())
                    # İsim olabilecek kriterler: sayı yok, çok uzun değil, parantez yok, soyad değil
                    if (next_line and not re.search(r'\d', next_line) and 
                        len(next_line.split()) <= 2 and 
                        '(' not in next_line and ')' not in next_line and
                        not any(word in next_line for word in ['GIVEN', 'NAME', 'SURNAME', 'TARIHI', 'BIRTH', 'CINSIYETI', 'DATE', 'GENDER', 'ANKARA', 'SURNAME']) and
                        len(next_line.strip()) <= 10):  # Çok uzun kelimeleri atla
                        name_parts.append(next_line.strip())
                        # Eğer 2 kelimeli bir satır bulduysak dur
                        if len(next_line.split()) >= 2:
                            break
                
                # İsim parçalarını birleştir
                if name_parts:
                    name = " ".join(name_parts)

        # SOYADI/SOYADİ etiketi bulundu, sonraki satırlarda soyad ara
        elif "SOYADI" in line_clean or "SOYADİ" in line_clean:
            # Aynı satırda soyad var mı?
            match = re.search(r"(?:SOYADI|SOYADİ)[:\-]?\s*([A-ZÇĞİÖŞÜ\s]+)", line_clean)
            if match and match.group(1).strip() and match.group(1).strip() != "SURNAME":
                surname = match.group(1).strip()
            else:
                # Sonraki satırlarda soyad ara - "SURNAME" kelimesini atla
                for j in range(i+1, min(i+4, len(lines))):
                    next_line = normalize_text(lines[j].strip().upper())
                    if (next_line and not re.search(r'\d', next_line) and 
                        len(next_line.split()) <= 3 and
                        next_line.strip() != "SURNAME"):
                        surname = next_line.strip()
                        break

        # AD SOYAD: Ali Karaca (form formatı) - OCR hatalarını da destekle
        elif any(pattern in line_clean for pattern in ["AD SOYAD", "AD SOVAD", "AD SOYADI", "AD SOVADI"]):
            # Farklı OCR hatalarını destekle
            patterns = [
                r"AD\s+(?:SOYAD|SOVAD|SOYADI|SOVADI)[:\-]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)",
                r"AD\s+(?:SOYAD|SOVAD|SOYADI|SOVADI)[:\-]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line_clean)
                if match and match.group(1).strip():
                    full_name = match.group(1).strip()
                    return clean_person_name(full_name)
            
            # Sonraki satırda isim olabilir
            if i + 1 < len(lines):
                next_line = normalize_text(lines[i + 1].strip())
                if next_line and not re.search(r'\d', next_line) and len(next_line.split()) >= 2:
                    return clean_person_name(next_line)

    full_name = f"{name} {surname}".strip()
    return clean_person_name(full_name) if len(full_name.split()) >= 2 else ""


def clean_person_name(s: str | None) -> str | None:
    """
    İsim bloğunu temizler ve standardize eder:
    - Gereksiz karakterleri kaldırır
    - Çoklu boşlukları düzeltir
    - Maksimum 4 kelimeye sınırlar (ad + ara isim + soyad)
    """
    if not s:
        return None
    
    # Çoklu boşlukları tek boşluğa indir
    s = re.sub(r"\s{2,}", " ", s.strip())
    
    # Sadece Türkçe harfler, boşluk, tire ve apostrof kalsın
    # Türkçe karakterleri KORUYORUZ (Ç, Ğ, İ, Ö, Ş, Ü)
    s = re.sub(r"[^A-ZÇĞİÖŞÜa-zçğıöşü\s\-']", "", s)
    
    # Büyük harfe çevir (Türkçe karakterlerle uyumlu)
    s = s.upper()
    
    # Kelime sayısını sınırla (4'ten fazla kelime varsa adres olabilir)
    toks = s.split()
    if len(toks) > 4:
        logger.debug(f"İsim 4 kelimeden uzun, kırpılıyor: {s}")
        toks = toks[:4]
    
    # En az 2 kelime olmalı
    if len(toks) < 2:
        logger.warning(f"İsim çok kısa: {s}")
        return None
    
    result = " ".join(toks) if toks else None
    logger.debug(f"Temizlenmiş isim: {result}")
    return result

def extract_name_from_form(text: str) -> str | None:
    """
    Başvuru formundan ad soyad bilgisini çıkarır.
    Genellikle formun alt kısmında yer aldığı için satırlar tersten taranır.
    Etiketle aynı satırda veya bir sonraki satırda olabilir.
    """
    lines = text.splitlines()

    for i in reversed(range(len(lines))):
        line_clean = normalize_text(lines[i].strip())
        line_upper = line_clean.upper()

        # Etiketle aynı satırda: "Ad Soyad: Ali Karaca"
        match_inline = re.search(
            r"(?:AD SOYAD|AD)[\s\-:]*([A-ZÇĞİÖŞÜa-zçğıöşü\s\-']{3,})",
            line_clean,
            re.IGNORECASE
        )
        if match_inline:
            name = match_inline.group(1).strip()
            return clean_person_name(name)

        # Etiket varsa, bir sonraki satırda isim olabilir
        if "AD SOYAD" in line_upper or "AD" in line_upper:
            if i + 1 < len(lines):
                next_line = normalize_text(lines[i + 1].strip())
                if not re.search(r'\d', next_line) and len(next_line.split()) >= 2:
                    return clean_person_name(next_line)

    logger.warning("Form'da isim bulunamadı")
    return None
