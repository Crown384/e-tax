"""Adapt Freedom Tax initialization data to the prototype XTX request model."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from app.errors import InitializationMappingError
from app.models import GenerateXtxRequest, IncomeAmounts, TaxOffice, Taxpayer

_SEPARATOR = "___SEPERATOR___"
_MAX_AMOUNT = 999_999_999_999_999


class InitializationMetadata:
    """Hold filing metadata that is not present in ``initialization.json``.

    Attributes:
        tax_year: Tax year represented by the source data.
        submission_date: Date stamped on the generated KOA020 document.
        etax_user_id: Sixteen-digit e-Tax user identifier.
        tax_office_code: Five-digit tax-office code.
        tax_office_name: Human-readable tax-office name.
    """

    def __init__(
        self,
        *,
        tax_year: int,
        submission_date: date,
        etax_user_id: str,
        tax_office_code: str,
        tax_office_name: str,
    ) -> None:
        """Initialize supplemental filing metadata.

        Args:
            tax_year: Tax year represented by the source data.
            submission_date: Date stamped on the generated document.
            etax_user_id: Sixteen-digit e-Tax user identifier.
            tax_office_code: Five-digit tax-office code.
            tax_office_name: Human-readable tax-office name.
        """
        self.tax_year = tax_year
        self.submission_date = submission_date
        self.etax_user_id = etax_user_id
        self.tax_office_code = tax_office_code
        self.tax_office_name = tax_office_name


def _mapping(value: object, path: str) -> Mapping[str, object]:
    """Return a JSON object or raise a path-specific mapping error.

    Args:
        value: Candidate JSON value.
        path: Human-readable source path.

    Returns:
        Mapping view of the value.

    Raises:
        InitializationMappingError: If the value is not a JSON object.
    """
    if isinstance(value, Mapping):
        return value
    raise InitializationMappingError([f"{path} must be an object"])


def _required_mapping(parent: Mapping[str, object], key: str, path: str) -> Mapping[str, object]:
    """Read one required object child.

    Args:
        parent: Source object.
        key: Child key.
        path: Human-readable parent path.

    Returns:
        Mapping stored under ``key``.

    Raises:
        InitializationMappingError: If the key is absent or is not an object.
    """
    if key not in parent:
        raise InitializationMappingError([f"{path}.{key} is required"])
    return _mapping(parent[key], f"{path}.{key}")


def _year_mapping(
    root: Mapping[str, object], section_name: str, tax_year: int
) -> Mapping[str, object] | None:
    """Read an optional year-keyed section.

    Args:
        root: Complete initialization object.
        section_name: Top-level source section.
        tax_year: Requested filing year.

    Returns:
        Year object when present, otherwise ``None``.

    Raises:
        InitializationMappingError: If a present section has an invalid shape.
    """
    section = root.get(section_name)
    if section is None:
        return None
    section_map = _mapping(section, section_name)
    year_value = section_map.get(str(tax_year))
    if year_value is None:
        return None
    return _mapping(year_value, f"{section_name}.{tax_year}")


def _required_text(parent: Mapping[str, object], key: str, path: str) -> str:
    """Read and normalize one required text field.

    Args:
        parent: Source object.
        key: Child key.
        path: Human-readable parent path.

    Returns:
        Non-empty normalized text.

    Raises:
        InitializationMappingError: If the source value is missing or empty.
    """
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InitializationMappingError([f"{path}.{key} must be a non-empty string"])
    return _normalize_text(value)


def _normalize_text(value: str) -> str:
    """Replace the application's separator token and collapse whitespace.

    Args:
        value: Source application text.

    Returns:
        Human-readable single-space-separated text.
    """
    return " ".join(value.replace(_SEPARATOR, " ").split())


def _taxpayer(root: Mapping[str, object], metadata: InitializationMetadata) -> Taxpayer:
    """Map taxpayer identity from the initialization object.

    Args:
        root: Complete initialization object.
        metadata: Supplemental e-Tax filing metadata.

    Returns:
        Validated taxpayer model used by the XTX generator.
    """
    details = _required_mapping(root, "user_details", "initialization")
    japan_name = _required_mapping(details, "japan_name", "user_details")
    address = _required_mapping(details, "address", "user_details")

    normalized_address = _required_text(address, "address", "user_details.address")
    property_name = address.get("name_of_property")
    if isinstance(property_name, str) and property_name.strip():
        normalized_address = f"{normalized_address} {_normalize_text(property_name)}"

    return Taxpayer(
        etax_user_id=metadata.etax_user_id,
        name=_required_text(japan_name, "name", "user_details.japan_name"),
        name_kana=_required_text(
            japan_name, "name_in_kana", "user_details.japan_name"
        ),
        address=normalized_address,
    )


def _excluded_ids(
    root: Mapping[str, object], meta_section: str, tax_year: int
) -> frozenset[str]:
    """Read source IDs explicitly excluded from the Japanese return.

    Args:
        root: Complete initialization object.
        meta_section: Child of ``income_meta`` containing exclusions.
        tax_year: Requested filing year.

    Returns:
        Immutable set of source record IDs excluded from Japan reporting.
    """
    income_meta = root.get("income_meta")
    if not isinstance(income_meta, Mapping):
        return frozenset()
    section = income_meta.get(meta_section)
    if not isinstance(section, Mapping):
        return frozenset()
    year_value = section.get(str(tax_year))
    if not isinstance(year_value, Mapping):
        return frozenset()
    values = year_value.get("notReportedJapanIncomeIds", [])
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return frozenset()
    return frozenset(value for value in values if isinstance(value, str))


def _whole_yen(value: object, path: str) -> int:
    """Validate one source amount as a non-negative whole-yen integer.

    Args:
        value: Candidate source amount.
        path: Human-readable source path.

    Returns:
        Validated yen amount.

    Raises:
        InitializationMappingError: If the value is not a supported amount.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InitializationMappingError([f"{path} must be a whole-yen integer"])
    if value < 0 or value > _MAX_AMOUNT:
        raise InitializationMappingError(
            [f"{path} must be between 0 and {_MAX_AMOUNT}"]
        )
    return value


