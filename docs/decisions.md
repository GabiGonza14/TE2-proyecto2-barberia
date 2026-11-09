# Decisiones (ADR ligero)

| # | Decisión | Alternativas | Motivo |
|---|----------|--------------|--------|
| D1 | Dominio: **Barbería** | Cancha, tutorías, coworking | Servicios con duraciones distintas hacen más interesante la regla de solapamiento. |
| D2 | FastAPI + React + PostgreSQL | Node, Next.js | Experiencia previa del equipo con FastAPI; Postgres permite exclusion constraint. |
| D3 | No doble reserva garantizada en BD | Solo validación en código | Una validación en código no resiste 2 peticiones simultáneas (RF-07). |
| D4 | Sin login de cliente (código + teléfono) | Cuentas de usuario | Reduce fricción (O2) y alcance del MVP. |
| D5 | Intervalos `[inicio, fin)` | Cerrados | Permite citas pegadas sin choque. |

## Cambios de requerimiento
*(CR-01 se documentará aquí: solicitud → specs afectadas → AC → tareas → commits/PR → tests → resultado.)*
