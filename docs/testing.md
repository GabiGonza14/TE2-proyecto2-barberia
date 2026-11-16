# Testing

## Estrategia
| Nivel | Herramienta | Qué cubre |
|-------|-------------|-----------|
| Unit | pytest | Reglas puras en `domain/rules.py` (BR-01…BR-05, BR-09) |
| Integración | pytest + httpx + PostgreSQL | Endpoints y AC-01…AC-17 |
| Concurrencia | pytest + threads | AC-06: 2 reservas simultáneas → 1 éxito |
| Frontend | vitest | Componentes del flujo de reserva |

Ejecutar: `docker compose up -d db && pytest -v`

## Evidencia de infraestructura
| Tarea | Criterio | Verificación | Estado |
|-------|----------|--------------|--------|
| T1 · Issue #1 | `docker compose up` levanta `db`, `api` y `web`; `GET /health` responde 200; CI ejecuta `test_health` | `docker compose up --build -d` · `curl http://localhost:8000/health` · `docker compose exec -T api pytest -v` | ✅ PASS local · ✅ PASS CI (GitHub Actions) |
| T2 · Issue #2 | `alembic upgrade head` aplica; la BD rechaza 2 reservas `CONFIRMADA` solapadas; permite solapadas si una está `CANCELADA`; permite citas pegadas `[10:00,10:30)` y `[10:30,11:00)`; seed correcto | `docker compose exec -T api pytest -v` (`test_migration_applies`, `test_db_rejects_overlapping_bookings`, `test_db_allows_overlap_if_cancelled`, `test_db_allows_adjacent_bookings`, `test_seed_data`) · `alembic check` | ✅ PASS local (6 passed) · ✅ PASS CI (GitHub Actions) |
| T3 · Issue #3 | Reglas puras: solape `[inicio, fin)` (BR-01), horario Mar–Sáb 09:00–19:00 (BR-02), fin = inicio + duración (BR-03), grilla de 15 min (BR-04), ventana de reserva: no pasado, máx. 14 días (BR-05), teléfono `6XXX-XXXX` y nombre de 2–60 caracteres (BR-09), zona horaria America/Panama (BR-11) | `pytest tests/backend/unit -v` (`tests/backend/unit/test_rules.py`, 57 casos) | ✅ PASS local (57 passed) · CI en el PR |
| T4 · Issue #4 | `GET /api/v1/barbers` devuelve solo barberos activos con `id` y `name` (RF-01, BR-08); `GET /api/v1/services` devuelve los 4 servicios con `name`, `duration_min` y `price` numérico (RF-02); `DomainError` responde el formato común con status correcto; la app importa y `/health` responde sin `DB_URL` | `docker compose exec -T api pytest -v` (`test_list_barbers_only_active`, `test_inactive_barber_not_listed`, `test_list_services`, `test_domain_error_format`, `test_health_works_without_db_url`) · `env -u DB_URL pytest -v tests/backend/integration/test_health.py` | ✅ PASS local (68 passed) · CI en el PR |

## Matriz de evidencia (Verify & Converge)
| AC | Requisito | Test | Estado |
|----|-----------|------|--------|
| AC-01 | RF-05 | test_create_booking_success | ✅ PASS |
| AC-02 ⭐ | RF-06 / BR-01 | test_double_booking_rejected | ✅ PASS |
| AC-03 ⭐ | RF-06 / BR-01 | test_partial_overlap_rejected | ✅ PASS |
| AC-04 | BR-01 | test_adjacent_bookings_allowed | ✅ PASS |
| AC-05 | BR-01 | test_same_time_different_barber_allowed | ✅ PASS |
| AC-06 ⭐ | RF-07 / RNF-01 | test_concurrent_double_booking | ⏳ |
| AC-07 | BR-02 | test_outside_business_hours | ✅ PASS |
| AC-08 | BR-04 | test_start_not_on_grid | ✅ PASS |
| AC-09 | BR-05 | test_booking_window | ✅ PASS |
| AC-10 | BR-09 | test_client_validation | ✅ PASS |
| AC-11 | RF-03 | test_availability_excludes_taken | ✅ PASS |
| AC-12 | RF-04 | test_availability_closed_day | ✅ PASS |
| AC-13 | RF-11 / BR-07 | test_cancel_frees_slot | ⏳ |
| AC-14 | RF-12 / BR-06 | test_cancel_window_closed | ⏳ |
| AC-15 | RF-10 | test_lookup_requires_phone | ⏳ |
| AC-16 | RF-13 | test_agenda_of_day | ⏳ |
| AC-17 | RF-14 | test_agenda_requires_admin | ⏳ |
