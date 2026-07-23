"""Persist and retrieve generated XTX documents locally."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class StoredDocument:
    """Describe a generated document stored on disk.

    Attributes:
        document_id: Stable UUID used by the API.
        filename: Download filename exposed to clients.
        path: Absolute or configured filesystem path.
    """

    document_id: str
    filename: str
    path: Path


class LocalXtxStorage:
    """Store XTX bytes and small JSON metadata using atomic renames."""

    def __init__(self, root: Path) -> None:
        """Initialize storage and create its root directory.

        Args:
            root: Directory receiving generated files.
        """
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes) -> StoredDocument:
        """Persist one generated document atomically.

        Args:
            content: Validated XTX bytes.

        Returns:
            Stored document identity and path.
        """
        document_id = str(uuid4())
        filename = f"koa020-{document_id}.xtx"
        destination = self.root / filename
        temporary = destination.with_suffix(".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, destination)
        metadata = {"document_id": document_id, "filename": filename}
        (self.root / f"{document_id}.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return StoredDocument(document_id, filename, destination)

    def get(self, document_id: str) -> StoredDocument | None:
        """Resolve a stored document without accepting path traversal.

        Args:
            document_id: UUID returned by the generation endpoint.

        Returns:
            Stored document when present, otherwise ``None``.
        """
        try:
            normalized = str(UUID(document_id))
        except ValueError:
            return None
        metadata_path = self.root / f"{normalized}.json"
        if not metadata_path.is_file():
            return None
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        path = self.root / metadata["filename"]
        if not path.is_file():
            return None
        return StoredDocument(normalized, metadata["filename"], path)
