"""Issue #15 · orígenes CORS configurables con CORS_ORIGINS."""

import pytest

from app.core.config import DEFAULT_CORS_ORIGINS, cors_origins


def test_cors_origins_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert cors_origins() == DEFAULT_CORS_ORIGINS == ["http://localhost:5173"]


def test_cors_origins_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", " http://localhost:5173 , https://barberbook.example ,")

    assert cors_origins() == ["http://localhost:5173", "https://barberbook.example"]


def test_cors_origins_rejects_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    """architecture.md §5: CORS limitado al origen del frontend, nunca '*'."""
    monkeypatch.setenv("CORS_ORIGINS", "*")

    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        cors_origins()


def test_cors_origins_strip_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    """El navegador envía el Origin sin '/' final: con '/' no coincidiría y bloquearía sin error claro."""
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173/, https://barberbook.example/")

    assert cors_origins() == ["http://localhost:5173", "https://barberbook.example"]
