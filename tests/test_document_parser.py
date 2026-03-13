import pytest

from src.services.document_parser import DocumentParser


def test_parse_markdown_returns_plain_text():
    parser = DocumentParser()
    md = b"# Title\n\nSome **bold** text and a [link](http://example.com)."
    _, text = parser.parse("policy.md", md)
    assert "Title" in text
    assert "bold" in text
    assert "<" not in text  # no HTML tags


def test_parse_unsupported_type_raises():
    parser = DocumentParser()
    with pytest.raises(ValueError, match="Unsupported file type"):
        parser.parse("file.docx", b"data")


def test_compute_hash_is_deterministic():
    data = b"hello world"
    h1 = DocumentParser.compute_hash(data)
    h2 = DocumentParser.compute_hash(data)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_compute_hash_differs_for_different_content():
    h1 = DocumentParser.compute_hash(b"content A")
    h2 = DocumentParser.compute_hash(b"content B")
    assert h1 != h2
