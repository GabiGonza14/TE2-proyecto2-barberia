# Business Rules — Barbería

> Reglas no negociables del dominio. Cada una tiene un test (ver `acceptance-criteria.md`).

| ID | Regla | Detalle |
|----|-------|---------|
| **BR-01** | **No doble reserva** | Dos reservas `CONFIRMADA` del mismo barbero no pueden solaparse. Se solapan si `nueva.inicio < existente.fin` **y** `nueva.fin > existente.inicio`. Intervalos semiabiertos `[inicio, fin)`: una cita que termina 10:30 y otra que empieza 10:30 **no** chocan. |
| **BR-02** | Horario laboral | Martes a sábado, 09:00–19:00. La cita debe **empezar y terminar** dentro de ese rango (fin ≤ 19:00). Domingo y lunes cerrado. |
| **BR-03** | Duración por servicio | `fin = inicio + duración del servicio`. Corte 30, Barba 20, Corte+Barba 45, Diseño/Fade 40 min. |
| **BR-04** | Grilla de 15 min | Las horas de inicio válidas van en múltiplos de 15 min (09:00, 09:15, …). |
| **BR-05** | Ventana de reserva | No se puede reservar en el pasado. Máximo **14 días** de anticipación. |
| **BR-06** | Ventana de cancelación | El cliente puede cancelar hasta **2 horas antes** del inicio. |
| **BR-07** | Cancelar libera | Una reserva `CANCELADA` no cuenta para BR-01: el horario vuelve a estar disponible. |
| **BR-08** | Barbero activo | Solo se reserva con barberos activos y servicios existentes. |
| **BR-09** | Datos del cliente | Nombre: 2–60 caracteres. Teléfono Panamá: 8 dígitos empezando por 6 (`6XXX-XXXX`, el guion es opcional). |
| **BR-10** | Identificación de reserva | Cada reserva tiene un **código** único de 6 caracteres (A-Z, 2-9). Consultar o cancelar exige código **+** teléfono. |
| **BR-11** | Zona horaria | Todo se calcula en America/Panama. |

## Estados de una reserva

```
CONFIRMADA ──(cliente cancela ≥ 2h antes)──► CANCELADA
```
*(Estados como `COMPLETADA` o `NO_SHOW` quedan fuera del MVP.)*

## Códigos de error

| Código | HTTP | Regla |
|--------|------|-------|
| `SLOT_TAKEN` | 409 | BR-01 |
| `OUTSIDE_BUSINESS_HOURS` | 422 | BR-02 |
| `INVALID_START_TIME` | 422 | BR-04 |
| `PAST_DATE` | 422 | BR-05 |
| `TOO_FAR_AHEAD` | 422 | BR-05 |
| `CANCEL_WINDOW_CLOSED` | 409 | BR-06 |
| `BARBER_INACTIVE` / `NOT_FOUND` | 422 / 404 | BR-08, BR-10 |
| `VALIDATION_ERROR` | 422 | BR-09 |
| `UNAUTHORIZED` | 401 | RF-14 |

## Preguntas resueltas (Clarify)

| Pregunta | Decisión |
|----------|----------|
| ¿Qué pasa si dos clientes toman el mismo horario a la vez? | Solo uno gana; la BD lo garantiza (BR-01 + RNF-01). |
| ¿Una cita puede terminar después de las 19:00? | No (BR-02). |
| ¿Citas pegadas (10:00–10:30 y 10:30–11:00) chocan? | No, intervalos `[inicio, fin)`. |
| ¿El cliente necesita cuenta/login? | No en el MVP: código + teléfono. |
| ¿Quién ve la agenda? | El admin, con clave `X-Admin-Key`. |
| ¿Zona horaria? | America/Panama. |
