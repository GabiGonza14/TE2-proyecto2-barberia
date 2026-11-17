# Testing

## Estrategia
| Nivel | Herramienta | Qué cubre |
|-------|-------------|-----------|
| Unit | pytest | Reglas puras en `domain/rules.py` (BR-01…BR-05, BR-09, BR-12) |
| Integración | pytest + httpx + PostgreSQL | Endpoints y AC-01…AC-25 |
| Concurrencia | pytest + threads | AC-06: 2 reservas simultáneas → 1 éxito |
| Frontend | vitest + Testing Library (jsdom) | Flujos de UI: reservar, consultar/cancelar y agenda (`tests/frontend/`) |
| End-to-end (manual) | Chrome + backend real (PostgreSQL) | Flujos completos de la UI contra la API real (ver "Demo end-to-end real") |

Ejecutar: ver la sección **Pruebas** del [README](../README.md).

## Resumen (cierre · T12)
| Indicador | Resultado |
|-----------|-----------|
| Tests backend (pytest) | **157 passed** (unitarios + integración + concurrencia, PostgreSQL real) |
| Tests frontend (vitest) | **12 passed** (`App`, `BookingFlow`, `ReservationManagement`, `AdminAgenda`) |
| Cobertura | Backend **99 %** (`pytest --cov`) · Frontend **78 %** de líneas (`npm run coverage`) |
| Criterios de aceptación | **AC-01…AC-25: 25/25 ✅ PASS** (matriz abajo) |
| CI (GitHub Actions) | ✅ backend-tests · frontend · SonarCloud (Quality Gate aprobado) |
| Demo end-to-end | ✅ Reservar, 409 por choque real, consultar, cancelar y agenda contra el backend real |

