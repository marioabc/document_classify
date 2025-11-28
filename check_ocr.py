#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.services.ocr_service import ocr_service

files_to_check = [
    "samples/aptt.png",
    "samples/zaswiadczenie_internista.png",
    "samples/zaswiadczenie_kardiolog.png",
    "samples/rtg_klatka2.webp"
]

for file_path in files_to_check:
    print(f"\n{'='*80}")
    print(f"File: {file_path}")
    print('='*80)

    try:
        extracted_text, lines = ocr_service.extract_text(file_path)
        print(f"\nExtracted text ({len(extracted_text)} chars):")
        print(extracted_text[:500])  # First 500 chars
        print("\n")
    except Exception as e:
        print(f"ERROR: {e}")
