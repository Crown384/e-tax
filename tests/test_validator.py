"""Tests for XSD validation."""

from pathlib import Path

import pytest

from app.errors import XtxValidationError
from app.generator import generate_xtx
from app.models import GenerateXtxRequest
from app.validator import validate_xtx


def test_generated_document_passes_subset_schema(
    payload: dict[str, object], subset_schema: Path
) -> None:
    """Validate generated XML against the prototype KOA020 schema."""
    xml_bytes = generate_xtx(GenerateXtxRequest.model_validate(payload))
    validate_xtx(xml_bytes, subset_schema)


def test_tampered_document_fails_schema(
    payload: dict[str, object], subset_schema: Path
) -> None:
    """Reject an invalid form version after document tampering."""
    xml_bytes = generate_xtx(GenerateXtxRequest.model_validate(payload)).replace(
        b'VR="23.0"', b'VR="99.0"', 1
    )
    with pytest.raises(XtxValidationError):
        validate_xtx(xml_bytes, subset_schema)
