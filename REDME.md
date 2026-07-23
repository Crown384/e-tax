Summary
We're building an e-Tax integration for a tax software platform serving Japan. We are looking for a Python developer to generate .xtx (XML) files based on National Tax Agency specifications. Attention to detail and experience with Python are essential.

You'll create a Python module that:
- Maps calculated tax data to e-Tax XML structure
- Generates .xtx files compliant with NTA specifications
- Validates output against Japanese technical documentation

This is a data mapping + XML generation project. No tax domain knowledge needed because you will be implementing a technical specification.

What We Need:
- Strong Python developer (comfortable with data structures, libraries)
- Able to read and implement dense technical documentation in Japanese
- Attention to detail (hundreds of data points with specific placement)

Deliverable:
Working Python module that generates valid e-Tax .xtx files ready for NTA submission.

.


plz check readme and follow this so you can print "Hello from FTJ!" of main.py

whole msg:

We have shared the spec doc with your email here: 
https://github.com/Freedom-Tax/ftj_etax_service/issues/1

This is the test phase of our project. It will help us see whether you can do this project. 

It has two deliverables listed there.

1) Please let me know how many hours this phase might take you. 

2) You may ask questions to us.


# Code documentation guidelines

## Introduction

These guidelines explain how to document code in this repository. They're based on the
[Google developer documentation style guide](https://developers.google.com/style). For anything
not covered below, follow that guide.

## Project requirements

1. Use [Poetry](https://python-poetry.org) to manage Python packages.
2. The application must expose a REST API.
3. The application must include a Dockerfile and must run as a container.

### Example: containerizing the application

The `Dockerfile` uses a multi-stage build. The `builder` stage resolves dependencies with Poetry
into a virtualenv; the `runtime` stage copies only that virtualenv, so build tools stay out of the
shipped image:

```dockerfile
FROM python:3.13-slim AS builder
WORKDIR /app

ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

COPY pyproject.toml ./
RUN --mount=type=ssh poetry install --only main --no-root

FROM python:3.13-slim AS runtime
WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY --from=builder /app/.venv /app/.venv
COPY ./app /app/
```

The image intentionally defines no `CMD`. The start command is supplied by whatever runs the
container, which keeps one image reusable across the API, the SSE service, and the pub/sub
listeners:

```yaml
# docker-compose.yaml
ftj-api:
  image: ftj-etax:1.0
  build:
    context: .
    dockerfile: Dockerfile
    ssh:
      - default=${SSH_AUTH_SOCK}
  command: ["python", "./main.py"]
```

Build and run it locally:

```bash
docker compose up --build --watch
```

Private dependencies are installed over SSH, so the build needs a running SSH agent — `ssh-add -l`
must list a key with access to the private repositories, or `poetry install` fails in the `builder`
stage.

## Docstring style

Write [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
Open with a one-line summary in the imperative mood ("Fetch the current rule set", not "Fetches" or
"This function fetches"), then a blank line, then the details.

Document what a reader can't get from the signature: units, side effects, what `None` means, which
errors escape. Don't restate types that are already annotated.

### Classes

Summarize what the class is for and how it fits the layer around it. Use an `Attributes:` section
for public attributes:

```python
class MongoContextEvalRuleSet(EvalRuleSet):
    """Stored shape of a context evaluation rule set document.

    Extends the domain ``EvalRuleSet`` (``version``/``title``/``description``/
    ``rules``/``filters``) with the persistence fields Mongo needs:

    Attributes:
        id: Mongo ``_id`` (set by the server on insert).
        rule_id: Business key identifying a *draft* rule set; ``None`` for the
            current/published set, which is keyed by ``tax_year`` alone.
        last_updated: Server timestamp of the last write, maintained via
            ``$currentDate``.
        tax_year: Tax year the rule set applies to (stored as the ``YYYY``
            string form).
    """
```

### Functions and methods

Use `Args:`, `Returns:`, and `Raises:`. Omit a section when it doesn't apply — don't write
`Raises: None`:

```python
async def get_rule_with_rule_id(self, rule_id: str):
    """Fetch a single draft rule set by its ``rule_id``.

    Args:
        rule_id: Business key identifying the draft.

    Returns:
        The draft document, or ``None`` if no draft has that ``rule_id``.
    """
```

`Returns:` should say what the value *means*, not just its type. `Raises:` lists only what callers
can act on — the errors this function deliberately raises or translates:

```python
async def get_eval_rule_with_id(self, rule_id: str):
    """Fetch a single draft rule set by its ``rule_id``.

    Args:
        rule_id: Business key identifying the draft.

    Returns:
        The draft document.

    Raises:
        ValueNotFound: If no draft has that ``rule_id``.
        ModelValidationErrors: If the stored document fails validation.
        InternalServerError: On unexpected failures.
    """
```

Document non-obvious behavior where it will actually be read. If a write bumps a version counter,
enlists in a session, or is created when absent, say so in the summary paragraph rather than making
the next reader infer it from the update operators.

### API routes

Every route must declare three things:

1. An explicit `status_code`.
2. A `responses` map documenting every status the route can return.
3. A docstring with an `Args:` section.

The `responses` map is what renders in the OpenAPI schema at `/docs`, so it's the contract API
consumers read. Keep it honest: list the statuses the route actually returns.

```python
@compliance_router.post(
    "/requirements",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"model": GenericResponse, "description": "On Success"},
        400: {"model": ErrorResponse, "description": "Model validation error, or a malformed/unknown authentication token."},
        401: {"model": ErrorResponse, "description": "Invalid authentication token."},
        403: {"model": ErrorResponse, "description": "Authentication token has expired."},
        404: {"model": ErrorResponse, "description": "Requested resource was not found."},
        500: {"model": ErrorResponse, "description": "Unknown error."},
    },
)
async def upsert_compliance_requirements(
    request: Request,
    tax_year: Annotated[CustomYear, Header()],
    data: UserComplicanceBody,
    current_auth: AuthObj = Depends(DependencyFunctions.get_current_auth_object),
    handler: ComplianceRouteHandler = Depends(ComplianceRouteHandler),
):
    """
    Create or update the user's compliance requirements for a given tax year.

    Args:
        request: Incoming HTTP request — used to extract the request_id from request.state.
        tax_year: Tax year for this operation, passed as a request header.
        data: UserComplicanceBody containing the compliance requirement fields to upsert.
        current_auth: Authenticated user object extracted from the bearer token.
        handler: FastAPI dependency-injected route handler instance.
    """
```

## Comments

Prefer a clear name over a comment. Write a comment to record what the code can't show — a
constraint, a rejected alternative, or a reason:

```python
# version is excluded from the $set payload because it is owned by the $inc —
# setting and incrementing the same path in one update is rejected by Mongo.
**data.model_dump(exclude={"version"}),
```

Don't narrate what the next line does, and don't leave comments that describe how the code got here
(`# fixed bug`, `# changed from X`).

## Keeping docs true

A docstring that contradicts the code is worse than no docstring:

- Validate the logic before you document it. If documenting a function surfaces a bug, fix the bug
  first; don't write a docstring that describes the intended behavior of broken code.
- When you change behavior, update the docstring in the same commit.