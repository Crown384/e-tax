# FTJ e-Tax XTX service

Python REST service that maps prototype tax data to the Japanese NTA e-Tax XML structure and generates an unsigned `.xtx` document for:

- Tax year: **2025 (令和7年分)**
- Procedure: `RKO0010` v25.0.0
- Main individual return: `KOA020` v23.0

The application creates the real nested XTX envelope (`DATA`, procedure, catalog, identity section, form/pages/groups, namespaces, versions, and `ID`/`IDREF` links), validates it, saves it locally, and returns a download URL.

## Prototype fields

| Request field | e-Tax field |
|---|---|
| Taxpayer name in Katakana | `ABA00130` → `NOZEISHA_NM_KN` |
| Interest income | `ABB00350` |
| Public-pension gross receipts | `ABB00100` |
| Other miscellaneous gross receipts | `ABB00110` |

See [`docs/field-mapping.md`](docs/field-mapping.md) for the complete paths and semantic notes.

## Fastest local setup: Docker Desktop

Prerequisites:

- Git
- Docker Desktop running

From Git Bash in the repository folder:

```bash
docker compose up --build
```

Leave that terminal running. In a second Git Bash window:

```bash
python scripts/smoke_test.py
```

Expected output:

```text
PASS: generated and downloaded data/generated/smoke-test.xtx
```

Then open:

- API documentation: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health

Stop the service with `Ctrl+C`, then run:

```bash
docker compose down
```

## Local setup without Docker

Prerequisites:

- Python 3.13
- Poetry 2.1+

```bash
poetry install
poetry run python main.py
```

The startup command prints `Hello from FTJ!` and starts the API on port 8000.

In a second terminal:

```bash
poetry run pytest
poetry run ruff check .
poetry run python scripts/smoke_test.py
```

## REST API

### Generate, validate, and save an XTX

```bash
curl -X POST http://localhost:8000/v1/xtx \
  -H 'Content-Type: application/json' \
  --data @examples/request.json
```

Example response:

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

Download the document using the returned URL:

```bash
curl -OJ http://localhost:8000/v1/xtx/{document_id}
```

Generated files are persisted under `data/generated`.

## Validation

Every generated file is validated before storage. The repository bundles a compact project-authored schema for the exact prototype envelope and fields so tests remain self-contained.

For final verification, validate against the complete official schema tree extracted from NTA `e-tax19.CAB`:

```bash
poetry run python scripts/validate_official.py /path/to/generated.xtx \
  --schema "/path/to/19XMLスキーマ/shotoku/RKO0010-250.xsd"
```

The API itself can use the full schema:

```bash
ETAX_SCHEMA_PATH="/path/to/19XMLスキーマ/shotoku/RKO0010-250.xsd" \
poetry run python main.py
```

## Tests and CI

```bash
poetry run pytest
poetry run ruff check .
```

GitHub Actions runs linting, unit/integration tests, a Docker image build, container startup, API health checking, XTX generation, and download smoke testing.

## Research answers

[`docs/research.md`](docs/research.md) answers:

1. Which listed returns/schedules belong in the `RKO0010` XTX and which applications require separate e-Tax procedures.
2. The possible import, schema, business-rule, signature, authentication, version, and transmission failure stages.
3. Available testing routes and the absence of an anonymous public individual-return XTX uploader.

## Extension design

The service separates:

1. API input models.
2. Source-data-to-e-Tax mapping.
3. XSD-derived ordered rendering.
4. Schema validation.
5. Storage and REST transport.

Additional fields extend the input adapter and item-code mapping. Additional forms or years require their official schema-derived layout, mapping, version metadata, and tests; the API and storage layers do not need to be rewritten.

## Limitations

- This coding-test implementation covers the four highlighted scenario fields, not every KOA020 field.
- It produces unsigned XTX. e-Tax handles authentication, electronic signatures, and transmission.
- XSD validity does not prove tax-calculation correctness or every cross-form business rule.
- No fictional or real taxpayer return was transmitted.
