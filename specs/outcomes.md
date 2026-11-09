# Outcomes — Sistema de Reservas para Barbería (Fase 1 · ODD)

> **Pregunta guía:** ¿Qué resultado queremos conseguir para el usuario?
> *(no: "¿qué aplicación queremos programar?")*

---

## 1. Contexto del negocio

Barbería de barrio con **3 barberos**, horario de **martes a sábado, 9:00–19:00** (domingo y lunes cerrado).
Servicios ofrecidos:

| Servicio        | Duración | Precio ref. |
|-----------------|----------|-------------|
| Corte           | 30 min   | $8          |
| Barba           | 20 min   | $5          |
| Corte + Barba   | 45 min   | $12         |
| Diseño / Fade   | 40 min   | $10         |

## 2. Problema actual

- Los clientes piden cita por **WhatsApp o llamada**; el barbero responde entre corte y corte.
- Se producen **cruces de horario**: dos clientes citados con el mismo barbero a la misma hora.
- El cliente **no sabe qué horas están libres** hasta que alguien le contesta (a veces horas después).
- Los servicios tienen **duraciones distintas**, y se agenda "a ojo" → retrasos en cadena.
- Hay **clientes que no se presentan** y el espacio se pierde.
- El dueño no tiene una **vista clara de la agenda del día** por barbero.

## 3. Actores

| Actor        | Necesidad principal |
|--------------|---------------------|
| **Cliente**  | Reservar rápido, ver horarios libres, elegir barbero, cancelar si no puede ir. |
| **Barbero**  | Ver su agenda del día sin interrupciones por mensajes. |
| **Administrador (dueño)** | Gestionar barberos, servicios y horarios; ver la agenda general. |

## 4. Outcomes (resultados esperados)

| ID | Outcome | Cómo lo medimos (evidencia) |
|----|---------|-----------------------------|
| **O1** | **Cero cruces de horario**: un barbero nunca tiene dos citas que se solapen. | Test automatizado de doble reserva + test concurrente (2 clientes, mismo slot → solo 1 éxito). |
| **O2** | El cliente **encuentra un espacio y reserva sin intervención del personal**, en menos de 2 minutos. | Flujo end-to-end: elegir servicio → barbero → hora → confirmar (≤ 4 pasos). |
| **O3** | El cliente **solo ve horarios realmente disponibles**, según la duración del servicio elegido. | Tests del cálculo de disponibilidad (horario laboral, citas existentes, duración). |
| **O4** | El barbero / admin **ve la agenda del día** por barbero en una sola pantalla. | Endpoint + vista de agenda filtrada por fecha y barbero. |
| **O5** | Se **reduce el espacio perdido**: el cliente puede cancelar y el slot vuelve a quedar libre. | Test: cancelar libera el horario y otro cliente puede reservarlo. |

## 5. Preguntas de exploración (ODD)

Preguntas usadas para entender el valor antes de especificar:

1. ¿Qué le molesta hoy al cliente al pedir una cita? → *esperar respuesta y no saber qué hay libre.*
2. ¿Qué le molesta al barbero? → *contestar mensajes mientras corta; cruces de citas.*
3. ¿El cliente quiere elegir barbero o le da igual? → *ambos casos: elegir uno o "cualquiera disponible".*
4. ¿Con cuánta anticipación se reserva? → *mismo día hasta 14 días antes.*
5. ¿Qué pasa si el cliente llega tarde o no llega? → *se pierde el espacio; necesitamos cancelación.*
6. ¿Hasta cuándo se puede cancelar? → *por definir en business-rules (propuesta: hasta 2 h antes).*
7. ¿Se aceptan clientes sin cita (walk-in)? → *sí, pero fuera del alcance del MVP.*
8. ¿Necesita pago en línea? → *no, se paga en el local.*

## 6. Hipótesis de valor

- **Si** el cliente ve solo horarios libres y reserva solo, **entonces** desaparecen los mensajes de coordinación y los cruces.
- **Si** el sistema calcula los slots con la duración real del servicio, **entonces** se acaban los retrasos en cadena.
- **Si** el cliente puede cancelar fácilmente, **entonces** se recuperan espacios que hoy se pierden.

## 7. Fuera de alcance (MVP)

- Pagos en línea.
- Notificaciones por WhatsApp / SMS / email.
- Clientes walk-in.
- Programa de fidelidad, reseñas.
- Múltiples sucursales.

## 8. Entregas priorizadas (vertical slices)

| # | Slice | Outcomes que cubre |
|---|-------|--------------------|
| S1 | Catálogo: barberos + servicios (consulta) | base |
| S2 | Consultar disponibilidad por barbero, fecha y servicio | O3 |
| S3 | Crear reserva **sin doble reserva** | O1, O2 |
| S4 | Cancelar reserva | O5 |
| S5 | Agenda del día (barbero / admin) | O4 |

## 9. Ideas candidatas para el "cambio de requerimiento" (a mitad del proyecto)

*(El profesor puede pedir otro; estas sirven de reserva para practicar el ciclo de cambio.)*

- Tiempo de **limpieza de 10 min** entre citas del mismo barbero.
- Opción **"cualquier barbero disponible"**.
- **Máximo 1 reserva activa** por cliente por día.
- **Lista de espera** cuando no hay espacio.

---

**Recorrido:** ODD (este archivo) → SDD (`requirements.md`, `business-rules.md`, …) → código → pruebas → valor al usuario.
