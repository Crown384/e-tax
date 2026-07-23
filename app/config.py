"""Application configuration and resource paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class Settings:
    """Store runtime paths used by the API and validator.

    Attributes:
        storage_dir: Directory used for generated XTX files and metadata.
        schema_path: XSD used for validation before a document is persisted.
    """

    storage_dir: Path
    schema_path: Path

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build settings from environment variables.

        Returns:
            Resolved settings with project-local defaults.
        """
        storage = Path(os.getenv("ETAX_STORAGE_DIR", PROJECT_ROOT / "data/generated"))
        schema = Path(
            os.getenv(
                "ETAX_SCHEMA_PATH",
                PROJECT_ROOT / "schemas/shotoku/RKO0010-250-koa020-prototype.xsd",
            )
        )
        return cls(storage_dir=storage, schema_path=schema)
