import csv
import io
from dataclasses import dataclass
from pathlib import Path

from docx import Document as DocxDocument
from openpyxl import load_workbook
from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedContent:
    text: str
    page_count: int | None = None
    sheet_names: tuple[str, ...] = ()


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".txt"}
MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".txt": "text/plain",
}


def extract_content(filename: str, data: bytes) -> ExtractedContent:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        return ExtractedContent(
            text="\n\n".join(page.extract_text() or "" for page in reader.pages),
            page_count=len(reader.pages),
        )
    if suffix == ".docx":
        document = DocxDocument(io.BytesIO(data))
        return ExtractedContent(text="\n\n".join(p.text for p in document.paragraphs if p.text.strip()))
    if suffix == ".xlsx":
        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        sections = []
        for sheet in workbook.worksheets:
            rows = ["\t".join("" if value is None else str(value) for value in row) for row in sheet.iter_rows(values_only=True)]
            sections.append(f"[{sheet.title}]\n" + "\n".join(row for row in rows if row.strip()))
        return ExtractedContent(text="\n\n".join(sections), sheet_names=tuple(workbook.sheetnames))
    if suffix == ".csv":
        rows = csv.reader(io.StringIO(data.decode("utf-8-sig")))
        return ExtractedContent(text="\n".join("\t".join(row) for row in rows))
    return ExtractedContent(text=data.decode("utf-8-sig"))
