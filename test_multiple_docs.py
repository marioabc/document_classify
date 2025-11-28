#!/usr/bin/env python3
import sys
import os
import glob

# Set environment variable for local testing
os.environ['OLLAMA_URL'] = 'http://localhost:11434'

sys.path.insert(0, '.')

from app.services.ocr_service import ocr_service
from app.services.classifier_service import classifier_service

# Test all files in samples directory
sample_files = glob.glob("samples/*.png") + glob.glob("samples/*.jpg") + glob.glob("samples/*.webp") + glob.glob("samples/*.avif")

print("\n" + "="*80)
print("TESTING CLASSIFIER ON MULTIPLE DOCUMENTS")
print("="*80 + "\n")

results = []

for file_path in sorted(sample_files):
    filename = os.path.basename(file_path)
    print(f"\n--- Testing: {filename} ---")

    try:
        # Extract text
        extracted_text, _ = ocr_service.extract_text(file_path)

        # Classify
        document_type, confidence, keywords_found = classifier_service.classify(extracted_text)

        result = {
            'file': filename,
            'type': document_type.value,
            'confidence': confidence,
            'keywords': keywords_found[:3]  # First 3 keywords
        }
        results.append(result)

        print(f"Type: {document_type.value}")
        print(f"Confidence: {confidence:.2f}")
        print(f"Keywords: {keywords_found[:3]}")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        results.append({
            'file': filename,
            'type': 'ERROR',
            'confidence': 0.0,
            'keywords': [str(e)]
        })

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"{'File':<40} {'Type':<30} {'Conf':<8}")
print("-"*80)

for r in results:
    print(f"{r['file']:<40} {r['type']:<30} {r['confidence']:.2f}")

print("="*80 + "\n")
