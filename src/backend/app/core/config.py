"""Configuración leída del entorno."""

import os

DEFAULT_CORS_ORIGINS = ["http://localhost:5173"]


def cors_origins() -> list[str]:
    """Orígenes permitidos por CORS (architecture.md §5).

    `CORS_ORIGINS` es una lista separada por comas. Sin la variable se usa el
    frontend local de Vite. Se rechaza `*`: el CORS debe limitarse al frontend.
    """
    raw = os.environ.get("CORS_ORIGINS")
    if raw is None:
        return list(DEFAULT_CORS_ORIGINS)
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if "*" in origins:
        raise ValueError("CORS_ORIGINS no puede ser '*': indica el origen del frontend")
    return origins
