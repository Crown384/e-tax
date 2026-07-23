"""Map API tax data to official e-Tax element codes."""

from __future__ import annotations

from dataclasses import dataclass

from app.models import GenerateXtxRequest


@dataclass(frozen=True, slots=True)
class FieldValue:
    """Represent one value destined for an XSD-derived form leaf.

    Attributes:
        value: Text written to the element or attribute.
        attribute: Attribute name when the field is an IDREF leaf.
    """

    value: str
    attribute: str | None = None


def map_koa020_fields(data: GenerateXtxRequest) -> dict[str, FieldValue]:
    """Map prototype input to KOA020 v23 item codes.

    Args:
        data: Validated API payload.

    Returns:
        Item-code keyed values consumed by the XTX renderer.
    """
    return {
        "ABA00010": FieldValue("NENBUN", attribute="IDREF"),
        "ABA00030": FieldValue("ZEIMUSHO", attribute="IDREF"),
        "ABA00090": FieldValue("NOZEISHA_ADR", attribute="IDREF"),
        "ABA00130": FieldValue("NOZEISHA_NM_KN", attribute="IDREF"),
        "ABA00140": FieldValue("NOZEISHA_NM", attribute="IDREF"),
        "ABB00100": FieldValue(str(data.income.public_pension_income)),
        "ABB00110": FieldValue(str(data.income.other_miscellaneous_income)),
        "ABB00350": FieldValue(str(data.income.interest_income)),
    }
