# Testing

## Estrategia
| Nivel | Herramienta | Qué cubre |
|-------|-------------|-----------|
| Unit | pytest | Reglas puras en `domain/rules.py` (BR-01…BR-05, BR-09) |
| Integración | pytest + httpx + PostgreSQL | Endpoints y AC-01…AC-17 |
| Concurrencia | pytest + threads | AC-06: 2 reservas simultáneas → 1 éxito |
| Frontend | vitest + Testing Library (jsdom) | Componentes del flujo de reserva (`tests/frontend/`) |

Ejecutar: `docker compose up -d db && pytest -v`

## Evidencia de infraestructura
| Tarea | Criterio | Verificación | Estado |
|-------|----------|--------------|--------|
| T1 · Issue #1 | `docker compose up` levanta `db`, `api` y `web`; `GET /health` responde 200; CI ejecuta `test_health` | `docker compose up --build -d` · `curl http://localhost:8000/health` · `docker compose exec -T api pytest -v` | ✅ PASS local · ✅ PASS CI (GitHub Actions) |
| T2 · Issue #2 | `alembic upgrade head` aplica; la BD rechaza 2 reservas `CONFIRMADA` solapadas; permite solapadas si una está `CANCELADA`; permite citas pegadas `[10:00,10:30)` y `[10:30,11:00)`; seed correcto | `docker compose exec -T api pytest -v` (`test_migration_applies`, `test_db_rejects_overlapping_bookings`, `test_db_allows_overlap_if_cancelled`, `test_db_allows_adjacent_bookings`, `test_seed_data`) · `alembic check` | ✅ PASS local (6 passed) · ✅ PASS CI (GitHub Actions) |
| T3 · Issue #3 | Reglas puras: solape `[inicio, fin)` (BR-01), horario Mar–Sáb 09:00–19:00 (BR-02), fin = inicio + duración (BR-03), grilla de 15 min (BR-04), ventana de reserva: no pasado, máx. 14 días (BR-05), teléfono `6XXX-XXXX` y nombre de 2–60 caracteres (BR-09), zona horaria America/Panama (BR-11) | `pytest tests/backend/unit -v` (`tests/backend/unit/test_rules.py`, 57 casos) | ✅ PASS local (57 passed) · ✅ PASS CI (GitHub Actions) |
| T4 · Issue #4 | `GET /api/v1/barbers` devuelve solo barberos activos con `id` y `name` (RF-01, BR-08); `GET /api/v1/services` devuelve los 4 servicios con `name`, `duration_min` y `price` numérico (RF-02); `DomainError` responde el formato común con status correcto; la app importa y `/health` responde sin `DB_URL` | `docker compose exec -T api pytest -v` (`test_list_barbers_only_active`, `test_inactive_barber_not_listed`, `test_list_services`, `test_domain_error_format`, `test_health_works_without_db_url`) · `env -u DB_URL pytest -v tests/backend/integration/test_health.py` | ✅ PASS local (68 passed) · ✅ PASS CI (GitHub Actions) |
| T7 · Issue #11 ⭐ | **AC-06**: 2 `POST /bookings` simultáneos (hilos + `Barrier`, sesiones de BD separadas) → exactamente 1×201 y 1×409 `SLOT_TAKEN`, 1 reserva por horario, 0 solapes; solape **parcial** simultáneo; carrera forzada **después** de la capa 1 → la BD (capa 2) decide; `DeadlockDetected` / `SerializationFailure` en el INSERT → 409 tras un reintento; otros errores de BD no se enmascaran | `pytest -v tests/backend/integration/test_concurrency.py` (7 tests, **50 rondas** por carrera, 5 corridas seguidas sin fallos; en la carrera forzada se observaron deadlocks reales de PostgreSQL —1 en 300 rondas— resueltos por el reintento) · prueba de carga manual: uvicorn con 4 workers, 150 carreras HTTP reales | ✅ PASS local (104 passed) · 150/150 carreras = 1×201 + 1×409, 0 respuestas 500, 0 dobles reservas · ✅ PASS CI (GitHub Actions) |
| T8 · Issue #16 | Consultar (`GET /bookings/{code}?phone=`) y cancelar (`POST /bookings/{code}/cancel`): código sin distinguir mayúsculas y mismo 404 si el código no existe o el teléfono no coincide (BR-10); cancelar con ≥ 2 h (2 h exactas sí, 1 h 59 min no) (BR-06); ya cancelada → 409 `ALREADY_CANCELLED`; al cancelar, el horario vuelve a `/availability` y otro cliente puede reservarlo (BR-07); dos cancelaciones simultáneas → 1×200 y 1×409 (`SELECT … FOR UPDATE`) | `pytest -v tests/backend/integration/test_cancel.py tests/backend/unit/test_rules.py` (14 de integración + 8 unitarios, 3 corridas seguidas sin fallos) | ✅ PASS local (127 passed) · ✅ PASS CI (GitHub Actions) |
| T9 · Issue #17 | `GET /api/v1/admin/agenda` con `X-Admin-Key`: agenda del día agrupada por barbero y ordenada por hora, sin canceladas ni otros días (AC-16); 401 sin clave, con clave incorrecta o sin `ADMIN_KEY` configurada, y la autenticación va antes que la validación (AC-17); barberos activos sin citas con `bookings: []` (AC-21); inactivo solo si tiene citas ese día (D8); sin `date` usa hoy (AC-22); filtro `barber_id`, barbero inexistente → 404, fecha inválida → 422; la respuesta no incluye el teléfono | `pytest -v tests/backend/integration/test_agenda.py` (14 tests, 3 corridas seguidas sin fallos) | ✅ PASS local (141 passed) · ✅ PASS CI (GitHub Actions) |
| Infra · Issue #15 | CORS limitado al frontend (`http://localhost:5173`, configurable con `CORS_ORIGINS`, `*` rechazado), preflight de `POST /bookings` y de `X-Admin-Key`, origen desconocido sin cabecera; hot reload (uvicorn `--reload` y Vite por sondeo); vitest con test mínimo; CI con job `frontend` (build + vitest) y cobertura (`coverage.xml` + `lcov.info`) para SonarCloud | `pytest -v tests/backend/integration/test_cors.py tests/backend/unit/test_config.py` (8 tests) · `pytest --cov` (99 % backend) · `cd src/frontend && npm run build && npm test` · prueba manual: `uvicorn --reload` con `WATCHFILES_FORCE_POLLING=true` recarga al tocar un archivo | ✅ PASS local (149 passed + 1 vitest) · ✅ PASS CI (GitHub Actions: backend-tests, frontend, SonarCloud) |

