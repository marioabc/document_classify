import pytest
from app.services.classifier_service import DocumentClassifier
from app.models import DocumentType


@pytest.fixture
def classifier():
    """Create classifier instance for testing"""
    return DocumentClassifier()


def test_classify_grupa_krwi(classifier):
    """Test classification of blood group document"""
    text = "Wynik badania: Grupa krwi A RH+"
    doc_type, confidence, keywords = classifier.classify(text)

    assert doc_type == DocumentType.GRUPA_KRWI
    assert confidence > 0.0
    assert len(keywords) > 0


def test_classify_morfologia(classifier):
    """Test classification of morphology document"""
    text = "Morfologia krwi: WBC 7.5, RBC 4.8, Hemoglobina 14.2, Hematokryt 42%"
    doc_type, confidence, keywords = classifier.classify(text)

    assert doc_type == DocumentType.MORFOLOGIA
    assert confidence > 0.0
    assert len(keywords) > 0


def test_classify_ekg(classifier):
    """Test classification of EKG document"""
    text = "Elektrokardiogram - EKG: Rytm zatokowy, prawidłowy"
    doc_type, confidence, keywords = classifier.classify(text)

    assert doc_type == DocumentType.EKG
    assert confidence > 0.0
    assert len(keywords) > 0


def test_classify_rtg(classifier):
    """Test classification of X-ray document"""
    text = "RTG klatki piersiowej: Bez zmian patologicznych"
    doc_type, confidence, keywords = classifier.classify(text)

    assert doc_type == DocumentType.RTG_KLATKA
    assert confidence > 0.0
    assert len(keywords) > 0


def test_classify_glukoza(classifier):
    """Test classification of glucose document"""
    text = "Glukoza na czczo: 95 mg/dl"
    doc_type, confidence, keywords = classifier.classify(text)

    assert doc_type == DocumentType.GLUKOZA
    assert confidence > 0.0


def test_classify_unknown_document(classifier):
    """Test classification of unknown document"""
    text = "To jest kompletnie losowy tekst bez sensu medycznego"
    doc_type, confidence, keywords = classifier.classify(text)

    assert doc_type == DocumentType.INNE
    assert confidence == 0.0


def test_extract_dates_polish_format(classifier):
    """Test date extraction in Polish format"""
    text = "Data badania: 15.11.2024"
    dates = classifier.extract_dates(text)

    assert len(dates) > 0
    assert "15.11.2024" in dates


def test_extract_dates_iso_format(classifier):
    """Test date extraction in ISO format"""
    text = "Data: 2024-11-15"
    dates = classifier.extract_dates(text)

    assert len(dates) > 0
    assert "2024-11-15" in dates


def test_extract_dates_month_name(classifier):
    """Test date extraction with month name"""
    text = "Wykonano dnia 15 listopada 2024"
    dates = classifier.extract_dates(text)

    assert len(dates) > 0


def test_extract_multiple_dates(classifier):
    """Test extraction of multiple dates"""
    text = "Badanie z dnia 15.11.2024, kontrolne: 2024-12-20"
    dates = classifier.extract_dates(text)

    assert len(dates) >= 2


def test_confidence_calculation(classifier):
    """Test that confidence is between 0 and 1"""
    text = "Morfologia krwi: WBC, RBC, Hemoglobina, Leukocyty, Erytrocyty"
    doc_type, confidence, keywords = classifier.classify(text)

    assert 0.0 <= confidence <= 1.0


def test_multiple_keywords_increase_confidence(classifier):
    """Test that more keywords increase confidence"""
    text_few = "EKG"
    text_many = "EKG elektrokardiogram serce rytm"

    _, confidence_few, _ = classifier.classify(text_few)
    _, confidence_many, _ = classifier.classify(text_many)

    assert confidence_many >= confidence_few
