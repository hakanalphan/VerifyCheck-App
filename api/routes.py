# api/routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
import os, tempfile, shutil
import logging
import traceback

from config.settings import settings
from core.models import ExtractedDocument, MatchScores, ValidateResponse
from services.ocr_service import EasyOCREngine, DocumentExtractor
from services.match_service import Matcher
from utils.tckn import is_valid_tckn

# Logging konfigürasyonu
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

def get_pipeline():
    engine = EasyOCREngine(languages=("tr","en"))
    extractor = DocumentExtractor(engine)
    matcher = Matcher(min_name_similarity=settings.min_name_similarity)
    return extractor, matcher

def _allowed(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in settings.allowed_extensions

@router.post("/validate", response_model=ValidateResponse)
async def validate(
    id_image: UploadFile = File(..., description="Kimlik (ön yüz) görseli"),
    form_image: UploadFile = File(..., description="İmzalı başvuru formu görseli"),
):
    tmp_id_path = None
    tmp_form_path = None
    
    try:
        # Dosya formatı kontrolü
        if not _allowed(id_image.filename) or not _allowed(form_image.filename):
            raise HTTPException(status_code=400, detail="Geçersiz dosya formatı. (jpg, jpeg, png, bmp, tiff)")

        # Boyut limiti kontrolü
        if (id_image.size and id_image.size > settings.max_upload_mb*1024*1024) or \
           (form_image.size and form_image.size > settings.max_upload_mb*1024*1024):
            raise HTTPException(status_code=413, detail=f"Dosya boyutu {settings.max_upload_mb}MB üstünde.")

        # Geçici dosyalara yazma
        logger.info("Dosyalar geçici klasöre yazılıyor...")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(id_image.filename)[1]) as tmp_id:
                shutil.copyfileobj(id_image.file, tmp_id)
                tmp_id_path = tmp_id.name
            logger.info(f"Kimlik dosyası yazıldı: {tmp_id_path}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(form_image.filename)[1]) as tmp_form:
                shutil.copyfileobj(form_image.file, tmp_form)
                tmp_form_path = tmp_form.name
            logger.info(f"Form dosyası yazıldı: {tmp_form_path}")
            
        except Exception as e:
            logger.error(f"Dosya yazma hatası: {e}")
            raise HTTPException(status_code=500, detail=f"Dosya yükleme hatası: {e}")

        # Pipeline oluşturma
        logger.info("OCR pipeline başlatılıyor...")
        extractor, matcher = get_pipeline()
        
        # Kimlik OCR
        logger.info(f"Kimlik OCR başlıyor: {tmp_id_path}")
        id_name, id_tckn, id_conf = extractor.extract(tmp_id_path)
        logger.info(f"Kimlik sonucu - Ad: {id_name}, TCKN: {id_tckn}, Güven: {id_conf}")
        
        # Form OCR
        logger.info(f"Form OCR başlıyor: {tmp_form_path}")
        form_name, form_tckn, form_conf = extractor.extract(tmp_form_path)
        logger.info(f"Form sonucu - Ad: {form_name}, TCKN: {form_tckn}, Güven: {form_conf}")

        # TCKN doğrulama (sadece log için, hata vermez)
        if id_tckn and not is_valid_tckn(id_tckn):
            logger.warning(f"Kimlik TCKN algoritmik doğrulamadan geçmedi: {id_tckn}")
        if form_tckn and not is_valid_tckn(form_tckn):
            logger.warning(f"Form TCKN algoritmik doğrulamadan geçmedi: {form_tckn}")

        # Eşleştirme
        logger.info("Eşleştirme yapılıyor...")
        name_similarity, tckn_match, is_valid = matcher.compare(id_name, form_name, id_tckn, form_tckn)
        logger.info(f"Eşleştirme sonucu - İsim benzerliği: {name_similarity}, TCKN eşleşmesi: {tckn_match}, Geçerli: {is_valid}")
        
        message = "Ad-Soyad ve TCKN tutarlı." if is_valid else "Eşleşme başarısız. Lütfen belgeleri kontrol edin."

        payload = ValidateResponse(
            is_valid=bool(is_valid),
            message=message,
            scores=MatchScores(
                name_similarity=name_similarity,
                tckn_match=bool(tckn_match),
                ocr_confidence_hint=max(id_conf, form_conf)
            ),
            id=ExtractedDocument(name=id_name, tckn=id_tckn, confidence=id_conf),
            form=ExtractedDocument(name=form_name, tckn=form_tckn, confidence=form_conf),
        )
        
        logger.info("İşlem başarıyla tamamlandı")
        return JSONResponse(payload.model_dump(), status_code=status.HTTP_200_OK)

    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"İşlem hatası: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        raise HTTPException(status_code=500, detail=f"İşlem hatası: {str(e)}")
    finally:
        # Geçici dosyaları temizle
        for p in (tmp_id_path, tmp_form_path):
            if p:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                        logger.debug(f"Geçici dosya silindi: {p}")
                except Exception as cleanup_err:
                    logger.warning(f"Dosya temizleme hatası ({p}): {cleanup_err}")