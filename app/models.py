"""REST API request and response models."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Digits5 = Annotated[str, StringConstraints(pattern=r"^\d{5}$")]
Digits16 = Annotated[str, StringConstraints(pattern=r"^\d{16}$")]
NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Amount = Annotated[int, Field(ge=0, le=999_999_999_999_999)]


class StrictModel(BaseModel):
    """Reject unknown fields in public API payloads."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TaxOffice(StrictModel):
    """Identify the Japanese tax office receiving the return."""

    code: Digits5
    name: NonBlank


class Taxpayer(StrictModel):
    """Hold taxpayer identity fields required by the e-Tax IT section."""

    etax_user_id: Digits16
    name: NonBlank
    name_kana: NonBlank
    address: NonBlank


class IncomeAmounts(StrictModel):
    """Hold the prototype income values mapped to KOA020 v23."""

    interest_income: Amount
    public_pension_income: Amount
    other_miscellaneous_income: Amount


class GenerateXtxRequest(StrictModel):
    """Describe one KOA020 v23 XTX generation request."""

    tax_year: Literal[2025] = 2025
    submission_date: date
    tax_office: TaxOffice
    taxpayer: Taxpayer
    income: IncomeAmounts


class GenerateXtxResponse(StrictModel):
    """Describe a generated and persisted XTX document."""

    document_id: str
    filename: str
    procedure: Literal["RKO0010"] = "RKO0010"
    procedure_version: Literal["25.0.0"] = "25.0.0"
    form: Literal["KOA020"] = "KOA020"
    form_version: Literal["23.0"] = "23.0"
    validation_scope: str
    download_url: str


class HealthResponse(StrictModel):
    """Describe service readiness."""

    status: Literal["ok"] = "ok"


class ErrorResponse(StrictModel):
    """Describe an API failure."""

    detail: str | list[str]