## Evidencia de infraestructura
| Tarea | Criterio | Verificación | Estado |
|-------|----------|--------------|--------|
| T1 · Issue #1 | `docker compose up` levanta `db`, `api` y `web`; `GET /health` responde 200; CI ejecuta `test_health` | `docker compose up --build -d` · `curl http://localhost:8000/health` · `docker compose exec -T api pytest -v` | ✅ PASS local · ✅ PASS CI (GitHub Actions) |
| T2 · Issue #2 | `alembic upgrade head` aplica; la BD rechaza 2 reservas `CONFIRMADA` solapadas; permite solapadas si una está `CANCELADA`; citas pegadas `[10:00,10:30)` y `[10:30,11:00)` (desde T13/BR-12 se rechazan: `test_db_rejects_adjacent_bookings`); seed correcto | `docker compose exec -T api pytest -v` (`test_migration_applies`, `test_db_rejects_overlapping_bookings`, `test_db_allows_overlap_if_cancelled`, `test_db_rejects_adjacent_bookings`, `test_seed_data`) · `alembic check` | ✅ PASS local (6 passed) · ✅ PASS CI (GitHub Actions) |
| T3 · Issue #3 | Reglas puras: solape `[inicio, fin)` (BR-01), horario Mar–Sáb 09:00–19:00 (BR-02), fin = inicio + duración (BR-03), grilla de 15 min (BR-04), ventana de reserva: no pasado, máx. 14 días (BR-05), teléfono `6XXX-XXXX` y nombre de 2–60 caracteres (BR-09), zona horaria America/Panama (BR-11) | `pytest tests/backend/unit -v` (`tests/backend/unit/test_rules.py`, 57 casos) | ✅ PASS local (57 passed) · ✅ PASS CI (GitHub Actions) |
| T4 · Issue #4 | `GET /api/v1/barbers` devuelve solo barberos activos con `id` y `name` (RF-01, BR-08); `GET /api/v1/services` devuelve los 4 servicios con `name`, `duration_min` y `price` numérico (RF-02); `DomainError` responde el formato común con status correcto; la app importa y `/health` responde sin `DB_URL` | `docker compose exec -T api pytest -v` (`test_list_barbers_only_active`, `test_inactive_barber_not_listed`, `test_list_services`, `test_domain_error_format`, `test_health_works_without_db_url`) · `env -u DB_URL pytest -v tests/backend/integration/test_health.py` | ✅ PASS local (68 passed) · ✅ PASS CI (GitHub Actions) |
| T7 · Issue #11 ⭐ | **AC-06**: 2 `POST /bookings` simultáneos (hilos + `Barrier`, sesiones de BD separadas) → exactamente 1×201 y 1×409 `SLOT_TAKEN`, 1 reserva por horario, 0 solapes; solape **parcial** simultáneo; carrera forzada **después** de la capa 1 → la BD (capa 2) decide; `DeadlockDetected` / `SerializationFailure` en el INSERT → 409 tras un reintento; otros errores de BD no se enmascaran | `pytest -v tests/backend/integration/test_concurrency.py` (7 tests, **50 rondas** por carrera, 5 corridas seguidas sin fallos; en la carrera forzada se observaron deadlocks reales de PostgreSQL —1 en 300 rondas— resueltos por el reintento) · prueba de carga manual: uvicorn con 4 workers, 150 carreras HTTP reales | ✅ PASS local (104 passed) · 150/150 carreras = 1×201 + 1×409, 0 respuestas 500, 0 dobles reservas · ✅ PASS CI (GitHub Actions) |
| T8 · Issue #16 | Consultar (`GET /bookings/{code}?phone=`) y cancelar (`POST /bookings/{code}/cancel`): código sin distinguir mayúsculas y mismo 404 si el código no existe o el teléfono no coincide (BR-10); cancelar con ≥ 2 h (2 h exactas sí, 1 h 59 min no) (BR-06); ya cancelada → 409 `ALREADY_CANCELLED`; al cancelar, el horario vuelve a `/availability` y otro cliente puede reservarlo (BR-07); dos cancelaciones simultáneas → 1×200 y 1×409 (`SELECT … FOR UPDATE`) | `pytest -v tests/backend/integration/test_cancel.py tests/backend/unit/test_rules.py` (14 de integración + 8 unitarios, 3 corridas seguidas sin fallos) | ✅ PASS local (127 passed) · ✅ PASS CI (GitHub Actions) |
| T9 · Issue #17 | `GET /api/v1/admin/agenda` con `X-Admin-Key`: agenda del día agrupada por barbero y ordenada por hora, sin canceladas ni otros días (AC-16); 401 sin clave, con clave incorrecta o sin `ADMIN_KEY` configurada, y la autenticación va antes que la validación (AC-17); barberos activos sin citas con `bookings: []` (AC-21); inactivo solo si tiene citas ese día (D8); sin `date` usa hoy (AC-22); filtro `barber_id`, barbero inexistente → 404, fecha inválida → 422; la respuesta no incluye el teléfono | `pytest -v tests/backend/integration/test_agenda.py` (14 tests, 3 corridas seguidas sin fallos) | ✅ PASS local (141 passed) · ✅ PASS CI (GitHub Actions) |
| Infra · Issue #15 | CORS limitado al frontend (`http://localhost:5173`, configurable con `CORS_ORIGINS`, `*` rechazado), preflight de `POST /bookings` y de `X-Admin-Key`, origen desconocido sin cabecera; hot reload (uvicorn `--reload` y Vite por sondeo); vitest con test mínimo; CI con job `frontend` (build + vitest) y cobertura (`coverage.xml` + `lcov.info`) para SonarCloud | `pytest -v tests/backend/integration/test_cors.py tests/backend/unit/test_config.py` (8 tests) · `pytest --cov` (99 % backend) · `cd src/frontend && npm run build && npm test` · prueba manual: `uvicorn --reload` con `WATCHFILES_FORCE_POLLING=true` recarga al tocar un archivo · revisión QA: el dev server de Vite responde 403 a `/@fs/` fuera del frontend (antes, en Docker, `/@fs/etc/passwd` devolvía el archivo) | ✅ PASS local (150 passed + 1 vitest) · ✅ PASS CI (GitHub Actions: backend-tests, frontend, SonarCloud) |
| T13 · Issue #22 (CR-01) | **BR-12**: 10 min de limpieza entre citas del mismo barbero; se compara `[inicio, fin + 10)` con `[inicio, blocked_until)` de las `CONFIRMADA`; la **cita** termina ≤ 19:00, la **limpieza** no (AC-25); columna `blocked_until` (TIMESTAMPTZ NOT NULL) con CHECK `= end_at + interval '10 minutes'` y `no_double_booking` sobre `tstzrange(start_at, blocked_until, '[)')`; la API sigue devolviendo el `end_at` real | `pytest -v tests/backend/integration/test_bookings.py tests/backend/integration/test_availability.py tests/backend/integration/test_no_double_booking.py tests/backend/unit/test_rules.py` (`test_buffer_after_booking`, `test_availability_excludes_taken`, `test_buffer_before_existing_booking`, `test_db_enforces_buffer`, `test_buffer_may_end_after_closing`, `test_db_rejects_adjacent_bookings`, `test_blocked_until_*`) · `alembic upgrade head --sql` (SQL de la migración) | ✅ PASS CI (GitHub Actions: backend-tests con PostgreSQL real, frontend, SonarCloud) |
| T10 · Issue #26 | **RNF-05**: reserva autónoma en 4 pasos con "Atrás" (Servicio → Barbero → Hora → Datos) y confirmación; `VITE_API_URL` (por defecto `http://localhost:8000/api/v1`); `reason` CLOSED/PAST_DATE/TOO_FAR_AHEAD con mensaje claro; teléfono `6XXX-XXXX` validado en el campo; 409 `SLOT_TAKEN` avisa, vuelve al paso 3 y **recarga** `/availability`; `start_at` en `-05:00` y horas mostradas en America/Panama; el teléfono nunca se registra en consola; diseño claro con los tokens de la issue (Bricolage Grotesque + Manrope, ticket lateral, franjas de poste, ≤ 200 ms y `prefers-reduced-motion`) | `cd src/frontend && npm test` → 5 tests en verde (`tests/frontend/BookingFlow.test.tsx`: flujo completo a confirmación con código, 409 SLOT_TAKEN → paso 3 + segunda llamada a `/availability`, teléfono inválido bloquea el envío sin `POST`, día CLOSED muestra el motivo; `App.test.tsx` sigue en verde) · `npm run build` (tsc + vite) · demo manual de los 4 pasos y la confirmación contra una **API mock** que respeta `api.md` (`src/frontend/dev/mock-server.mjs`, no se usa en build ni tests) en escritorio y móvil → capturas abajo | ✅ PASS local (5 vitest + build) · ✅ PASS CI · ✅ Demo end-to-end real (QA, PR #29): capturas con API mock de la Dev + demo contra el backend real abajo |
| T11 · Issue #27 | **O5 (RF-10…RF-12) + O4 (RF-13, RF-14)**: "Mi reserva" con código (sin distinguir mayúsculas) + teléfono → detalle en el mismo ticket de T10 con badge CONFIRMADA/CANCELADA; cancelación con confirmación en línea, 404 genérico, 409 `CANCEL_WINDOW_CLOSED`, 409 `ALREADY_CANCELLED` y 422 en el campo de `details.field`; agenda del admin con clave escrita por el usuario y guardada solo en memoria (nunca `VITE_*`, `localStorage` ni `sessionStorage`) enviada en `X-Admin-Key`, fecha de hoy en America/Panama, filtro por barbero, "Sin citas", 401 → "Clave de administrador inválida" y pedir la clave otra vez, "Salir" la borra; navegación por hash (`#/reservar`, `#/mi-reserva`, `#/agenda`) sin router ni dependencias nuevas; ni teléfonos ni clave en consola (RNF-06) | `cd src/frontend && npm test` → 12 tests en verde (`ReservationManagement.test.tsx`: consulta correcta, 404, cancelar → CANCELADA sin botón, 409 ventana cerrada; `AdminAgenda.test.tsx`: cabecera `X-Admin-Key`, "Sin citas", 401 vuelve a pedir la clave, la clave no sale de `import.meta.env` y "Salir" la borra; siguen en verde `BookingFlow.test.tsx` y `App.test.tsx`) · `npm run build` (tsc + vite) · demo manual contra la API mock ampliada (`src/frontend/dev/mock-server.mjs`: `GET /bookings/{code}`, `POST /bookings/{code}/cancel`, `GET /admin/agenda`, con casos 404/409/401) en escritorio y móvil → capturas abajo | ✅ PASS local (12 vitest + build) · ✅ PASS CI · ✅ Demo end-to-end real (QA, PR #30): capturas con API mock de la Dev + demo contra el backend real abajo |

