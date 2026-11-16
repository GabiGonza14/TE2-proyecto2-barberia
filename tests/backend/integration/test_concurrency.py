"""T7 · Concurrencia: doble reserva simultánea (issue #11).

Trazabilidad: O1 → RF-07, RNF-01 → BR-01 → AC-06.

Cada petición usa su propia sesión de BD (``get_db``) y se lanza desde su
propio hilo, sincronizados con ``threading.Barrier`` para que lleguen a la vez.
Corre contra PostgreSQL real: la capa 2 (``no_double_booking``) es la garantía.
"""

import asyncio
import threading
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

import httpx
import pytest
from psycopg.errors import DeadlockDetected, SerializationFailure
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

import app.repositories.bookings as bookings_repository
from app.core.clock import get_now
from app.domain.rules import TZ
from app.main import app

FIXED_NOW = datetime(2026, 12, 1, 8, 0, tzinfo=TZ)
ROUNDS = 20
BARRIER_TIMEOUT = 10


@pytest.fixture(autouse=True)
def fixed_clock(clean_bookings) -> None:
    app.dependency_overrides[get_now] = lambda: FIXED_NOW
    yield
    app.dependency_overrides.pop(get_now, None)


async def _post(body: dict[str, Any]) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.post("/api/v1/bookings", json=body)


def _ids(engine: Engine) -> dict[str, int]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT 'barber_' || name AS key, id FROM barbers "
                "UNION ALL SELECT 'service_' || name AS key, id FROM services"
            )
        )
    return {row.key: row.id for row in rows}


def _body(ids: dict[str, int], start: datetime, service: str = "Corte", n: int = 1):
    return {
        "barber_id": ids["barber_Carlos"],
        "service_id": ids[f"service_{service}"],
        "start_at": start.isoformat(),
        "client_name": f"Cliente {n}",
        "client_phone": "6123-4567",
    }


def _race(bodies: list[dict[str, Any]]) -> list[tuple[int, str | None]]:
    """Lanza todas las peticiones a la vez y devuelve (status, código de error)."""
    barrier = threading.Barrier(len(bodies), timeout=BARRIER_TIMEOUT)
    results: list[tuple[int, str | None]] = []
    lock = threading.Lock()

    def worker(body: dict[str, Any]) -> None:
        barrier.wait()
        response = asyncio.run(_post(body))
        code = None if response.status_code == 201 else response.json()["error"]["code"]
        with lock:
            results.append((response.status_code, code))

    threads = [threading.Thread(target=worker, args=(b,)) for b in bodies]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert len(results) == len(bodies), "alguna petición no terminó"
    return results


def _confirmed(engine: Engine) -> list[tuple[datetime, datetime]]:
    with engine.connect() as conn:
        return [
            (row.start_at, row.end_at)
            for row in conn.execute(
                text(
                    "SELECT start_at, end_at FROM bookings "
                    "WHERE status = 'CONFIRMADA' ORDER BY start_at"
                )
            )
        ]


def _slots(rounds: int) -> list[datetime]:
    """Inicios de 30 min (sin solaparse entre rondas) en días hábiles."""
    days = [datetime(2026, 12, d, 9, 0, tzinfo=TZ) for d in (1, 2, 3, 4, 5)]
    starts = [d + timedelta(minutes=30 * i) for d in days for i in range(20)]
    return starts[:rounds]


def _assert_no_overlaps(rows: list[tuple[datetime, datetime]]) -> None:
    for (s1, e1), (s2, e2) in zip(rows, rows[1:]):
        assert e1 <= s2, f"reservas solapadas: {s1}-{e1} y {s2}-{e2}"


# --------------------------------------------------------------- AC-06 ⭐
def test_concurrent_double_booking(engine: Engine) -> None:
    """AC-06: 2 clientes, mismo barbero y hora, al mismo tiempo → 1×201 y 1×409."""
    ids = _ids(engine)
    outcomes: Counter = Counter()

    for n, start in enumerate(_slots(ROUNDS)):
        results = _race([_body(ids, start, n=1), _body(ids, start, n=2)])
        outcomes[tuple(sorted(results, key=lambda r: r[0]))] += 1
        assert sorted(r[0] for r in results) == [201, 409], f"ronda {n}: {results}"
        assert (409, "SLOT_TAKEN") in results

    rows = _confirmed(engine)
    assert len(rows) == ROUNDS  # exactamente 1 reserva por horario
    _assert_no_overlaps(rows)


