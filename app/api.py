"""FastAPI routes for KOA020 XTX generation and retrieval."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.config import Settings
from app.errors import XtxValidationError
from app.generator import generate_xtx
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
        version="1.0.0",
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
        """Generate, validate, and store a KOA020 v23 XTX document.

        Args:
            request: Incoming request used to build the download URL.
            data: Validated taxpayer and income fields.

        Returns:
            Stored document metadata and download URL.

        Raises:
            HTTPException: If XSD validation fails.
        """
        xml_bytes = generate_xtx(data)
        try:
            validate_xtx(xml_bytes, resolved.schema_path)
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
            validation_scope=_validation_scope(resolved.schema_path),
            download_url=download_url,
        )

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
