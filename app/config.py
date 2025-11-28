from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Medical Document Classifier"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PORT: int = 8000

    # OCR
    OCR_LANGUAGES: str = "pl,en"
    OCR_GPU: bool = False

    # LLM Classifier (Ollama)
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # File Storage
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,png,jpg,jpeg,tiff"
    UPLOAD_DIR: str = "/app/data/uploads"
    PROCESSED_DIR: str = "/app/data/processed"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def ocr_languages_list(self) -> List[str]:
        return [lang.strip() for lang in self.OCR_LANGUAGES.split(",")]

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
