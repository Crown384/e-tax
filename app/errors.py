"""Application-specific exceptions."""


class XtxValidationError(ValueError):
    """Report one or more XML schema validation failures."""

    def __init__(self, errors: list[str]) -> None:
        """Initialize the exception with readable schema errors.

        Args:
            errors: Validation messages produced by lxml.
        """
        self.errors = errors
        super().__init__("; ".join(errors))
