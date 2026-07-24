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


class InitializationMappingError(ValueError):
    """Report source-data fields that cannot be mapped to the prototype."""

    def __init__(self, errors: list[str]) -> None:
        """Initialize the exception with readable source mapping errors.

        Args:
            errors: Source paths and mapping failures.
        """
        self.errors = errors
        super().__init__("; ".join(errors))
