class ApplicationError(Exception):
    """Base exception for all service-layer errors."""

    def __init__(self, message: str, extra: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.extra = extra or {}


class PermissionDenied(ApplicationError):
    pass


class ValidationError(ApplicationError):
    pass


class NotFound(ApplicationError):
    pass
