"""FastAPI routes for KOA020 XTX generation and retrieval."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from pydantic import ValidationError

from app.config import Settings
from app.errors import InitializationMappingError, XtxValidationError
from app.generator import generate_xtx
from app.initialization_adapter import InitializationMetadata, initialization_to_request
from app.models import (
    ErrorResponse,
    GenerateXtxRequest,
    GenerateXtxResponse,
    HealthResponse,
)
from app.storage import LocalXtxStorage
from app.validator import validate_xtx


def _validation_scope(schema_path: Path) -> str:
    """Describe whether validation used the bundled subset or a full NTA schema.

    Args:
        schema_path: Configured root XSD.

    Returns:
        Human-readable validation scope for API consumers.
    """
    if schema_path.name == "RKO0010-250.xsd":
        return "official-full"
    return "koa020-prototype-subset"


def _generate_and_store(
    request: Request,
    data: GenerateXtxRequest,
    storage: LocalXtxStorage,
    schema_path: Path,
) -> GenerateXtxResponse:
    """Generate, validate, and persist one document.

    Args:
        request: Incoming request used to build the download URL.
        data: Validated XTX generation request.
        storage: Local persistence service.
        schema_path: Configured root XSD.

    Returns:
        Stored document metadata and download URL.

    Raises:
        HTTPException: If XML schema validation fails.
    """
    xml_bytes = generate_xtx(data)
    try:
        validate_xtx(xml_bytes, schema_path)
    except XtxValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.errors,
        ) from exc
    document = storage.save(xml_bytes)
    download_url = str(request.url_for("download_document", document_id=document.document_id))
    return GenerateXtxResponse(
        document_id=document.document_id,
        filename=document.filename,
        validation_scope=_validation_scope(schema_path),
        download_url=download_url,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the configured REST application.

    Args:
        settings: Optional explicit settings, primarily for tests.

    Returns:
        Configured FastAPI application.
    """
    resolved = settings or Settings.from_environment()
    storage = LocalXtxStorage(resolved.storage_dir)
    app = FastAPI(
        title="FTJ e-Tax XTX Service",
        version="1.1.0",
        description="Generate and validate unsigned RKO0010/KOA020 v23 XTX files.",
    )

    @app.get(
        "/health",
        response_model=HealthResponse,
        status_code=status.HTTP_200_OK,
        responses={200: {"description": "Service is ready."}},
    )
    async def health(request: Request) -> HealthResponse:
        """Return service readiness.

        Args:
            request: Incoming HTTP request.

        Returns:
            Static readiness response.
        """
        del request
        return HealthResponse()

    @app.post(
        "/v1/xtx",
        response_model=GenerateXtxResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            201: {"description": "XTX generated, validated, and stored."},
            422: {"model": ErrorResponse, "description": "Input or XSD validation failed."},
            500: {"model": ErrorResponse, "description": "Unexpected generation failure."},
        },
    )
    async def generate_document(
        request: Request, data: GenerateXtxRequest
    ) -> GenerateXtxResponse:
        """Generate an XTX from the compact prototype request structure.

        Args:
            request: Incoming request used to build the download URL.
            data: Validated taxpayer and income fields.

        Returns:
            Stored document metadata and download URL.
        """
        return _generate_and_store(request, data, storage, resolved.schema_path)

    @app.post(
        "/v1/xtx/from-initialization",
        response_model=GenerateXtxResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            201: {"description": "Initialization data mapped to a stored XTX."},
            422: {
                "model": ErrorResponse,
                "description": "A required source path, header, or XSD rule failed.",
            },
        },
    )
    async def generate_from_initialization(
        request: Request,
        initialization: Annotated[
            dict[str, object],
            Body(description="The unmodified Freedom Tax initialization.json object."),
        ],
        etax_user_id: Annotated[
            str, Query(description="16-digit e-Tax user ID")
        ],
        tax_office_code: Annotated[
            str, Query(description="5-digit tax-office code")
        ],
        tax_office_name: Annotated[
            str, Query(description="Tax-office display name")
        ],
        submission_date: Annotated[
            date, Query(description="ISO date: YYYY-MM-DD")
        ],
        tax_year: Annotated[
            int, Query(description="Prototype supports 2025")
        ] = 2025,
    ) -> GenerateXtxResponse:
        """Generate an XTX directly from Freedom Tax initialization data.

        The source object does not contain the e-Tax user ID, receiving tax office, or
        document creation date, so those values are supplied as query parameters.

        Args:
            request: Incoming request used to build the download URL.
            initialization: Complete, unmodified ``initialization.json`` object.
            etax_user_id: Sixteen-digit e-Tax user identifier.
            tax_office_code: Five-digit receiving tax-office code.
            tax_office_name: Human-readable receiving tax-office name.
            submission_date: Date stamped on KOA020.
            tax_year: Source year to read; currently 2025.

        Returns:
            Stored document metadata and download URL.

        Raises:
            HTTPException: If source mapping or model validation fails.
        """
        metadata = InitializationMetadata(
            tax_year=tax_year,
            submission_date=submission_date,
            etax_user_id=etax_user_id,
            tax_office_code=tax_office_code,
            tax_office_name=tax_office_name,
        )
        try:
            data = initialization_to_request(initialization, metadata)
        except (InitializationMappingError, ValidationError) as exc:
            detail = exc.errors if isinstance(exc, InitializationMappingError) else exc.errors()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=detail,
            ) from exc
        return _generate_and_store(request, data, storage, resolved.schema_path)

    @app.get(
        "/v1/xtx/{document_id}",
        name="download_document",
        response_class=FileResponse,
        status_code=status.HTTP_200_OK,
        responses={
            200: {"content": {"application/xml": {}}, "description": "Stored XTX file."},
            404: {"model": ErrorResponse, "description": "Document was not found."},
        },
    )
    async def download_document(request: Request, document_id: str) -> FileResponse:
        """Download a previously generated XTX document.

        Args:
            request: Incoming HTTP request.
            document_id: UUID returned by the generation route.

        Returns:
            XTX file response.

        Raises:
            HTTPException: If the document does not exist.
        """
        del request
        document = storage.get(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generated XTX document was not found.",
            )
        return FileResponse(
            path=document.path,
            filename=document.filename,
            media_type="application/xml",
        )

    return app


app = create_app()
