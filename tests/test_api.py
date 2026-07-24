"""Integration tests for the REST API."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.api import create_app
from app.config import Settings


def test_generate_and_download(
    tmp_path: Path, payload: dict[str, object], subset_schema: Path
) -> None:
    """Generate a valid XTX and download the same stored bytes."""
    app = create_app(Settings(storage_dir=tmp_path, schema_path=subset_schema))
    client = TestClient(app)

    response = client.post("/v1/xtx", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["form"] == "KOA020"
    assert body["form_version"] == "23.0"

    download = client.get(f"/v1/xtx/{body['document_id']}")
    assert download.status_code == 200
    assert b"<ABB00350>100000</ABB00350>" in download.content


def test_invalid_user_id_returns_422(
    tmp_path: Path, payload: dict[str, object], subset_schema: Path
) -> None:
    """Reject a taxpayer identifier that is not exactly 16 digits."""
    app = create_app(Settings(storage_dir=tmp_path, schema_path=subset_schema))
    client = TestClient(app)
    payload["taxpayer"]["etax_user_id"] = "123"  # type: ignore[index]
    assert client.post("/v1/xtx", json=payload).status_code == 422


def test_missing_document_returns_404(tmp_path: Path, subset_schema: Path) -> None:
    """Return 404 for a syntactically valid but unknown UUID."""
    app = create_app(Settings(storage_dir=tmp_path, schema_path=subset_schema))
    client = TestClient(app)
    response = client.get("/v1/xtx/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_generate_from_initialization(
    tmp_path: Path, subset_schema: Path
) -> None:
    """Generate an XTX from the unmodified Freedom Tax initialization shape."""
    import json

    fixture = Path(__file__).parent / "fixtures/initialization.json"
    initialization = json.loads(fixture.read_text(encoding="utf-8"))
    app = create_app(Settings(storage_dir=tmp_path, schema_path=subset_schema))
    client = TestClient(app)
    response = client.post(
        "/v1/xtx/from-initialization",
        params={
            "etax_user_id": "0000000000000000",
            "tax_office_code": "01143",
            "tax_office_name": "新宿",
            "submission_date": "2026-01-05",
            "tax_year": "2025",
        },
        json=initialization,
    )

    assert response.status_code == 201
    download = client.get(f"/v1/xtx/{response.json()['document_id']}")
    assert b"<ABB00350>4000</ABB00350>" in download.content
    assert b"<ABB00100>6000</ABB00100>" in download.content
    assert b"<ABB00110>7000</ABB00110>" in download.content


def test_initialization_missing_identity_returns_422(
    tmp_path: Path, subset_schema: Path
) -> None:
    """Return a readable source-path error for incomplete initialization data."""
    app = create_app(Settings(storage_dir=tmp_path, schema_path=subset_schema))
    client = TestClient(app)
    response = client.post(
        "/v1/xtx/from-initialization",
        params={
            "etax_user_id": "0000000000000000",
            "tax_office_code": "01143",
            "tax_office_name": "新宿",
            "submission_date": "2026-01-05",
        },
        json={},
    )
    assert response.status_code == 422
    assert "user_details" in str(response.json()["detail"])
