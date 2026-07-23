"""Tests for deterministic field mapping and XTX rendering."""

from lxml import etree

from app.generator import GENERAL_NS, SHOTOKU_NS, generate_xtx
from app.models import GenerateXtxRequest

NS = {"s": SHOTOKU_NS, "g": GENERAL_NS}


def test_generate_maps_expected_fields(payload: dict[str, object]) -> None:
    """Map the four requested fields and taxpayer references correctly."""
    document = etree.fromstring(generate_xtx(GenerateXtxRequest.model_validate(payload)))
    assert document.xpath("string(.//s:ABA00130/@IDREF)", namespaces=NS) == "NOZEISHA_NM_KN"
    assert document.xpath("string(.//s:ABB00350)", namespaces=NS) == "100000"
    assert document.xpath("string(.//s:ABB00100)", namespaces=NS) == "500000"
    assert document.xpath("string(.//s:ABB00110)", namespaces=NS) == "20000"
    assert document.xpath("string(.//s:KOA020/@VR)", namespaces=NS) == "23.0"
    assert document.xpath("string(.//s:RKO0010/@VR)", namespaces=NS) == "25.0.0"


def test_generate_is_deterministic(payload: dict[str, object]) -> None:
    """Produce identical bytes for identical input."""
    data = GenerateXtxRequest.model_validate(payload)
    assert generate_xtx(data) == generate_xtx(data)
