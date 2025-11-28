#!/usr/bin/env python3
import sys
import os

# Set environment variable for local testing
os.environ['OLLAMA_URL'] = 'http://localhost:11434'

sys.path.insert(0, '.')

from app.services.ocr_service import ocr_service
from app.services.classifier_service import classifier_service

# Test the problematic file
file_path = "samples/wzw_typ_b.png"

print(f"\n=== Analyzing: {file_path} ===\n")

# Extract text
extracted_text, lines = ocr_service.extract_text(file_path)

print("--- Extracted Text ---")
print(extracted_text)
print("\n--- Text Lines ---")
for i, line in enumerate(lines, 1):
    print(f"{i}. {line}")

# Classify
document_type, confidence, keywords_found = classifier_service.classify(extracted_text)

print("\n--- Classification Result ---")
print(f"Type: {document_type}")
print(f"Confidence: {confidence:.2f}")
print(f"Keywords found: {keywords_found}")
print("\n" + "="*60)
