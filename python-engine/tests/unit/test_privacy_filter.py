"""Unit tests for PrivacyFilter blacklist, whitelist scan, and path stripping."""

import os
from src.infrastructure.privacy_filter import PrivacyFilter


def test_blacklist_detection():
    pf = PrivacyFilter()

    # Should be blacklisted
    assert pf.is_blacklisted(".env") is True
    assert pf.is_blacklisted(".env.local") is True
    assert pf.is_blacklisted("C:/Users/test/.ssh/id_rsa") is True
    assert pf.is_blacklisted("passwords.txt") is True
    assert pf.is_blacklisted("sifreler.docx") is True
    assert pf.is_blacklisted("my_api_key.json") is True
    assert pf.is_blacklisted("game.exe") is True
    assert pf.is_blacklisted("system.dll") is True

    # Should NOT be blacklisted
    assert pf.is_blacklisted("Ders_Notlari.pdf") is False
    assert pf.is_blacklisted("proje_sunum.pptx") is False
    assert pf.is_blacklisted("tatil_fotograflari") is False
    assert pf.is_blacklisted("odev.txt") is False


def test_filter_names_strips_paths_and_limits():
    pf = PrivacyFilter(max_items=3)

    raw_items = [
        "C:\\Users\\John\\Desktop\\odev.txt",
        "C:\\Users\\John\\Desktop\\.env",
        "C:\\Users\\John\\Documents\\secret_token.txt",
        "C:\\Users\\John\\Documents\\proje",
        "C:\\Users\\John\\Downloads\\kitap.epub",
        "C:\\Users\\John\\Downloads\\fazla_dosya.txt",
    ]

    clean = pf.filter_names(raw_items)
    assert ".env" not in clean
    assert "secret_token.txt" not in clean
    assert clean == ["odev.txt", "proje", "kitap.epub"]
    # Ensure max_items respected
    assert len(clean) == 3
