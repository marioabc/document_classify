from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
import time
import logging
import requests
from datetime import datetime

from app.models import (
    DocumentUploadResponse,
    BatchUploadResponse,
    DocumentClassificationResult,
    DocumentType
)
from app.services.ocr_service import ocr_service
from app.services.classifier_service import classifier_service
from app.services.storage_service import storage_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Required documents list
REQUIRED_DOCUMENTS = [
    DocumentType.GRUPA_KRWI,
    DocumentType.MORFOLOGIA,
    DocumentType.APTT,
    DocumentType.PT_INR,
    DocumentType.EKG,
    DocumentType.RTG_KLATKA,
]


@router.post("/classify", response_model=DocumentUploadResponse)
async def classify_document(file: UploadFile = File(...)):
    """
    Classify a single medical document
    """
    start_time = time.time()
    file_path = None

    try:
        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
            )

        # Save uploaded file
        file_id, file_path = storage_service.save_uploaded_file(file.file, file.filename)

        # Extract text with OCR
        logger.info(f"Processing document: {file.filename}")
        extracted_text, _ = ocr_service.extract_text(file_path)

        # Classify document
        document_type, confidence, keywords_found = classifier_service.classify(extracted_text)

        # Extract dates
        dates = classifier_service.extract_dates(extracted_text)

        # Move to processed directory
        storage_service.move_to_processed(file_path, document_type.value)

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Create classification result
        classification = DocumentClassificationResult(
            document_type=document_type,
            confidence=confidence,
            keywords_found=keywords_found,
            extracted_text=extracted_text[:500],  # First 500 chars
            extracted_dates=dates,
            metadata={}
        )

        response = DocumentUploadResponse(
            id=file_id,
            filename=file.filename,
            file_size=file_size,
            upload_timestamp=datetime.utcnow(),
            classification=classification,
            processing_time_ms=processing_time
        )

        logger.info(f"Document classified successfully: {document_type} ({confidence:.2f})")
        return response

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        if file_path:
            storage_service.cleanup_temp_file(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify/merged", response_model=DocumentUploadResponse)
async def classify_merged_document(files: List[UploadFile] = File(...)):
    """
    Classify multiple files as ONE document (e.g., multi-page scan)
    - Performs OCR on all files
    - Merges extracted text
    - Returns single classification
    """
    start_time = time.time()
    temp_files = []

    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        logger.info(f"Processing {len(files)} files as merged document")

        # Extract text from all files
        all_text_parts = []
        total_file_size = 0
        filenames = []

        for file in files:
            # Validate file size
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            total_file_size += file_size
            filenames.append(file.filename)

            if file_size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
                )

            # Save temporary file
            file_id, file_path = storage_service.save_uploaded_file(file.file, file.filename)
            temp_files.append((file_id, file_path))

            # Extract text with OCR
            logger.info(f"  - Processing {file.filename}")
            extracted_text, _ = ocr_service.extract_text(file_path)
            all_text_parts.append(extracted_text)

        # Merge all text
        merged_text = ' '.join(all_text_parts)
        logger.info(f"Merged text from {len(files)} files: {len(merged_text)} characters")

        # Classify merged document
        document_type, confidence, keywords_found = classifier_service.classify(merged_text)

        # Extract dates
        dates = classifier_service.extract_dates(merged_text)

        # Move first file to processed directory (represents the merged document)
        main_file_id, main_file_path = temp_files[0]
        storage_service.move_to_processed(main_file_path, document_type.value)

        # Clean up other temporary files
        for file_id, file_path in temp_files[1:]:
            storage_service.cleanup_temp_file(file_path)

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Create classification result
        classification = DocumentClassificationResult(
            document_type=document_type,
            confidence=confidence,
            keywords_found=keywords_found,
            extracted_text=merged_text[:500],  # First 500 chars
            extracted_dates=dates,
            metadata={
                "merged_files": filenames,
                "total_files": len(files)
            }
        )

        response = DocumentUploadResponse(
            id=main_file_id,
            filename=f"merged_{len(files)}_files",
            file_size=total_file_size,
            upload_timestamp=datetime.utcnow(),
            classification=classification,
            processing_time_ms=processing_time
        )

        logger.info(f"Merged document classified: {document_type} ({confidence:.2f})")
        return response

    except Exception as e:
        logger.error(f"Error processing merged document: {str(e)}")
        # Cleanup all temporary files
        for _, file_path in temp_files:
            storage_service.cleanup_temp_file(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify/batch", response_model=BatchUploadResponse)
async def classify_documents_batch(files: List[UploadFile] = File(...)):
    """
    Classify multiple medical documents and check completeness
    """
    results = []
    failed = 0

    for file in files:
        try:
            result = await classify_document(file)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {str(e)}")
            failed += 1

    # Check for missing required documents
    classified_types = [r.classification.document_type for r in results]
    missing_docs = [
        doc.value for doc in REQUIRED_DOCUMENTS
        if doc not in classified_types
    ]

    completeness = ((len(REQUIRED_DOCUMENTS) - len(missing_docs)) / len(REQUIRED_DOCUMENTS)) * 100

    return BatchUploadResponse(
        total_documents=len(files),
        successfully_processed=len(results),
        failed=failed,
        results=results,
        missing_required_documents=missing_docs,
        completeness_percentage=completeness
    )


def send_classification_callback(element_id: str, document_type: str, confidence: float):
    """
    Send classification result to external API as callback
    """
    callback_url = f"http://localhost:9091/public/api/v1/checklists/elements/{element_id}/ai-validate"

    payload = {
        "document_type": document_type,
        "confidence": confidence
    }

    try:
        logger.info(f"Sending callback to {callback_url}")
        logger.info(f"Payload: {payload}")

        response = requests.post(
            callback_url,
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code in [200, 201, 204]:
            logger.info(f"Callback sent successfully. Status: {response.status_code}")
        else:
            logger.error(f"Callback failed with status {response.status_code}: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending callback to {callback_url}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error sending callback: {str(e)}")


def process_merged_document_async(element_id: str, files_data: List[tuple]):
    """
    Process merged document classification in background and send callback
    files_data: List of tuples (file_id, file_path, filename)
    """
    temp_files = []

    try:
        logger.info(f"Background processing started for element {element_id}")

        # Extract text from all files
        all_text_parts = []

        for file_id, file_path, filename in files_data:
            temp_files.append((file_id, file_path))

            # Extract text with OCR
            logger.info(f"  - Processing {filename}")
            extracted_text, _ = ocr_service.extract_text(file_path)
            all_text_parts.append(extracted_text)

        # Merge all text
        merged_text = ' '.join(all_text_parts)
        logger.info(f"Merged text from {len(files_data)} files: {len(merged_text)} characters")

        # Classify merged document
        document_type, confidence, keywords_found = classifier_service.classify(merged_text)
        logger.info(f"Classification result: {document_type} ({confidence:.2f})")

        # Move first file to processed directory
        main_file_id, main_file_path = temp_files[0]
        storage_service.move_to_processed(main_file_path, document_type.value)

        # Clean up other temporary files
        for file_id, file_path in temp_files[1:]:
            storage_service.cleanup_temp_file(file_path)

        # Send callback with classification result
        send_classification_callback(element_id, document_type.value, confidence)

        logger.info(f"Background processing completed for element {element_id}")

    except Exception as e:
        logger.error(f"Error in background processing for element {element_id}: {str(e)}")
        # Cleanup all temporary files on error
        for _, file_path in temp_files:
            try:
                storage_service.cleanup_temp_file(file_path)
            except:
                pass


@router.post("/classify/merged/{element_id}", status_code=201)
async def classify_merged_document_async(
    element_id: str,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Classify multiple files as ONE document (async version with callback)
    - Returns 201 immediately
    - Performs OCR and classification in background
    - Sends POST callback to external API with result

    Callback URL: http://app:9091/public/api/v1/checklists/elements/{element_id}/ai-validate
    Callback payload: {"document_type": "DOC_BADANIE_LK", "confidence": 0.95}
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        logger.info(f"Received {len(files)} files for async processing (element: {element_id})")

        # Save all files temporarily
        files_data = []

        for file in files:
            # Validate file size
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)

            if file_size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
                )

            # Save temporary file
            file_id, file_path = storage_service.save_uploaded_file(file.file, file.filename)
            files_data.append((file_id, file_path, file.filename))
            logger.info(f"  - Saved {file.filename} temporarily")

        # Schedule background processing
        background_tasks.add_task(process_merged_document_async, element_id, files_data)

        logger.info(f"Background task scheduled for element {element_id}")

        # Return immediate response
        return {
            "status": "accepted",
            "message": "Document processing started",
            "element_id": element_id,
            "files_count": len(files)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting document for async processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
