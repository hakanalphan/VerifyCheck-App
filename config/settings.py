from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = Field(default="VerifyCheck")
    environment: str = Field(default="dev")
    allowed_extensions: set[str] = Field(default_factory=lambda: {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"})
    min_name_similarity: int = 80
    min_ocr_confidence: float = 0.35
    max_upload_mb: int = 10

    class Config:
        env_prefix = "KYC_"
        case_sensitive = False

settings = Settings()
