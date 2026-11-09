# Instrucciones para agentes de IA — BarberBook

Proyecto universitario: sistema de reservas para barbería, desarrollado con **ODD → SDD → código → pruebas**.
La **especificación es la fuente de verdad**; tú eres el ejecutor; los tests son el verificador.

## Metodología (cómo la define el curso)
- **ODD = Outcome-Driven Development** (no "Organic"). Todo parte del resultado para el usuario: `specs/outcomes.md` (O1–O5). Cada cambio debe aportar a un outcome.
- **SDD = Spec-Driven Development.** Especificación = fuente de verdad · IA = ejecutor · tests = verificador. Ciclo: Constitution → Specify → Clarify → Plan → Tasks → Implement → Verify/Converge. Nivel usado: **spec-anchored** (la spec se mantiene viva y se actualiza junto al código).
- **TDD = Test-Driven Development.** Dentro de cada tarea: 🔴 test que falla → 🟢 código mínimo → 🔵 refactor. Los tests salen de los criterios de aceptación (AC), no se inventan para justificar el código.
- **Trazabilidad obligatoria:** Outcome → Requisito (RF) → Regla (BR) → Criterio (AC) → Test. Menciona estos IDs en commits, PRs y reportes.
- **Converge:** si código y spec no coinciden, corrige el código o propone actualizar la spec explícitamente; nunca dejes la diferencia sin resolver.

## Antes de hacer cualquier cosa, lee:
1. `specs/architecture.md` → sección **Constitution** (reglas no negociables)
2. `specs/outcomes.md` → para qué existe el sistema
3. `specs/requirements.md`, `specs/business-rules.md`, `specs/acceptance-criteria.md`
4. `specs/api.md`, `specs/data-model.md`
5. `specs/implementation-plan.md` → la tarea (T#) que te pidan

## Reglas de trabajo
- Implementa **solo la tarea (T#) que se te indique**. Nada de "mejoras" no pedidas.
- **TDD:** escribe primero los tests de los AC de esa tarea (rojo), luego el código mínimo (verde), luego refactor.
- La regla **BR-01 (no doble reserva)** es crítica: nunca la debilites; está garantizada también en BD (`no_double_booking`).
- **No cambies contratos** de `api.md` ni el modelo de `data-model.md` sin detenerte y avisar; si hay que cambiarlos, se actualiza primero la spec.
- Si la spec es **ambigua o contradictoria con el código: detente y pregunta.** No inventes.
- Mantén el diff mínimo. Respeta la estructura `routers/ → services/ → domain/ → repositories/`.
- Zona horaria: America/Panama. Intervalos de reserva `[inicio, fin)`.
- No registres teléfonos completos en logs.

## Cuándo consultar `GUIA-DEL-EQUIPO.md`
No la leas completa (es para humanos). Consúltala solo si la tarea lo requiere:
- **§6** → flujo Git, plantilla de Pull Request.
- **§8** → formato de `docs/ai-log.md`, `docs/decisions.md`, matriz de `docs/testing.md` y ciclo del **cambio de requerimiento (CR)**.

## Stack
Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL 16 · React + Vite + TypeScript · pytest · vitest · Docker Compose.

## Convenciones
- Ramas: `feat/T<n>-nombre` · Commits: `tipo(alcance): mensaje #issue` (feat, test, fix, docs, chore, refactor).
- Tests: nombres de `specs/acceptance-criteria.md` (ej. `test_double_booking_rejected`).
- Comandos: `docker compose up -d db` · `pytest -v` (backend) · `npm test` (frontend).

## Al terminar, reporta
1. Archivos cambiados
2. Tests ejecutados y resultado
3. AC cubiertos
4. Riesgos o dudas pendientes
5. Una línea lista para pegar en `docs/ai-log.md` (Actividad · IA · Solicitud · Resultado · Decisión pendiente del humano)
