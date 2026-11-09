# Acceptance Criteria — Barbería

> Formato **Dado / Cuando / Entonces**. Cada AC tiene su test automatizado (columna *Test*).
> Fecha de ejemplo: martes 2026-12-01. Barbero **B1 = Carlos**, servicio **Corte (30 min)**.

| AC | Requisito / Regla | Escenario | Test |
|----|-------------------|-----------|------|
| **AC-01** | RF-05 | **Dado** B1 libre a las 10:00, **cuando** reservo Corte 10:00, **entonces** 201, estado `CONFIRMADA`, fin 10:30 y código de 6 caracteres. | `test_create_booking_success` |
| **AC-02** ⭐ | RF-06 · BR-01 | **Dado** B1 tiene 10:00–10:30, **cuando** otro cliente reserva B1 10:00, **entonces** 409 `SLOT_TAKEN` y solo existe 1 reserva. | `test_double_booking_rejected` |
| **AC-03** ⭐ | RF-06 · BR-01 | **Dado** B1 tiene 10:00–10:45 (Corte+Barba), **cuando** reservo Corte 10:30, **entonces** 409 (solapamiento parcial). | `test_partial_overlap_rejected` |
| **AC-04** | BR-01 | **Dado** B1 tiene 10:00–10:30, **cuando** reservo B1 10:30, **entonces** 201 (citas pegadas no chocan). | `test_adjacent_bookings_allowed` |
| **AC-05** | BR-01 | **Dado** B1 tiene 10:00, **cuando** reservo **B2** 10:00, **entonces** 201 (otro barbero). | `test_same_time_different_barber_allowed` |
| **AC-06** ⭐ | RF-07 · RNF-01 | **Dado** B1 libre, **cuando** 2 solicitudes simultáneas piden B1 10:00, **entonces** exactamente 1 → 201 y 1 → 409. | `test_concurrent_double_booking` |
| **AC-07** | RF-08 · BR-02 | **Cuando** reservo un lunes, o Corte+Barba a las 18:30 (terminaría 19:15), **entonces** 422 `OUTSIDE_BUSINESS_HOURS`. | `test_outside_business_hours` |
| **AC-08** | BR-04 | **Cuando** reservo a las 10:10, **entonces** 422 `INVALID_START_TIME`. | `test_start_not_on_grid` |
| **AC-09** | BR-05 | **Cuando** reservo ayer → 422 `PAST_DATE`; a 15 días → 422 `TOO_FAR_AHEAD`. | `test_booking_window` |
| **AC-10** | RF-09 · BR-09 | **Cuando** envío teléfono `1234` o nombre vacío, **entonces** 422 `VALIDATION_ERROR` con el campo. | `test_client_validation` |
| **AC-11** | RF-03 | **Dado** B1 tiene 10:00–10:30, **cuando** consulto disponibilidad de Corte, **entonces** 09:30 sí aparece, 09:45, 10:00 y 10:15 no, 10:30 sí, y el último slot es 18:30. | `test_availability_excludes_taken` |
| **AC-12** | RF-04 | **Cuando** consulto un domingo, **entonces** lista vacía con motivo `CLOSED`. | `test_availability_closed_day` |
| **AC-13** | RF-11 · BR-07 | **Dado** reserva 10:00 con 3 h de anticipación, **cuando** la cancelo, **entonces** queda `CANCELADA` y otro cliente puede reservar B1 10:00. | `test_cancel_frees_slot` |
| **AC-14** | RF-12 · BR-06 | **Dado** faltan 90 min para la cita, **cuando** cancelo, **entonces** 409 `CANCEL_WINDOW_CLOSED`. | `test_cancel_window_closed` |
| **AC-15** | RF-10 · BR-10 | **Cuando** consulto con código correcto y teléfono incorrecto, **entonces** 404. | `test_lookup_requires_phone` |
| **AC-16** | RF-13 | **Dado** 3 reservas del día, **cuando** el admin pide la agenda, **entonces** salen ordenadas por hora y agrupadas por barbero, sin las canceladas. | `test_agenda_of_day` |
| **AC-17** | RF-14 | **Cuando** pido la agenda sin `X-Admin-Key`, **entonces** 401. | `test_agenda_requires_admin` |

⭐ = criterios de la regla **obligatoria** de no doble reserva (O1).

## Definición de "Terminado"
- Todos los AC en verde en CI.
- Cada AC aparece en la matriz de `docs/testing.md` con estado PASS.
