import os
import pytest
from app.document_processing.extractor import DocumentExtractor, DocumentExtractionError
from app.demo_data.synthetic_dataset import generate_synthetic_documents


def test_pdf_extraction():
    files = generate_synthetic_documents()
    assert len(files) == 5

    for f in files:
        assert os.path.exists(f)
        extracted = DocumentExtractor.extract(f)
        assert "full_text" in extracted
        assert len(extracted["full_text"]) > 100
        assert extracted["page_count"] >= 1
        assert len(extracted["pages"]) == extracted["page_count"]


def test_text_file_extraction(tmp_path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("Patient Sarah Jenkins presented with elevated blood sugar.")
    res = DocumentExtractor.extract(str(txt_file))
    assert res["full_text"] == "Patient Sarah Jenkins presented with elevated blood sugar."
    assert res["page_count"] == 1


def test_invalid_file():
    with pytest.raises(DocumentExtractionError):
        DocumentExtractor.extract("non_existent_file.pdf")