def test_concurrent_partial_overlap(engine: Engine) -> None:
    """Corte+Barba 10:00–10:45 vs Corte 10:30–11:00 simultáneos → solo uno gana."""
    ids = _ids(engine)

    for n, base in enumerate(_slots(10)[::2]):  # bloques de 1 h libres
        combo = _body(ids, base, service="Corte+Barba", n=1)
        corte = _body(ids, base + timedelta(minutes=30), service="Corte", n=2)
        results = _race([combo, corte])
        assert sorted(r[0] for r in results) == [201, 409], f"ronda {n}: {results}"

    _assert_no_overlaps(_confirmed(engine))


# ------------------------------------------------- Capa 2 bajo carrera real
def test_db_layer_catches_race(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ambas peticiones pasan la capa 1 a la vez (nadie ve conflicto) → la BD decide."""
    ids = _ids(engine)
    real_find = bookings_repository.find_overlapping
    gate: dict[str, threading.Barrier | None] = {"barrier": None}

    def find_then_wait(*args: Any, **kwargs: Any):
        found = real_find(*args, **kwargs)
        barrier = gate["barrier"]
        if barrier is not None:
            barrier.wait()  # las dos ya consultaron: ninguna vio a la otra
        return found

    monkeypatch.setattr(bookings_repository, "find_overlapping", find_then_wait)

    for n, start in enumerate(_slots(ROUNDS)):
        gate["barrier"] = threading.Barrier(2, timeout=BARRIER_TIMEOUT)
        results = _race([_body(ids, start, n=1), _body(ids, start, n=2)])
        assert sorted(r[0] for r in results) == [201, 409], f"ronda {n}: {results}"

    assert len(_confirmed(engine)) == ROUNDS


# ------------------------------------- Deadlock de PostgreSQL (bug de T6)
def _db_error(exc_type: type[Exception]) -> OperationalError:
    return OperationalError("INSERT INTO bookings ...", {}, exc_type("simulado"))


@pytest.mark.parametrize("pg_error", [DeadlockDetected, SerializationFailure])
def test_deadlock_on_insert_returns_slot_taken(
    engine: Engine, monkeypatch: pytest.MonkeyPatch, pg_error: type[Exception]
) -> None:
    """Reproduce el bug hallado en la revisión de T6: si el INSERT pierde por
    deadlock (o serialización), el perdedor debe recibir 409, no 500.

    Escenario: el ganador ya guardó 10:00; el perdedor no lo vio en la capa 1
    (carrera) y su INSERT es abortado por PostgreSQL con DeadlockDetected.
    """
    ids = _ids(engine)
    start = datetime(2026, 12, 1, 10, 0, tzinfo=TZ)
    first = asyncio.run(_post(_body(ids, start, n=1)))
    assert first.status_code == 201

    real_find = bookings_repository.find_overlapping
    real_add = bookings_repository.add_booking
    calls = {"find": 0, "add": 0}

    def find_misses_once(*args: Any, **kwargs: Any):
        calls["find"] += 1
        return [] if calls["find"] == 1 else real_find(*args, **kwargs)

    def add_deadlocks_once(*args: Any, **kwargs: Any):
        calls["add"] += 1
        if calls["add"] == 1:
            raise _db_error(pg_error)
        return real_add(*args, **kwargs)

    monkeypatch.setattr(bookings_repository, "find_overlapping", find_misses_once)
    monkeypatch.setattr(bookings_repository, "add_booking", add_deadlocks_once)

    response = asyncio.run(_post(_body(ids, start, n=2)))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_TAKEN"
    assert calls["find"] == 2  # reintentó y la capa 1 vio al ganador
    assert len(_confirmed(engine)) == 1


def test_persistent_deadlock_gives_up_with_slot_taken(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si el deadlock se repite, no hay bucle infinito: 1 reintento y luego 409."""
    ids = _ids(engine)
    calls = {"add": 0}

    def always_deadlock(*_args: Any, **_kwargs: Any):
        calls["add"] += 1
        raise _db_error(DeadlockDetected)

    monkeypatch.setattr(bookings_repository, "add_booking", always_deadlock)

    response = asyncio.run(
        _post(_body(ids, datetime(2026, 12, 1, 10, 0, tzinfo=TZ)))
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_TAKEN"
    assert calls["add"] == 2
    assert _confirmed(engine) == []


def test_other_operational_errors_are_not_masked(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Un fallo de BD que NO es una carrera no debe disfrazarse de 409."""
    ids = _ids(engine)

    def connection_lost(*_args: Any, **_kwargs: Any):
        raise OperationalError("INSERT ...", {}, Exception("connection lost"))

    monkeypatch.setattr(bookings_repository, "add_booking", connection_lost)

    with pytest.raises(OperationalError):
        asyncio.run(_post(_body(ids, datetime(2026, 12, 1, 10, 0, tzinfo=TZ))))
