"""RNF-06: no se registran teléfonos completos en logs.

`GET /api/v1/bookings/{code}?phone=...` (RF-10) lleva el teléfono en la URL y
el access log de uvicorn la imprime entera. Este filtro deja solo los últimos
4 dígitos: `phone=6123-4567` → `phone=***4567`.
"""

import logging
import re
from urllib.parse import unquote

ACCESS_LOGGER = "uvicorn.access"
_PHONE_PARAM = re.compile(r"(phone=)([^&\s\"]*)", re.IGNORECASE)


def _mask(match: re.Match[str]) -> str:
    value = match.group(2)
    if not value:
        return match.group(0)
    digits = re.sub(r"\D", "", unquote(value))
    return f"{match.group(1)}***{digits[-4:] if len(digits) > 4 else ''}"


def mask_phone_in_text(text: str) -> str:
    return _PHONE_PARAM.sub(_mask, text)


class PhoneMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_phone_in_text(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                mask_phone_in_text(a) if isinstance(a, str) else a
                for a in record.args
            )
        return True


def install_log_filters() -> None:
    logger = logging.getLogger(ACCESS_LOGGER)
    if not any(isinstance(f, PhoneMaskingFilter) for f in logger.filters):
        logger.addFilter(PhoneMaskingFilter())