## Matriz de evidencia (Verify & Converge)
| AC | Requisito | Test | Estado |
|----|-----------|------|--------|
| AC-01 | RF-05 | test_create_booking_success | ✅ PASS |
| AC-02 ⭐ | RF-06 / BR-01 | test_double_booking_rejected | ✅ PASS |
| AC-03 ⭐ | RF-06 / BR-01 | test_partial_overlap_rejected | ✅ PASS |
| AC-04 ✏️ | BR-01 / BR-12 | test_buffer_after_booking | ⏳ CR-01 (T13) |
| AC-05 | BR-01 | test_same_time_different_barber_allowed | ✅ PASS |
| AC-06 ⭐ | RF-07 / RNF-01 | test_concurrent_double_booking | ✅ PASS |
| AC-07 | BR-02 | test_outside_business_hours | ✅ PASS |
| AC-08 | BR-04 | test_start_not_on_grid | ✅ PASS |
| AC-09 | BR-05 | test_booking_window | ✅ PASS |
| AC-10 | BR-09 | test_client_validation | ✅ PASS |
| AC-11 ✏️ | RF-03 / RF-15 | test_availability_excludes_taken | ⏳ CR-01 (T13) |
| AC-12 | RF-04 | test_availability_closed_day | ✅ PASS |
| AC-13 | RF-11 / BR-07 | test_cancel_frees_slot | ✅ PASS |
| AC-14 | RF-12 / BR-06 | test_cancel_window_closed | ✅ PASS |
| AC-15 | RF-10 | test_lookup_requires_phone | ✅ PASS |
| AC-16 | RF-13 | test_agenda_of_day | ✅ PASS |
| AC-17 | RF-14 | test_agenda_requires_admin | ✅ PASS |
| AC-18 | RF-11 / BR-06 | test_cancel_exactly_two_hours_before | ✅ PASS |
| AC-19 | RF-11 | test_cancel_already_cancelled | ✅ PASS |
| AC-20 | BR-10 | test_lookup_code_case_insensitive | ✅ PASS |
| AC-21 | RF-13 | test_agenda_lists_barbers_without_bookings | ✅ PASS |
| AC-22 | RF-13 | test_agenda_defaults_to_today | ✅ PASS |
| AC-23 🆕 | RF-15 / BR-12 | test_buffer_before_existing_booking | ⏳ CR-01 (T13) |
| AC-24 🆕 | RNF-01 / BR-12 | test_db_enforces_buffer | ⏳ CR-01 (T13) |
| AC-25 🆕 | BR-02 / BR-12 | test_buffer_may_end_after_closing | ⏳ CR-01 (T13) |

✏️ = AC modificado por CR-01 · 🆕 = AC nuevo de CR-01 · ⏳ = pendiente de implementar.
