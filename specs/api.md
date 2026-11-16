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

## GET /barbers
**200** — solo barberos activos (BR-08), ordenados por `id`.
```json
[
  { "id": 1, "name": "Carlos" },
  { "id": 2, "name": "Luis" },
  { "id": 3, "name": "Andrés" }
]
```

## GET /services
**200** — todos los servicios, ordenados por `id`.
```json
[
  { "id": 1, "name": "Corte", "duration_min": 30, "price": 8.00 },
  { "id": 2, "name": "Barba", "duration_min": 20, "price": 5.00 },
  { "id": 3, "name": "Corte+Barba", "duration_min": 45, "price": 12.00 },
  { "id": 4, "name": "Diseño/Fade", "duration_min": 40, "price": 10.00 }
]
```
`price` es un número decimal en USD (no string).

## GET /availability
**200**
```json
{ "date": "2026-12-01", "barber_id": 1, "service_id": 1,
  "slots": ["09:00", "09:15", "09:30", "10:30"], "reason": null }
```
Día cerrado / fuera de ventana → `"slots": [], "reason": "CLOSED" | "PAST_DATE" | "TOO_FAR_AHEAD"`.

**CR-01 (BR-12):** un slot solo aparece si, además de no solaparse, deja **10 min de limpieza** antes y después de las otras reservas `CONFIRMADA` del barbero. El formato de la respuesta **no cambia**.

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
**CR-01:** si el horario choca solo con la limpieza de otra cita (BR-12), también responde 409 `SLOT_TAKEN`. El cuerpo del 201 **no cambia** (`end_at` es el fin real del servicio, sin limpieza).

**Errores:** 409 `SLOT_TAKEN` · 422 `OUTSIDE_BUSINESS_HOURS` · `INVALID_START_TIME` · `PAST_DATE` · `TOO_FAR_AHEAD` · `VALIDATION_ERROR` · `BARBER_INACTIVE`

## GET /bookings/{code}?phone=61234567
El código no distingue mayúsculas y minúsculas: se normaliza a mayúsculas antes de buscar.

**200** misma forma que el 201 · **404** `NOT_FOUND` con el mismo mensaje genérico si el código no existe o el teléfono no coincide, para no revelar qué códigos existen.

## POST /bookings/{code}/cancel
**Request** `{ "phone": "61234567" }`
**200** `{ "code": "K7P2QX", "status": "CANCELADA" }`
**Errores:** 404 `NOT_FOUND` · 409 `CANCEL_WINDOW_CLOSED` · 409 `ALREADY_CANCELLED`

## GET /admin/agenda?date=&barber_id=
`date` es opcional; si no se envía, se usa la fecha de hoy en America/Panama. `barber_id` también es opcional; si no existe, responde **404** `NOT_FOUND`.

Header `X-Admin-Key: <clave>` · **401** `UNAUTHORIZED` si falta, es incorrecto o la variable `ADMIN_KEY` no está configurada. El 401 incluye `WWW-Authenticate: X-Admin-Key realm="admin"`.

La respuesta incluye todos los barberos activos, aunque no tengan citas (`bookings: []`). Un barbero inactivo aparece solo si tiene reservas `CONFIRMADA` en la fecha consultada. Las reservas canceladas no aparecen y la respuesta no incluye el teléfono del cliente.

Si `barber_id` corresponde a un barbero **inactivo sin reservas confirmadas** en la fecha consultada, responde **200** con `"barbers": []` (no es un 404: el barbero existe).

```json
{
  "date": "2026-12-01",
  "barbers": [
    {
      "barber": "Carlos",
      "bookings": [
        {
          "start": "10:00",
          "end": "10:30",
          "service": "Corte",
          "client": "Ana Pérez",
          "code": "K7P2QX"
        }
      ]
    },
    { "barber": "Luis", "bookings": [] },
    { "barber": "Andrés", "bookings": [] }
  ]
}
```
