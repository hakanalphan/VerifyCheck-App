# KYC Doğrulama PoC — SOLID Mimari (FastAPI + EasyOCR)

**Amaç:** Kimlik (ön yüz) ve imzalı başvuru formundan OCR ile `Ad Soyad` ve `TCKN` çıkarıp tutarlılığı denetler.

## Klasörleme
```
config/   -> Settings (pydantic-settings), env ile ayarlar
core/     -> Pydantic modelleri (response/request)
services/ -> EasyOCR motoru ve eşleştirme servisi
utils/    -> TCKN validasyonu, metin normalizasyonu
api/      -> FastAPI router'ları
templates/-> index.html
static/   -> CSS vb.
main.py   -> FastAPI app montajı
```

## Çalıştırma (Geliştirme)
```bash
pip install -r requirements.txt
uvicorn main:app --reload
# http://127.0.0.1:8000
```

## Docker
```bash
docker build -t kyc-poc .
docker run --rm -p 8000:8000 kyc-poc
# veya
docker compose up --build
```

## Ortam Değişkenleri (örn. docker-compose)
- `KYC_MIN_NAME_SIMILARITY` (int, default: 80)
- `KYC_MIN_OCR_CONFIDENCE` (float, default: 0.35)
- `KYC_MAX_UPLOAD_MB` (int, default: 10)

## Hata Yüzeyi (UI)
- `index.html`′de üstte **kırmızı hata kutusu** gösterilir.
- Başarılı doğrulamada **yeşil kutu** ve JSON sonuç görünür.

## Notlar
- EasyOCR CPU modda çalışır; GPU için container imajı + Torch CUDA gerekir.
- TCKN algoritması aktiftir (10. ve 11. hane kontrolü).
- Türkçe metinlerde diakritik/uppercase normalizasyonu yapılır.
```

# Güvenlik
- Yüklenen dosyalar geçici dizinde tutulur ve işlem sonunda silinir.
- Üretimde HTTPS ve WAF önerilir; loglarda PII maskeleyin.
