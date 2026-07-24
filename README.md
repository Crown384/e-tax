# FTJ e-Tax XTX service

Python REST service that generates an unsigned Japanese e-Tax `.xtx` document for:

- Income-tax procedure `RKO0010` v25.0.0
- Main individual return `KOA020` v23.0
- Tax year 2025

It supports both a small prototype request and the client's existing `initialization.json` structure. Every generated file is validated, saved locally, and available through a download endpoint.

## Prototype fields

| Field | KOA020 item |
|---|---|
| Taxpayer name in Katakana | `ABA00130` → `NOZEISHA_NM_KN` |
| Interest income | `ABB00350` |
| Public-pension gross receipts | `ABB00100` |
| Other miscellaneous gross receipts | `ABB00110` |

The exact Freedom Tax paths and exclusion rules are documented in [docs/field-mapping.md](docs/field-mapping.md).

## Local setup with Poetry

Requirements: Python 3.13 and Poetry 2.1+.

```bash
git clone https://github.com/Crown384/e-tax.git
cd e-tax

pip install poetry==2.1.4
poetry install
poetry run pytest
poetry run python main.py
```

The terminal prints `Hello from FTJ!`. Open:

- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Local setup with Docker

Install Docker Desktop, then run:

```bash
git clone https://github.com/Crown384/e-tax.git
cd e-tax
docker compose up --build
```

Open http://localhost:8000/docs. Generated files persist under `data/generated`.

To run the test suite inside Docker:

```bash
docker build --target test -t ftj-etax-test .
docker run --rm ftj-etax-test
```

## Generate from the client's initialization.json

The initialization object contains taxpayer and income data, but it does not contain the official 16-digit e-Tax ID, receiving tax office, or form creation date. Supply those as query parameters while sending the original JSON as the request body.

```bash
curl -X POST \
  "http://localhost:8000/v1/xtx/from-initialization?etax_user_id=0000000000000000&tax_office_code=01143&tax_office_name=Shinjuku&submission_date=2026-01-05&tax_year=2025" \
  -H "Content-Type: application/json" \
  --data-binary @initialization.json
```

`0000000000000000` is only suitable for local structure testing. Use a legitimate user ID and the correct tax-office details for a real filing.

The response contains a `download_url`:

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

Open the URL in a browser or download it:

```bash
curl -OJ http://localhost:8000/v1/xtx/{document_id}
```

The same operation can be tested more easily from Swagger at `/docs`: select `POST /v1/xtx/from-initialization`, enter the query values, paste the JSON body, and click **Execute**.

## Compact prototype request

```bash
curl -X POST http://localhost:8000/v1/xtx \
  -H "Content-Type: application/json" \
  --data @examples/request.json
```

## Validation

The bundled schema is a compact project-authored subset covering the implemented envelope and fields. A generated file was also tested successfully against the complete official `RKO0010-250.xsd` dependency tree extracted from the NTA `e-tax19.CAB` package.

To repeat full official validation:

```bash
poetry run python scripts/validate_official.py /path/to/generated.xtx \
  --schema "/path/to/19XMLスキーマ/shotoku/RKO0010-250.xsd"
```

The server can use the full official tree directly:

```bash
ETAX_SCHEMA_PATH="/path/to/19XMLスキーマ/shotoku/RKO0010-250.xsd" \
poetry run python main.py
```

## Tests and CI

```bash
poetry run pytest
poetry run ruff check .
```

Tests cover direct mapping, the real initialization data shape, Japan-reporting exclusions, deterministic XML generation, schema rejection after tampering, API generation/download, invalid input, and missing files. GitHub Actions also builds the Docker test and runtime stages and performs a container health check.

## Scope and limitations

- The prototype fills the four requested scenario fields, not every KOA020 field.
- It produces unsigned XTX. e-Tax performs login, signing, and transmission.
- XSD validity does not prove tax-calculation correctness or all server-side business rules.
- The exact legacy document called `配当所得の内訳書` needs client confirmation because no current form with that exact name appears in `RKO0010-250`.
- No real taxpayer return was transmitted.

The open-question research is answered in [docs/research.md](docs/research.md).
