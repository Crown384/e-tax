"""Tests for Freedom Tax initialization.json mapping."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from app.errors import InitializationMappingError
from app.initialization_adapter import InitializationMetadata, initialization_to_request

FIXTURE = Path(__file__).parent / "fixtures/initialization.json"


def _metadata() -> InitializationMetadata:
    """Return supplemental metadata absent from initialization.json."""
    return InitializationMetadata(
        tax_year=2025,
        submission_date=date(2026, 1, 5),
        etax_user_id="0000000000000000",
        tax_office_code="01143",
        tax_office_name="新宿",
    )


def test_maps_real_application_paths_and_exclusions() -> None:
    """Map identity and only income records reportable in Japan."""
    initialization = json.loads(FIXTURE.read_text(encoding="utf-8"))
    request = initialization_to_request(initialization, _metadata())

    assert request.taxpayer.name == "Test User"
    assert request.taxpayer.name_kana == "テスト ユーザー"
    assert request.taxpayer.address == "Tokyo Chiyoda-ku 1-2-3 Metro Mansion 105"
    assert request.income.interest_income == 4000
    assert request.income.public_pension_income == 6000
    assert request.income.other_miscellaneous_income == 7000


def test_missing_user_details_fails_loudly() -> None:
    """Reject initialization data that cannot supply taxpayer identity."""
    with pytest.raises(InitializationMappingError, match="user_details"):
        initialization_to_request({}, _metadata())
