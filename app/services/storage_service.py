import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import BinaryIO
from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        # Create directories if they don't exist
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(settings.PROCESSED_DIR).mkdir(parents=True, exist_ok=True)

    def save_uploaded_file(self, file: BinaryIO, filename: str) -> tuple[str, str]:
        """
        Save uploaded file to temporary storage
        Returns: (file_id, file_path)
        """
        file_id = str(uuid.uuid4())
        file_extension = Path(filename).suffix

        # Validate extension
        if file_extension.lstrip('.').lower() not in settings.allowed_extensions_list:
            raise ValueError(f"File extension {file_extension} not allowed")

        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{file_extension}")

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file, buffer)

            logger.info(f"File saved: {file_path}")
            return file_id, file_path

        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise

    def move_to_processed(self, file_path: str, document_type: str) -> str:
        """
        Move processed file to permanent storage
        Returns: new_file_path
        """
        try:
            filename = Path(file_path).name
            type_dir = os.path.join(settings.PROCESSED_DIR, document_type)
            Path(type_dir).mkdir(parents=True, exist_ok=True)

            new_path = os.path.join(type_dir, filename)
            shutil.move(file_path, new_path)

            logger.info(f"File moved to: {new_path}")
            return new_path

        except Exception as e:
            logger.error(f"Error moving file: {str(e)}")
            raise

    def cleanup_temp_file(self, file_path: str):
        """
        Remove temporary file
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file removed: {file_path}")
        except Exception as e:
            logger.error(f"Error removing temporary file: {str(e)}")


# Singleton instance
storage_service = StorageService()
