from io import BytesIO

import pytest
from openpyxl import Workbook

from app.services.extraction import extract_content


def test_text_extraction_decodes_utf8_bom() -> None:
    result = extract_content("notes.txt", b"\xef\xbb\xbfRetention policy")
    assert result.text == "Retention policy"


def test_workbook_extraction_includes_sheet_name_and_values() -> None:
    workbook = Workbook()
    workbook.active.title = "Policy"
    workbook.active.append(["Retention", 7])
    stream = BytesIO()
    workbook.save(stream)

    result = extract_content("policy.xlsx", stream.getvalue())

    assert "[Policy]" in result.text
    assert "Retention\t7" in result.text


def test_unsupported_extension_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_content("malware.exe", b"data")
