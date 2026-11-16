"""Errores de dominio y sus códigos (specs/business-rules.md → Códigos de error)."""

SLOT_TAKEN = "SLOT_TAKEN"
OUTSIDE_BUSINESS_HOURS = "OUTSIDE_BUSINESS_HOURS"
INVALID_START_TIME = "INVALID_START_TIME"
PAST_DATE = "PAST_DATE"
TOO_FAR_AHEAD = "TOO_FAR_AHEAD"
CLOSED = "CLOSED"
CANCEL_WINDOW_CLOSED = "CANCEL_WINDOW_CLOSED"
ALREADY_CANCELLED = "ALREADY_CANCELLED"
BARBER_INACTIVE = "BARBER_INACTIVE"
NOT_FOUND = "NOT_FOUND"
VALIDATION_ERROR = "VALIDATION_ERROR"
UNAUTHORIZED = "UNAUTHORIZED"


class DomainError(Exception):
    """Violación de una regla de negocio; los routers la traducen a HTTP."""

    def __init__(self, code: str, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
