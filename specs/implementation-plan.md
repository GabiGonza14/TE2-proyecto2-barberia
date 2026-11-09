# Implementation Plan — Barbería

> Cada tarea: 1 objetivo, dependencias, criterio de aceptación y test. 1 tarea ≈ 1 issue ≈ 1 rama ≈ 1 PR.
> Ramas: `feat/T<n>-nombre`. Roles rotan por ciclo.
> Equipo: **Gabriel González · Isalleth · Derlin**

## Ciclo 1 — Base (Spec Lead: Gabriel · Dev Lead: Isalleth · QA/DevOps: Derlin)
| T | Tarea | Archivos | Dep. | AC / Test |
|---|-------|----------|------|-----------|
| T1 | Repo, Docker Compose (db+api+web), CI con GitHub Actions | `docker-compose.yml`, `.github/workflows/ci.yml` | — | CI verde con test dummy |
| T2 | Modelos + migración (incluye `no_double_booking`) + seed | `models/`, `alembic/` | T1 | Migración aplica; insertar 2 solapadas falla |
| T3 | Reglas puras: `overlaps`, `is_within_hours`, `on_grid`, `in_window`, validación teléfono | `domain/rules.py` | — | Unit tests BR-01…BR-05, BR-09 |
| T4 | GET `/barbers`, `/services` | `routers/catalog.py` | T2 | RF-01, RF-02 |

## Ciclo 2 — Reservar (Spec Lead: Isalleth · Dev Lead: Derlin · QA/DevOps: Gabriel)
| T | Tarea | Archivos | Dep. | AC / Test |
|---|-------|----------|------|-----------|
| T5 | Servicio de disponibilidad + GET `/availability` | `services/availability.py` | T3, T4 | AC-11, AC-12 |
| T6 | POST `/bookings` con transacción + captura de `ExclusionViolation` | `services/booking.py` | T2, T3 | AC-01…AC-05, AC-07…AC-10 |
| T7 | **Test concurrente** de doble reserva | `tests/backend/integration/` | T6 | **AC-06** |

## Ciclo 3 — Gestionar (Spec Lead: Derlin · Dev Lead: Gabriel · QA/DevOps: Isalleth)
| T | Tarea | Archivos | Dep. | AC / Test |
|---|-------|----------|------|-----------|
| T8 | GET `/bookings/{code}` + POST cancelar | `services/booking.py` | T6 | AC-13, AC-14, AC-15 |
| T9 | GET `/admin/agenda` + auth admin | `routers/admin.py` | T6 | AC-16, AC-17 |

## Ciclo 4 — UI y entrega (Spec Lead: Gabriel · Dev Lead: Isalleth · QA/DevOps: Derlin)
| T | Tarea | Dep. | Evidencia |
|---|-------|------|-----------|
| T10 | UI: flujo reservar en 4 pasos (servicio → barbero → hora → datos) | T5, T6 | RNF-05, demo |
| T11 | UI: consultar/cancelar + agenda admin | T8, T9 | demo |
| T12 | Matriz de evidencia en `docs/testing.md` + README final | todo | todos los AC en PASS |

## Cambio de requerimiento (a mitad del proyecto)
Se registrará como **CR-01** siguiendo: cambio solicitado → `requirements.md` / `business-rules.md` → `acceptance-criteria.md` → nueva tarea aquí → código → tests → resultado. Evidencia en `docs/decisions.md`.
