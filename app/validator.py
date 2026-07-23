"""Validate generated XTX documents against an XML Schema."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from lxml import etree

from app.errors import XtxValidationError


@lru_cache(maxsize=4)
def _load_schema(schema_path: str) -> etree.XMLSchema:
    """Compile and cache one XSD document.

    Args:
        schema_path: Absolute or relative XSD path.

    Returns:
        Compiled lxml schema validator.
    """
    return etree.XMLSchema(etree.parse(schema_path))


def validate_xtx(xml_bytes: bytes, schema_path: Path) -> None:
    """Reject an XTX document that does not satisfy the configured XSD.

    Args:
        xml_bytes: Complete XTX document bytes.
        schema_path: Root XSD path, including any relative dependencies.

    Raises:
        XtxValidationError: If XML parsing or XSD validation fails.
    """
    try:
        document = etree.fromstring(xml_bytes)
        schema = _load_schema(str(schema_path.resolve()))
    except (etree.XMLSyntaxError, etree.XMLSchemaParseError, OSError) as exc:
        raise XtxValidationError([str(exc)]) from exc
    if schema.validate(document):
        return
    errors = [f"line {entry.line}: {entry.message}" for entry in schema.error_log]
    raise XtxValidationError(errors or ["Unknown XML schema validation error"])
