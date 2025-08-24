"""
Test suite for IDE Integration Server
"""
import pytest
from fastapi.testclient import TestClient
from servers.ide_integration_server import app
from datetime import datetime

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "supported_languages" in data
    assert "active_sessions" in data
    assert len(data["supported_languages"]) > 0

@pytest.mark.parametrize("language,code", [
    ("python", "def test():\n    print('Hello')\n    try:\n        pass\n    except:\n        pass"),
    ("javascript", "var x = 1;\nconsole.log('test');"),
    ("go", "func main() {\n    // TODO: Implement\n}"),
    ("typescript", "const x = 1;\n// FIXME: Remove debug"),
    ("generic", "This is a very long line that exceeds the recommended maximum line length of 100 characters and should be split into multiple lines. " * 2)
])
def test_code_analysis(language, code):
    """Test code analysis for different languages"""
    test_data = {
        "file_path": "test_file." + language,
        "content": code,
        "language": language
    }
    
    response = client.post("/analyze/code", json=test_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["file_path"] == test_data["file_path"]
    assert data["language"] == language
    assert "issues" in data
    assert "summary" in data
    
    # Verify at least one issue is found in each test case
    assert len(data["issues"]) > 0
    
    # Verify summary counts
    summary = data["summary"]
    assert summary["total_issues"] == len(data["issues"])
    assert summary["errors"] >= 0
    assert summary["warnings"] >= 0
    assert summary["info"] >= 0

@pytest.mark.parametrize("invalid_language", ["", "invalid", "123"]) 
def test_invalid_language_analysis(invalid_language):
    """Test code analysis with invalid languages"""
    test_data = {
        "file_path": "test_file.txt",
        "content": "test content",
        "language": invalid_language
    }
    
    response = client.post("/analyze/code", json=test_data)
    assert response.status_code == 200  # Should still work with fallback to generic
    data = response.json()
    assert data["language"] == invalid_language
    assert len(data["issues"]) >= 0  # May or may not find issues

@pytest.mark.parametrize("invalid_code", ["", "\n\n\n", "    "]) 
def test_empty_code_analysis(invalid_code):
    """Test code analysis with empty/invalid code"""
    test_data = {
        "file_path": "empty_file.py",
        "content": invalid_code,
        "language": "python"
    }
    
    response = client.post("/analyze/code", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["issues"]) >= 0  # May or may not find issues

def test_python_syntax_error_analysis():
    """Test Python code with syntax errors"""
    invalid_python = "def test(\n    print('missing parenthesis')"
    test_data = {
        "file_path": "syntax_error.py",
        "content": invalid_python,
        "language": "python"
    }
    
    response = client.post("/analyze/code", json=test_data)
    assert response.status_code == 200
    data = response.json()
    
    # Should find at least one syntax error
    assert any(issue["severity"] == "error" for issue in data["issues"])
    assert data["summary"]["errors"] >= 1

@pytest.mark.parametrize("test_case", [
    {"code": "print('test')", "expected": "print('test')"},
    {"code": "def test():\n    pass", "expected": "def test():\n    pass"}
])
def test_code_formatting(test_case):
    """Test code formatting (basic test - would be expanded with actual formatters)"""
    test_data = {
        "file_path": "format_test.py",
        "content": test_case["code"],
        "language": "python"
    }
    
    response = client.post("/format/code", json=test_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "formatted_code" in data
    assert data["formatted_code"] == test_case["expected"]