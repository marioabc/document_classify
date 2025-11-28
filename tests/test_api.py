from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_simple_health():
    """Test simple health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_classify_document():
    """Test document classification endpoint"""
    # Note: This test requires a real image file
    # For production, you should create test fixtures with sample medical documents

    # Example with mock file (uncomment when you have test images):
    # with open("tests/fixtures/test_document.png", "rb") as f:
    #     response = client.post(
    #         "/api/v1/classify",
    #         files={"file": ("test.png", f, "image/png")}
    #     )
    #
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert "classification" in data
    #     assert "document_type" in data["classification"]
    #     assert "confidence" in data["classification"]
    pass


def test_classify_document_file_too_large():
    """Test file size validation"""
    # Create a mock large file
    large_content = b"0" * (11 * 1024 * 1024)  # 11MB (over limit)

    response = client.post(
        "/api/v1/classify",
        files={"file": ("large.png", large_content, "image/png")}
    )

    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


def test_list_documents():
    """Test listing documents endpoint"""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_documents_with_pagination():
    """Test document listing with pagination"""
    response = client.get("/api/v1/documents?skip=0&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_document_not_found():
    """Test getting non-existent document"""
    response = client.get("/api/v1/documents/nonexistent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
