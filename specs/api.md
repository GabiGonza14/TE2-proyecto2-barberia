# API — Barbería (`/api/v1`)

Formato de error común:
```json
{ "error": { "code": "SLOT_TAKEN", "message": "El barbero ya tiene una cita en ese horario", "details": {} } }
```

| Método | Ruta | Descripción | Req. |
|--------|------|-------------|------|
| GET | `/barbers` | Barberos activos | RF-01 |
| GET | `/services` | Servicios | RF-02 |
| GET | `/availability?barber_id=&service_id=&date=YYYY-MM-DD` | Slots libres | RF-03, RF-04 |
| POST | `/bookings` | Crear reserva | RF-05…09 |
| GET | `/bookings/{code}?phone=` | Consultar reserva | RF-10 |
| POST | `/bookings/{code}/cancel` | Cancelar | RF-11, RF-12 |
| GET | `/admin/agenda?date=&barber_id=` | Agenda (header `X-Admin-Key`) | RF-13, RF-14 |

## GET /availability
**200**
```json
{ "date": "2026-12-01", "barber_id": 1, "service_id": 1,
  "slots": ["09:00", "09:15", "09:30", "10:30"], "reason": null }
```
Día cerrado / fuera de ventana → `"slots": [], "reason": "CLOSED" | "PAST_DATE" | "TOO_FAR_AHEAD"`.

## POST /bookings
**Request**
```json
{ "barber_id": 1, "service_id": 1, "start_at": "2026-12-01T10:00:00-05:00",
  "client_name": "Ana Pérez", "client_phone": "6123-4567" }
```
**201**
```json
{ "code": "K7P2QX", "status": "CONFIRMADA", "barber": "Carlos", "service": "Corte",
  "start_at": "2026-12-01T10:00:00-05:00", "end_at": "2026-12-01T10:30:00-05:00" }
```
**Errores:** 409 `SLOT_TAKEN` · 422 `OUTSIDE_BUSINESS_HOURS` · `INVALID_START_TIME` · `PAST_DATE` · `TOO_FAR_AHEAD` · `VALIDATION_ERROR` · `BARBER_INACTIVE`

## GET /bookings/{code}?phone=61234567
**200** misma forma que el 201 · **404** `NOT_FOUND` si código o teléfono no coinciden.

## POST /bookings/{code}/cancel
**Request** `{ "phone": "61234567" }`
**200** `{ "code": "K7P2QX", "status": "CANCELADA" }`
**Errores:** 404 `NOT_FOUND` · 409 `CANCEL_WINDOW_CLOSED`

## GET /admin/agenda?date=2026-12-01
Header `X-Admin-Key: <clave>` · **401** sin clave.
```json
{ "date": "2026-12-01",
  "barbers": [ { "barber": "Carlos",
                 "bookings": [ { "start": "10:00", "end": "10:30", "service": "Corte",
                                 "client": "Ana Pérez", "code": "K7P2QX" } ] } ] }
```