def _sum_reportable_items(
    section: Mapping[str, object],
    *,
    section_path: str,
    list_key: str,
    amount_key: str,
    excluded_ids: frozenset[str],
    fallback_total_key: str,
) -> int:
    """Sum list records after removing IDs excluded from Japan reporting.

    Args:
        section: Year-specific income section.
        section_path: Human-readable source path.
        list_key: Key containing item records.
        amount_key: Item field containing the JPY amount.
        excluded_ids: Item IDs marked as not reported in Japan.
        fallback_total_key: Aggregate field used when no item list is present.

    Returns:
        Reportable whole-yen total.

    Raises:
        InitializationMappingError: If a present item has an invalid shape or amount.
    """
    raw_items = section.get(list_key)
    if raw_items is None:
        return _whole_yen(
            section.get(fallback_total_key, 0), f"{section_path}.{fallback_total_key}"
        )
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
        raise InitializationMappingError([f"{section_path}.{list_key} must be an array"])

    total = 0
    for index, raw_item in enumerate(raw_items):
        item_path = f"{section_path}.{list_key}[{index}]"
        item = _mapping(raw_item, item_path)
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id in excluded_ids:
            continue
        total += _whole_yen(item.get(amount_key), f"{item_path}.{amount_key}")
    return total


def _interest_income(root: Mapping[str, object], tax_year: int) -> int:
    """Map reportable interest receipts for the requested year."""
    section = _year_mapping(root, "user_interest_income", tax_year)
    if section is None:
        return 0
    return _sum_reportable_items(
        section,
        section_path=f"user_interest_income.{tax_year}",
        list_key="list_all_interest",
        amount_key="total_amount",
        excluded_ids=_excluded_ids(root, "investment_income_meta", tax_year),
        fallback_total_key="total_investment_income",
    )


def _pension_income(root: Mapping[str, object], tax_year: int) -> int:
    """Map reportable public-pension gross receipts for the requested year."""
    candidates = (
        "user_pension_income",
        "user_pension_income_details",
        "user_pension_income_details_us",
    )
    for section_name in candidates:
        section = _year_mapping(root, section_name, tax_year)
        if section is None:
            continue
        return _sum_reportable_items(
            section,
            section_path=f"{section_name}.{tax_year}",
            list_key="list_pension_data",
            amount_key="total_income",
            excluded_ids=_excluded_ids(root, "pension_income_meta", tax_year),
            fallback_total_key="total_pension",
        )
    return 0


def _miscellaneous_income(root: Mapping[str, object], tax_year: int) -> int:
    """Map reportable miscellaneous gross receipts for the requested year."""
    section = _year_mapping(root, "user_misc_income", tax_year)
    if section is None:
        return 0
    return _sum_reportable_items(
        section,
        section_path=f"user_misc_income.{tax_year}",
        list_key="list_miscellaneous_income_from_work",
        amount_key="gross_payment",
        excluded_ids=_excluded_ids(root, "misc_income_meta", tax_year),
        fallback_total_key="total_gross_income_from_work",
    )


def initialization_to_request(
    initialization: Mapping[str, object], metadata: InitializationMetadata
) -> GenerateXtxRequest:
    """Map Freedom Tax initialization data to the four-field prototype request.

    Args:
        initialization: Full object loaded from ``initialization.json``.
        metadata: Filing metadata absent from that object.

    Returns:
        Validated request ready for XTX generation.

    Raises:
        InitializationMappingError: If required source identity fields are absent or malformed.
    """
    return GenerateXtxRequest(
        tax_year=metadata.tax_year,
        submission_date=metadata.submission_date,
        tax_office=TaxOffice(code=metadata.tax_office_code, name=metadata.tax_office_name),
        taxpayer=_taxpayer(initialization, metadata),
        income=IncomeAmounts(
            interest_income=_interest_income(initialization, metadata.tax_year),
            public_pension_income=_pension_income(initialization, metadata.tax_year),
            other_miscellaneous_income=_miscellaneous_income(
                initialization, metadata.tax_year
            ),
        ),
    )
