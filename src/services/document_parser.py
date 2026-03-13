import hashlib
import io
import re
from pathlib import Path


class DocumentParser:

    @staticmethod
    def compute_hash(content: bytes) -> str:
        """Return a SHA-256 hex digest of the raw file bytes."""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def parse_pdf(content: bytes) -> str:
        """Extract all text from a PDF using pdfplumber, joining pages with double newlines."""
        import pdfplumber

        text_pages: list[str] = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text.strip())
        return "\n\n".join(text_pages)

    @staticmethod
    def parse_markdown(content: bytes) -> str:
        """Convert Markdown to plain text by rendering to HTML then stripping tags."""
        import mistune

        md_text = content.decode("utf-8", errors="replace")
        html = mistune.html(md_text)
        clean = re.sub(r"<[^>]+>", " ", html)
        clean = re.sub(r"&[a-z]+;", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def parse(self, filename: str, content: bytes) -> tuple[str, str]:
        """
        Parse a document and return (file_type, extracted_text).
        Raises ValueError for unsupported file types.
        """
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            return "pdf", self.parse_pdf(content)
        elif suffix in (".md", ".markdown"):
            return "markdown", self.parse_markdown(content)
        else:
            raise ValueError(f"Unsupported file type '{suffix}'. Only .pdf and .md/.markdown are accepted.")
