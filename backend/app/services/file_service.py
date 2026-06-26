MAX_TEXT = 8000
HEAD = 6000
TAIL = 2000


def _truncate(text: str) -> str:
    if len(text) <= MAX_TEXT:
        return text
    return text[:HEAD] + "\n...\n" + text[-TAIL:]


def parse_file(file_path: str, file_type: str) -> str:
    """Extract plain text from an uploaded file. file_type: pdf|word|txt|markdown."""
    if file_type == "pdf":
        import pdfplumber

        parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        text = "\n".join(parts)
    elif file_type == "word":
        from docx import Document

        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)
    elif file_type in ("txt", "markdown"):
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

    return _truncate(text.strip())
