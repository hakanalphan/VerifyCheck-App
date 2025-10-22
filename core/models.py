from pydantic import BaseModel, Field

class ExtractedDocument(BaseModel):
    name: str | None = None
    tckn: str | None = None
    confidence: float = 0.0
    source: str = "easyocr"

class MatchScores(BaseModel):
    name_similarity: int
    tckn_match: bool
    ocr_confidence_hint: float

class ValidateResponse(BaseModel):
    is_valid: bool
    message: str
    scores: MatchScores
    id: ExtractedDocument
    form: ExtractedDocument
