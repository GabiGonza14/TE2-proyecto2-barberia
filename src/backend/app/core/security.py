"""Autenticación del administrador (RF-14 · specs/architecture.md §5)."""

import os
import secrets
from typing import Annotated

from fastapi import Header

from app.core.errors import UNAUTHORIZED, DomainError

ADMIN_KEY_ENV = "ADMIN_KEY"


def require_admin(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
) -> None:
    """401 si falta la clave, es incorrecta o ADMIN_KEY no está configurada.

    Se compara en tiempo constante y la clave nunca se registra en logs.
    """
    expected = os.environ.get(ADMIN_KEY_ENV, "")
    if not expected or not x_admin_key or not secrets.compare_digest(
        x_admin_key.encode(), expected.encode()
    ):
        raise DomainError(UNAUTHORIZED, "Se requiere una clave de administrador válida")
