"""Run the FTJ e-Tax REST API."""

import uvicorn


def main() -> None:
    """Print the initialization marker and start the API server."""
    print("Hello from FTJ!")
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
