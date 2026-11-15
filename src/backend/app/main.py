from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import (
    BARBER_INACTIVE,
    CANCEL_WINDOW_CLOSED,
    INVALID_START_TIME,
    NOT_FOUND,
    OUTSIDE_BUSINESS_HOURS,
    PAST_DATE,
    SLOT_TAKEN,
    TOO_FAR_AHEAD,
    UNAUTHORIZED,
    VALIDATION_ERROR,
    DomainError,
)
from app.routers.availability import router as availability_router
from app.routers.catalog import router as catalog_router

ERROR_STATUS = {
    SLOT_TAKEN: 409,
    OUTSIDE_BUSINESS_HOURS: 422,
    INVALID_START_TIME: 422,
    PAST_DATE: 422,
    TOO_FAR_AHEAD: 422,
    CANCEL_WINDOW_CLOSED: 409,
    BARBER_INACTIVE: 422,
    NOT_FOUND: 404,
    VALIDATION_ERROR: 422,
    UNAUTHORIZED: 401,
}

app = FastAPI(title="BarberBook API")
app.include_router(catalog_router)
app.include_router(availability_router)


@app.exception_handler(DomainError)
async def domain_error_handler(
    _request: Request, exc: DomainError
) -> JSONResponse:
    details = {"field": exc.field} if exc.field else {}
    return JSONResponse(
        status_code=ERROR_STATUS.get(exc.code, 400),
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0]
    location = first_error.get("loc", ())
    field = str(location[-1]) if location else "request"
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": VALIDATION_ERROR,
                "message": first_error.get("msg", "Solicitud inválida"),
                "details": {"field": field},
            }
        },
    )


@app.get("/health", status_code=200)
def health() -> dict[str, str]:
    return {"status": "ok"}
