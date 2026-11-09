# Requirements — Sistema de Reservas para Barbería

> Derivados de `outcomes.md`. Formato EARS: **WHEN / IF … THEN el sistema SHALL …**
> Cada requisito apunta a un outcome (O#) y tendrá al menos un criterio de aceptación (AC#) y un test.

## 1. Requisitos funcionales

### Catálogo
| ID | Requisito | Outcome |
|----|-----------|---------|
| **RF-01** | WHEN un cliente consulta los barberos, THEN el sistema SHALL listar solo los barberos **activos** (id, nombre). | O2 |
| **RF-02** | WHEN un cliente consulta los servicios, THEN el sistema SHALL listar los servicios con nombre, **duración en minutos** y precio. | O2, O3 |

### Disponibilidad
| ID | Requisito | Outcome |
|----|-----------|---------|
| **RF-03** | WHEN un cliente consulta disponibilidad indicando barbero, servicio y fecha, THEN el sistema SHALL devolver los horarios de inicio en los que el servicio **cabe completo** sin solaparse con otra reserva confirmada y dentro del horario laboral. | O3 |
| **RF-04** | IF la fecha consultada es un día cerrado (domingo o lunes), está en el pasado o a más de 14 días, THEN el sistema SHALL devolver una lista vacía con el motivo. | O3 |

### Reservas
| ID | Requisito | Outcome |
|----|-----------|---------|
| **RF-05** | WHEN un cliente envía una reserva válida (barbero, servicio, fecha-hora de inicio, nombre, teléfono), THEN el sistema SHALL crearla con estado `CONFIRMADA`, calcular la hora de fin según la duración del servicio y devolver un **código de reserva**. | O2 |
| **RF-06** | IF el horario solicitado se **solapa** con otra reserva `CONFIRMADA` del mismo barbero, THEN el sistema SHALL rechazarla con **409 `SLOT_TAKEN`** y no crear nada. | **O1** |
| **RF-07** | IF dos solicitudes llegan **al mismo tiempo** para el mismo barbero y horario solapado, THEN el sistema SHALL aceptar **solo una** y rechazar la otra con 409 `SLOT_TAKEN`. | **O1** |
| **RF-08** | IF la reserva cae fuera del horario laboral, en el pasado o a más de 14 días, THEN el sistema SHALL rechazarla con 422 y el código de error correspondiente. | O3 |
| **RF-09** | IF los datos del cliente no son válidos (nombre o teléfono), THEN el sistema SHALL rechazar con 422 `VALIDATION_ERROR` indicando el campo. | O2 |

### Consulta y cancelación
| ID | Requisito | Outcome |
|----|-----------|---------|
| **RF-10** | WHEN un cliente consulta su reserva con código + teléfono, THEN el sistema SHALL mostrar el detalle. IF no coinciden, THEN SHALL responder 404. | O2 |
| **RF-11** | WHEN un cliente cancela con código + teléfono y faltan **2 horas o más** para la cita, THEN el sistema SHALL cambiar el estado a `CANCELADA` y el horario SHALL quedar disponible de nuevo. | O5 |
| **RF-12** | IF faltan menos de 2 horas, THEN el sistema SHALL rechazar la cancelación con 409 `CANCEL_WINDOW_CLOSED`. | O5 |

### Agenda (barbero / admin)
| ID | Requisito | Outcome |
|----|-----------|---------|
| **RF-13** | WHEN el administrador consulta la agenda de una fecha (opcionalmente filtrada por barbero), THEN el sistema SHALL listar las reservas `CONFIRMADA` ordenadas por hora, agrupadas por barbero. | O4 |
| **RF-14** | IF la petición a la agenda no incluye una clave de administrador válida, THEN el sistema SHALL responder 401 `UNAUTHORIZED`. | O4 |

## 2. Requisitos no funcionales

| ID | Requisito |
|----|-----------|
| **RNF-01** | La regla de no-doble-reserva SHALL estar garantizada **también a nivel de base de datos** (no solo en código). |
| **RNF-02** | Todas las horas se manejan en zona horaria **America/Panama** (UTC−5, sin horario de verano). |
| **RNF-03** | Toda regla de negocio (BR-xx) SHALL tener al menos un test automatizado. |
| **RNF-04** | La consulta de disponibilidad SHALL responder en < 300 ms con datos de prueba (≈ 500 reservas). |
| **RNF-05** | El flujo de reserva en la UI SHALL completarse en ≤ 4 pasos (servicio → barbero → hora → datos). |
| **RNF-06** | No se registran teléfonos completos en logs. |

## 3. Trazabilidad Outcome → Requisito

| Outcome | Requisitos |
|---------|------------|
| O1 Cero cruces | RF-06, RF-07, RNF-01 |
| O2 Reserva autónoma | RF-01, RF-02, RF-05, RF-09, RF-10, RNF-05 |
| O3 Solo horarios reales | RF-03, RF-04, RF-08 |
| O4 Agenda del día | RF-13, RF-14 |
| O5 Recuperar espacios | RF-11, RF-12 |