| T12 · Issue #28 | Evidencia final y README: matriz AC-01…AC-25 verificada contra los tests reales (25/25 existen y pasan); RNF-01…RNF-06 con evidencia; demo end-to-end real de la UI; README para levantar el proyecto sin ayuda; revisión Converge specs ↔ código | `pytest --cov` (157 passed, 99 %) · `npm run coverage` (12 passed) · demo con Chrome contra backend + PostgreSQL reales (capturas abajo) · medición RNF-04 con 520 reservas | ✅ PASS local · ✅ PASS CI |

## Requisitos no funcionales
| RNF | Evidencia | Estado |
|-----|-----------|--------|
| RNF-01 No doble reserva también en BD | Exclusion constraint `no_double_booking` (desde CR-01 sobre `blocked_until`) · `test_db_rejects_overlapping_bookings`, `test_db_enforces_buffer`, `test_concurrent_double_booking` (50 rondas) | ✅ |
| RNF-02 America/Panama | `domain/rules.py` (`TZ`) · tests de reglas con horas locales · la UI envía `-05:00` y muestra hora de Panamá | ✅ |
| RNF-03 Cada BR con test | BR-01…BR-12 cubiertas en `tests/backend/unit/test_rules.py` e integración (ver matriz) | ✅ |
| RNF-04 Disponibilidad < 300 ms con ≈ 500 reservas | Medición T12: 520 reservas `CONFIRMADA` en 14 días y 3 barberos → 50 consultas a `/availability`: **p50 3,1 ms · p95 5,0 ms · máx 11,2 ms** (uvicorn local + PostgreSQL 16) | ✅ |
| RNF-05 Reserva en ≤ 4 pasos | `BookingFlow.test.tsx` + demo real (Servicio → Barbero → Hora → Datos) | ✅ |
| RNF-06 Sin teléfonos en logs | La app no registra teléfonos y la UI no los muestra en consola (demo real) · **⚠️ Hallazgo T12 (Converge):** el *access log* de uvicorn imprime la URL completa de `GET /bookings/{code}?phone=…`, así que el teléfono **sí** queda en el log (`"GET /api/v1/bookings/ABCDEF?phone=6123-4567 HTTP/1.1" 404`). Corrección pendiente en un PR aparte (filtro que enmascare `phone` en `uvicorn.access`, con test) | ⚠️ |

