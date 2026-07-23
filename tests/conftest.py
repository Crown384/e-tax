"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import PROJECT_ROOT


@pytest.fixture
def payload() -> dict[str, object]:
    """Return a representative valid generation payload."""
    return {
        "tax_year": 2025,
        "submission_date": "2026-01-05",
        "tax_office": {"code": "01143", "name": "新宿"},
        "taxpayer": {
            "etax_user_id": "0000000000000000",
            "name": "山田 太郎",
            "name_kana": "ヤマダ タロウ",
            "address": "東京都新宿区",
        },
        "income": {
            "interest_income": 100000,
            "public_pension_income": 500000,
            "other_miscellaneous_income": 20000,
        },
    }


@pytest.fixture
def subset_schema() -> Path:
    """Return the bundled KOA020 validation XSD."""
    return PROJECT_ROOT / "schemas/shotoku/RKO0010-250-koa020-prototype.xsd"
