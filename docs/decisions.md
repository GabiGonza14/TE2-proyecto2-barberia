# Decisiones (ADR ligero)

| # | Decisión | Alternativas | Motivo |
|---|----------|--------------|--------|
| D1 | Dominio: **Barbería** | Cancha, tutorías, coworking | Servicios con duraciones distintas hacen más interesante la regla de solapamiento. |
| D2 | FastAPI + React + PostgreSQL | Node, Next.js | Experiencia previa del equipo con FastAPI; Postgres permite exclusion constraint. |
| D3 | No doble reserva garantizada en BD | Solo validación en código | Una validación en código no resiste 2 peticiones simultáneas (RF-07). |
| D4 | Sin login de cliente (código + teléfono) | Cuentas de usuario | Reduce fricción (O2) y alcance del MVP. |
| D5 | Intervalos `[inicio, fin)` | Cerrados | Permite citas pegadas sin choque. *(Se mantiene el intervalo semiabierto, pero desde CR-01 / D9 el mismo barbero ya no puede tener citas pegadas.)* |
| D6 | Seed dentro de la migración inicial | Script de seed separado | El catálogo base forma parte del esquema inicial del MVP; garantiza datos deterministas en tests y evita un paso extra en Docker/CI. |
| D7 | Ante `DeadlockDetected` / `SerializationFailure` al insertar una reserva: rollback, **1 reintento** y, si persiste, 409 `SLOT_TAKEN` | Responder 500 · reintentar sin límite · `SERIALIZABLE` o `SELECT … FOR UPDATE` en toda la transacción | En la revisión de T6 (PR #13), 20 carreras HTTP reales contra uvicorn con 4 workers dieron **0 dobles reservas** (la exclusion constraint funcionó) pero **2 respuestas 500**: el log de PostgreSQL mostró dos procesos esperándose mutuamente en `no_double_booking` (`Process A waits for ShareLock on transaction X; blocked by process B` y viceversa). El deadlock es intermitente (en 150 carreras posteriores no se repitió), por eso se cubre con tests **deterministas** que simulan el error en el INSERT, además de las carreras reales. Un reintento basta porque la capa 1 ya ve al ganador; limitarlo evita bucles. |
| D8 | **Clarify del ciclo 3 (T8/T9):** (1) cancelar una reserva ya cancelada → 409 `ALREADY_CANCELLED`; (2) código sin distinción de mayúsculas; (3) cancelar exactamente 2 h antes está permitido; (4) todos los barberos activos aparecen en la agenda; (5) un barbero inactivo aparece solo con reservas confirmadas del día; (6) sin `date`, la agenda usa hoy en America/Panama | Cancelación idempotente · código sensible a mayúsculas · rechazar el borde de 2 h · omitir barberos sin citas · excluir siempre inactivos · exigir `date` | Hace deterministas los contratos de T8/T9, evita revelar códigos existentes, mejora la recuperación de espacios (O5) y mantiene una agenda completa y útil para el admin (O4). |

| D9 | **CR-01 · Limpieza de 10 min:** (1) se compara `[inicio, fin + 10 min)` de ambas reservas, en los dos sentidos; (2) la limpieza no tiene que caber antes de las 19:00; (3) choque con la limpieza → 409 `SLOT_TAKEN`; (4) en BD, columna `blocked_until` con `CHECK = end_at + 10 min` y `no_double_booking` sobre ella; (5) la migración falla si hay reservas existentes que violen la regla | Guardar `end_at` ya con la limpieza · `end_at + interval` dentro de la restricción · función SQL `IMMUTABLE` propia · validar la limpieza solo en código · código de error nuevo `BUFFER_CONFLICT` | Mantiene `end_at` como fin real (agenda y API no cambian); la expresión con `interval` no es `IMMUTABLE` y PostgreSQL la rechaza (verificado); una función `IMMUTABLE` falsa sería frágil; validar solo en código rompería RNF-01 ante concurrencia; para el cliente un choque con la limpieza es igual que un horario ocupado. |

## Cambios de requerimiento

### CR-01 · 10 minutos de limpieza entre citas del mismo barbero
| Paso | Evidencia |
|------|-----------|
| 1. Cambio solicitado | Issue **CR-01 (#21)** (cambio simulado por el equipo, como pide el enunciado): el dueño reporta que los barberos no alcanzan a limpiar y desinfectar entre clientes y las citas pegadas se atrasan en cadena. Pide 10 min libres entre citas del mismo barbero. |
| 2. Especificación | `business-rules.md` → **BR-12** nueva, BR-01 actualizada, Clarify; `requirements.md` → **RF-15** nuevo, RNF-01; `data-model.md` → `blocked_until` y `no_double_booking`; `api.md` → notas de disponibilidad y 409 |
| 3. Criterios | `acceptance-criteria.md` → **AC-04 y AC-11 modificados**, **AC-23, AC-24, AC-25 nuevos** |
| 4. Plan / tareas | `implementation-plan.md` → **T13** (antes de T10) |
| 5. Código | T13 (**#22**, rama `feat/T13-limpieza-entre-citas`): `domain/rules.py` (`CLEANUP_BUFFER`, `blocked_until`), `services/availability.py`, `services/booking.py`, `repositories/bookings.py`, `models/booking.py` (columna, CHECK y listener `before_insert`) y migración `0002_t13_cleanup` (columna → backfill → NOT NULL + CHECK → `no_double_booking` sobre `tstzrange(start_at, blocked_until, '[)')`). Commits 🔴 `808d78e` → 🟢 `5ff6402` |
| 6. Pruebas | Tests primero (rojo): AC-04 `test_buffer_after_booking`, AC-11 `test_availability_excludes_taken`, AC-23 `test_buffer_before_existing_booking`, AC-24 `test_db_enforces_buffer`, AC-25 `test_buffer_may_end_after_closing`; ajustes `test_db_rejects_adjacent_bookings` y fixtures de concurrencia (inicios cada 45 min). En verde: 82 unitarios en local, integración contra PostgreSQL en CI |
| 7. Resultados | PR **#25**; CI en verde (`backend-tests`, `frontend`, `sonarcloud`, `SonarCloud Code Analysis`); AC-04/11/23/24/25 en ✅ en `testing.md`; `api.md` sin cambios (mismo JSON y `end_at` real) |

## Revisión Converge (T12 · cierre)
Se recorrieron las specs contra el código y la evidencia. Diferencias encontradas:

| # | Spec | Hallazgo | Acción |
|---|------|----------|--------|
| C1 | RNF-04 (disponibilidad < 300 ms con ≈ 500 reservas) | No tenía evidencia | **Medido** en T12: p95 = 5 ms con 520 reservas → ✅ (`docs/testing.md`, RNF) |
| C2 | RNF-06 (sin teléfonos en logs) | El *access log* de uvicorn imprime `GET /bookings/{code}?phone=…` con el teléfono completo | **Código corregido** en PR #32: `PhoneMaskingFilter` en `uvicorn.access` deja `phone=***4567` (TDD, 9 tests) ✅ |
| C3 | architecture.md (levantar con `docker compose up`) | `docker compose up` no aplica las migraciones: sin `alembic upgrade head` la API arranca sin tablas | **Corregido en PR #33:** el contenedor `api` ejecuta `alembic upgrade head` (idempotente) antes de uvicorn; el README ya no pide el paso manual ✅ |
| C4 | Pruebas en Docker | `pytest` vacía la tabla `bookings` de la BD a la que apunta; dentro del contenedor esa es la BD de la demo | Documentado en el README: usar `barberbook_test` |
| C5 | AC-01…AC-25 | Los 25 tests de la matriz existen y pasan en CI | Sin diferencias ✅ |