## Demo end-to-end real (QA · T12)
Frontend (Vite) + API (FastAPI) + PostgreSQL 16 reales, navegador Chrome. **Sin mocks.**

| Paso | Captura | Qué demuestra |
|------|---------|---------------|
| 1 · Reservar: hora | ![hora](evidencias/T12/1-reservar-hora.jpg) | Ticket lateral, slots Mañana/Tarde del backend |
| 2 · Choque real (409) | ![409](evidencias/T12/2-reservar-409-recarga.jpg) | Otro cliente toma las 11:00 → aviso, vuelve al paso 3 y recarga: desaparecen 11:00 y 10:45 (limpieza de CR-01) |
| 3 · Confirmada | ![confirmada](evidencias/T12/3-reservar-confirmada.jpg) | Código de reserva y horas reales `12:00 – 12:30` |
| 4 · Mi reserva | ![mi reserva](evidencias/T12/4-mi-reserva-confirmar.jpg) | Búsqueda con el código en minúsculas (BR-10) y confirmación de cancelar |
| 5 · Cancelada | ![cancelada](evidencias/T12/5-mi-reserva-cancelada.jpg) | Estado `CANCELADA`, sin botón de cancelar (BR-07) |
| 6 · Agenda | ![agenda](evidencias/T12/6-agenda.jpg) | Agenda del admin con `X-Admin-Key`: solo la cita confirmada; la cancelada no aparece; "Sin citas" |
| 7 · Móvil | ![móvil](evidencias/T12/7-movil-reservar.jpg) | Una columna (390 px) |

### T10 · Capturas de la demo manual (API mock, sin Docker en esta máquina)

Escritorio (1280 px) y móvil (390 px). Flujo: Corte → Carlos o Luis → 09:00/11:00 → datos → confirmación.

