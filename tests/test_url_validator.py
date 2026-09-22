import pytest
from ingestion.url_validator import is_valid_url, is_ssrf_safe

def test_is_valid_url():
    assert is_valid_url("https://example.com") is True
    assert is_valid_url("http://google.com/path?query=1") is True
    assert is_valid_url("ftp://invalid-scheme.com") is False
    assert is_valid_url("not_a_url") is False
    assert is_valid_url("") is False

def test_is_ssrf_safe():
    assert is_ssrf_safe("http://127.0.0.1") is False
    assert is_ssrf_safe("http://localhost") is False
    assert is_ssrf_safe("http://192.168.1.1") is False
    assert is_ssrf_safe("http://10.0.0.1") is False
    assert is_ssrf_safe("https://example.com") is True
