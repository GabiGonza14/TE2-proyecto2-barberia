# Testing

## Estrategia
| Nivel | Herramienta | Qué cubre |
|-------|-------------|-----------|
| Unit | pytest | Reglas puras en `domain/rules.py` (BR-01…BR-05, BR-09) |
| Integración | pytest + httpx + PostgreSQL | Endpoints y AC-01…AC-17 |
| Concurrencia | pytest + threads | AC-06: 2 reservas simultáneas → 1 éxito |
| Frontend | vitest | Componentes del flujo de reserva |

Ejecutar: `docker compose up -d db && pytest -v`

## Matriz de evidencia (Verify & Converge)
| AC | Requisito | Test | Estado |
|----|-----------|------|--------|
| AC-01 | RF-05 | test_create_booking_success | ⏳ |
| AC-02 ⭐ | RF-06 / BR-01 | test_double_booking_rejected | ⏳ |
| AC-03 ⭐ | RF-06 / BR-01 | test_partial_overlap_rejected | ⏳ |
| AC-04 | BR-01 | test_adjacent_bookings_allowed | ⏳ |
| AC-05 | BR-01 | test_same_time_different_barber_allowed | ⏳ |
| AC-06 ⭐ | RF-07 / RNF-01 | test_concurrent_double_booking | ⏳ |
| AC-07 | BR-02 | test_outside_business_hours | ⏳ |
| AC-08 | BR-04 | test_start_not_on_grid | ⏳ |
| AC-09 | BR-05 | test_booking_window | ⏳ |
| AC-10 | BR-09 | test_client_validation | ⏳ |
| AC-11 | RF-03 | test_availability_excludes_taken | ⏳ |
| AC-12 | RF-04 | test_availability_closed_day | ⏳ |
| AC-13 | RF-11 / BR-07 | test_cancel_frees_slot | ⏳ |
| AC-14 | RF-12 / BR-06 | test_cancel_window_closed | ⏳ |
| AC-15 | RF-10 | test_lookup_requires_phone | ⏳ |
| AC-16 | RF-13 | test_agenda_of_day | ⏳ |
| AC-17 | RF-14 | test_agenda_requires_admin | ⏳ |
