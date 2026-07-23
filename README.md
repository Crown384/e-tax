# FTJ e-Tax XTX service

Python REST service that maps the supplied prototype tax fields to the Japanese NTA e-Tax structure and generates an unsigned `.xtx` document for:

- Procedure `RKO0010` v25.0.0
- Main individual return `KOA020` v23.0
- Tax year 2025

The generated XTX is not a flat XML export. It includes the official `DATA`, procedure, catalog, identity (`IT`), form, page, group, `ID`/`IDREF`, namespace, and version structure.

## Implemented prototype fields

| Request field | e-Tax tag |
|---|---|
| Taxpayer name in Katakana | `ABA00130` → `NOZEISHA_NM_KN` reference |
| Interest income | `ABB00350` |
| Public pension gross receipts | `ABB00100` |
| Other miscellaneous gross receipts | `ABB00110` |

See [docs/field-mapping.md](docs/field-mapping.md) for the exact paths and semantic notes.

## Run with Poetry

```bash
poetry install
poetry run python main.py
```

`main.py` prints `Hello from FTJ!` and serves the API on port 8000. Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

## Run with Docker

```bash
docker compose up --build
```

Generated files are persisted under `data/generated`.

## API

### Health

```bash
curl http://localhost:8000/health
```

### Generate, validate, and save XTX

```bash
curl -X POST http://localhost:8000/v1/xtx \
  -H 'Content-Type: application/json' \
  --data @examples/request.json
```

Response:

```json
{
  "document_id": "generated-uuid",
  "filename": "koa020-generated-uuid.xtx",
  "procedure": "RKO0010",
  "procedure_version": "25.0.0",
  "form": "KOA020",
  "form_version": "23.0",
  "validation_scope": "koa020-prototype-subset",
  "download_url": "http://localhost:8000/v1/xtx/generated-uuid"
}
```

Download it with the returned URL:

```bash
curl -OJ http://localhost:8000/v1/xtx/{document_id}
```

## Validation

Every file is validated before storage. The bundled validator is a compact, project-authored subset derived from the official RKO0010, KOA020, IT, catalog, and common-vocabulary definitions for the exact fields implemented by this prototype.

A generated synthetic document was validated successfully against the **complete official `RKO0010-250.xsd`** and all its dependencies extracted from `e-tax19.CAB`.

To repeat full validation locally:

```bash
poetry run python scripts/validate_official.py /path/to/generated.xtx \
  --schema "/path/to/19XMLスキーマ/shotoku/RKO0010-250.xsd"
```

Alternatively, point the running service at the full schema:

```bash
ETAX_SCHEMA_PATH="/path/to/19XMLスキーマ/shotoku/RKO0010-250.xsd" \
poetry run python main.py
```

The API then reports `validation_scope` as `official-full`.

## Tests

```bash
poetry run pytest
```

Coverage includes field mapping, deterministic generation, schema rejection after tampering, API generation/download, input validation, and missing-document behavior.

## Design for extension

The service separates:

1. Pydantic input models.
2. Tax-data-to-e-Tax item mapping.
3. XSD-derived ordered form rendering.
4. Schema validation.
5. Storage and REST transport.

Adding another field means extending the input model and item-code mapping. Adding another form or year requires its official XSD-derived layout, mapping, version metadata, and tests; it does not require rewriting the API/storage layers.

## Limitations

- This test implements the four supplied scenario fields, not every KOA020 field.
- It produces unsigned XTX. The NTA/e-Tax software handles user authentication, electronic signatures, and transmission.
- XSD validity does not independently prove tax-calculation correctness or all e-Tax business-rule checks.
- No live taxpayer return was submitted.

Research findings are recorded in [docs/research.md](docs/research.md).