| Paso | Escritorio | Móvil |
|------|-----------|-------|
| 1 · Servicio | ![T10 escritorio paso 1](evidencias/T10/desktop-1-servicio.jpg) | ![T10 móvil paso 1](evidencias/T10/mobile-1-servicio.jpg) |
| 2 · Barbero | ![T10 escritorio paso 2](evidencias/T10/desktop-2-barbero.jpg) | ![T10 móvil paso 2](evidencias/T10/mobile-2-barbero.jpg) |
| 3 · Hora | ![T10 escritorio paso 3](evidencias/T10/desktop-3-hora.jpg) | ![T10 móvil paso 3](evidencias/T10/mobile-3-hora.jpg) |
| 4 · Datos | ![T10 escritorio paso 4](evidencias/T10/desktop-4-datos.jpg) | ![T10 móvil paso 4](evidencias/T10/mobile-4-datos.jpg) |
| Confirmación | ![T10 escritorio confirmación](evidencias/T10/desktop-5-confirmacion.jpg) | ![T10 móvil confirmación](evidencias/T10/mobile-5-confirmacion.jpg) |

### T11 · Capturas de la demo manual (API mock, sin Docker en esta máquina)

Escritorio (1280 px) y móvil (390 px). Reserva de ejemplo: `UBCDDE` (Luis, Corte+Barba). La demo real con backend va a cargo de QA.

| Caso | Escritorio | Móvil |
|------|-----------|-------|
| Consultar la reserva | ![T11 escritorio consultar](evidencias/T11/desktop-1-consultar.jpg) | ![T11 móvil consultar](evidencias/T11/mobile-1-consultar.jpg) |
| Cancelar: confirmación | ![T11 escritorio cancelar antes](evidencias/T11/desktop-2-cancelar-antes.jpg) | ![T11 móvil cancelar antes](evidencias/T11/mobile-2-cancelar-antes.jpg) |
| Cancelada (sin botón) | ![T11 escritorio cancelada](evidencias/T11/desktop-3-cancelada.jpg) | ![T11 móvil cancelada](evidencias/T11/mobile-3-cancelada.jpg) |
| Error 404 | ![T11 escritorio error 404](evidencias/T11/desktop-4-error-404.jpg) | ![T11 móvil error 404](evidencias/T11/mobile-4-error-404.jpg) |
| Agenda con citas y "Sin citas" | ![T11 escritorio agenda](evidencias/T11/desktop-5-agenda.jpg) | ![T11 móvil agenda](evidencias/T11/mobile-5-agenda.jpg) |
| Agenda filtrada sin citas | ![T11 escritorio agenda sin citas](evidencias/T11/desktop-6-agenda-sin-citas.jpg) | — |
| Clave de administrador inválida | ![T11 escritorio clave inválida](evidencias/T11/desktop-7-clave-invalida.jpg) | ![T11 móvil clave inválida](evidencias/T11/mobile-6-clave-invalida.jpg) |

## Matriz de evidencia (Verify & Converge)
| AC | Requisito | Test | Estado |
|----|-----------|------|--------|
| AC-01 | RF-05 | test_create_booking_success | ✅ PASS |
| AC-02 ⭐ | RF-06 / BR-01 | test_double_booking_rejected | ✅ PASS |
| AC-03 ⭐ | RF-06 / BR-01 | test_partial_overlap_rejected | ✅ PASS |
| AC-04 ✏️ | BR-01 / BR-12 | test_buffer_after_booking | ✅ PASS |
| AC-05 | BR-01 | test_same_time_different_barber_allowed | ✅ PASS |
| AC-06 ⭐ | RF-07 / RNF-01 | test_concurrent_double_booking | ✅ PASS |
| AC-07 | BR-02 | test_outside_business_hours | ✅ PASS |
| AC-08 | BR-04 | test_start_not_on_grid | ✅ PASS |
| AC-09 | BR-05 | test_booking_window | ✅ PASS |
| AC-10 | BR-09 | test_client_validation | ✅ PASS |
| AC-11 ✏️ | RF-03 / RF-15 | test_availability_excludes_taken | ✅ PASS |
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
| AC-23 🆕 | RF-15 / BR-12 | test_buffer_before_existing_booking | ✅ PASS |
| AC-24 🆕 | RNF-01 / BR-12 | test_db_enforces_buffer | ✅ PASS |
| AC-25 🆕 | BR-02 / BR-12 | test_buffer_may_end_after_closing | ✅ PASS |

✏️ = AC modificado por CR-01 · 🆕 = AC nuevo de CR-01.

**Verificación T12:** los 25 tests de la matriz existen en `tests/backend/` (comprobado por nombre) y pasan en CI con PostgreSQL real.
