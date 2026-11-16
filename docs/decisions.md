# Decisiones (ADR ligero)

| # | Decisión | Alternativas | Motivo |
|---|----------|--------------|--------|
| D1 | Dominio: **Barbería** | Cancha, tutorías, coworking | Servicios con duraciones distintas hacen más interesante la regla de solapamiento. |
| D2 | FastAPI + React + PostgreSQL | Node, Next.js | Experiencia previa del equipo con FastAPI; Postgres permite exclusion constraint. |
| D3 | No doble reserva garantizada en BD | Solo validación en código | Una validación en código no resiste 2 peticiones simultáneas (RF-07). |
| D4 | Sin login de cliente (código + teléfono) | Cuentas de usuario | Reduce fricción (O2) y alcance del MVP. |
| D5 | Intervalos `[inicio, fin)` | Cerrados | Permite citas pegadas sin choque. |
| D6 | Seed dentro de la migración inicial | Script de seed separado | El catálogo base forma parte del esquema inicial del MVP; garantiza datos deterministas en tests y evita un paso extra en Docker/CI. |
| D7 | Ante `DeadlockDetected` / `SerializationFailure` al insertar una reserva: rollback, **1 reintento** y, si persiste, 409 `SLOT_TAKEN` | Responder 500 · reintentar sin límite · `SERIALIZABLE` o `SELECT … FOR UPDATE` en toda la transacción | En la revisión de T6 (PR #13), 20 carreras HTTP reales contra uvicorn con 4 workers dieron **0 dobles reservas** (la exclusion constraint funcionó) pero **2 respuestas 500**: el log de PostgreSQL mostró dos procesos esperándose mutuamente en `no_double_booking` (`Process A waits for ShareLock on transaction X; blocked by process B` y viceversa). El deadlock es intermitente (en 150 carreras posteriores no se repitió), por eso se cubre con tests **deterministas** que simulan el error en el INSERT, además de las carreras reales. Un reintento basta porque la capa 1 ya ve al ganador; limitarlo evita bucles. |

## Cambios de requerimiento
*(CR-01 se documentará aquí: solicitud → specs afectadas → AC → tareas → commits/PR → tests → resultado.)*
