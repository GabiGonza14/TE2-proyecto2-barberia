# 💈 Guía del Equipo — BarberBook (Proyecto 2)

> **Léanla completa antes de tocar código.** Aquí está qué hacemos, cómo trabajamos y qué tenemos que registrar para la nota.
> Equipo: **Gabriel González · Isalleth · Derlin** · Curso: Tópicos Especiales II · Prof. Regis Rivera

---

## 📌 1. ¿Qué estamos construyendo?

Un **sistema de reservas para una barbería** (3 barberos, servicios con duraciones distintas).

| | |
|---|---|
| **Problema** | Las citas se piden por WhatsApp → cruces de horario, el cliente no sabe qué hay libre, se pierden espacios. |
| **Resultado que buscamos** | **Cero cruces** de horario y que el cliente **reserve solo**, viendo únicamente horarios reales. |
| **Stack** | FastAPI · PostgreSQL · React + Vite · pytest · Docker · GitHub Actions |

⚠️ **Lo más importante del proyecto:** el profe exige que la regla **"no permitir doble reserva"** tenga **prueba automatizada obligatoria**. Todo gira alrededor de eso.

---

## 🎯 2. Lo que el profe va a evaluar

> *"No evaluaré la marca de la herramienta. Se evaluará el **proceso**."*

El recorrido que hay que **demostrar**:

```
ODD  →  SDD  →  código  →  pruebas  →  valor al usuario
```

### Checklist de entrega (todo esto tiene que existir en el repo)

- [ ] Repositorio Git
- [ ] Estructura `specs/` + `docs/` + `src/` + `tests/` ✅ *(ya está)*
- [ ] **Issues** (una por tarea)
- [ ] **Commits identificables** (formato acordado, ver §6)
- [ ] **Ramas** por tarea
- [ ] **Pull Requests** con revisión de otro compañero
- [ ] **Pruebas automatizadas** (unitarias, reglas críticas, conflictos de reserva, validaciones de usuario, criterios de aceptación)
- [ ] **Historial de cambios** (sale solo si hacemos bien commits + PRs)
- [ ] **README**
- [ ] Stack justificado en `specs/architecture.md` ✅
- [ ] **`docs/ai-log.md`** con cada uso de IA
- [ ] **Cambio de requerimiento** a mitad del proyecto, documentado de punta a punta
- [ ] Material para la presentación

### Presentación
- 🎲 **El presentador se elige al azar** → los 3 tenemos que entender TODO el proyecto.
- 🔁 El profe **puede pedir un cambio en vivo**. Si las specs y los tests están bien, es: editar spec → editar test → editar código → correr tests.

---

## 🧠 3. Los conceptos (explicado corto)

### ODD — *Outcome-Driven Development*
**Empezar por el resultado, no por la app.**

| ❌ No preguntamos | ✅ Preguntamos |
|---|---|
| "¿Qué aplicación programamos?" | "¿Qué resultado queremos para el usuario?" |

Ejemplo nuestro:
- **Problema:** citas por WhatsApp con cruces.
- **Outcome:** reducir cruces a cero y que el cliente encuentre horarios libres sin hablar con nadie.

📄 Está en **`specs/outcomes.md`** (5 outcomes: O1…O5).

> 💡 En las diapositivas del Tema 9, ODD aparece también como *"Organic Driven Development"* (un enfoque ligero). **Para este proyecto el profe lo usa como *Outcome-Driven*.**

### SDD — *Spec-Driven Development*
**La especificación manda; la IA ejecuta; los tests verifican.**

```
Especificación = fuente de verdad
IA             = ejecutor
Tests          = verificador
```

En vez de decirle a la IA *"hazme una app de reservas"* (código rápido → errores → parches → se pierde el contexto), primero escribimos **qué** debe hacer el sistema, y la IA trabaja **contra ese contrato**.

**El ciclo SDD (7 pasos):**

| # | Paso | Qué es | Dónde lo tenemos |
|---|------|--------|------------------|
| 1 | **Constitution** | Reglas que nunca cambian (stack, "toda regla tiene test"…) | `specs/architecture.md` §1 |
| 2 | **Specify** | Requisitos verificables (*WHEN… THEN el sistema SHALL…*) | `specs/requirements.md` |
| 3 | **Clarify** | Resolver ambigüedades antes de programar. *"No inventes: pregunta."* | `specs/business-rules.md` (Preguntas resueltas) |
| 4 | **Plan** | Arquitectura, datos, API | `architecture.md`, `data-model.md`, `api.md` |
| 5 | **Tasks** | Tareas pequeñas con dependencias y su test | `specs/implementation-plan.md` |
| 6 | **Implement** | La IA implementa **una tarea a la vez** | `src/` |
| 7 | **Verify / Converge** | Demostrar que código = spec (tabla requisito → test → PASS) | `docs/testing.md` |

**Regla clave:** si el código y la spec no coinciden → **se arregla el código, o se actualiza la spec explícitamente**. Nunca se queda "a medias".

### TDD — *Test-Driven Development*
Dentro de cada tarea: **🔴 test que falla → 🟢 código mínimo que pasa → 🔵 refactor.**
SDD dice *qué* construir; TDD ayuda a construirlo bien.

> **Patrón con IA:** humano aprueba spec → IA propone tests → humano valida tests → IA implementa hasta verde → refactor → volver a la spec.

---

## 🗂️ 4. Mapa del repositorio

```
README.md                 ← portada del proyecto
GUIA-DEL-EQUIPO.md        ← este archivo
specs/
  outcomes.md             ← ODD: problema, actores, outcomes O1–O5
  requirements.md         ← RF-01…RF-14, RNF-01…RNF-06
  business-rules.md       ← BR-01…BR-11 + códigos de error
  acceptance-criteria.md  ← AC-01…AC-17 (cada uno = un test)
  architecture.md         ← constitution + stack + componentes
  data-model.md           ← tablas + restricción anti doble reserva
  api.md                  ← endpoints y JSON
  implementation-plan.md  ← tareas T1–T12 por ciclo
docs/
  ai-log.md               ← 📝 REGISTRO DE USO DE IA (obligatorio)
  decisions.md            ← decisiones + cambio de requerimiento
  testing.md              ← estrategia + matriz de evidencia
src/backend · src/frontend
tests/
```

**Trazabilidad** (esto es lo que impresiona en la presentación):
```
O1 (cero cruces) → RF-06 / BR-01 → AC-02, AC-03, AC-06 → test_double_booking_rejected, test_concurrent_double_booking
```

---

## 👥 5. Roles (rotan por ciclo)

| Rol | Responsable de |
|-----|----------------|
| **Spec Lead** | Requisitos, outcomes, specs, backlog/issues. Mantiene las specs al día. |
| **Dev Lead** | Arquitectura e implementación (con la IA). |
| **QA / DevOps Lead** | Tests, CI, integración, revisar PRs, Docker. |

| Ciclo | Tareas | Spec Lead | Dev Lead | QA/DevOps |
|-------|--------|-----------|----------|-----------|
| 1 · Base | T1–T4 | Gabriel | Isalleth | Derlin |
| 2 · Reservar | T5–T7 | Isalleth | Derlin | Gabriel |
| 3 · Gestionar | T8–T9 | Derlin | Gabriel | Isalleth |
| 4 · UI y entrega | T10–T12 | Gabriel | Isalleth | Derlin |

*"Responsable principal" ≠ "único que trabaja". Todos ayudan, pero el responsable responde por esa parte.*

---

## 🔁 6. Cómo trabajamos (flujo Git)

### Una tarea = una issue = una rama = un PR

```
1. Tomar una issue (ej. #5 "T5 · Disponibilidad")  → asignártela
2. git checkout main && git pull
3. git checkout -b feat/T5-disponibilidad
4. Escribir TEST primero (rojo) → código (verde) → refactor
5. Commits pequeños
6. git push -u origin feat/T5-disponibilidad
7. Abrir Pull Request → "Closes #5"
8. Otro compañero revisa y aprueba → merge a main
```

### Formato de commits
```
tipo(alcance): mensaje corto #issue
```
| tipo | uso | ejemplo |
|------|-----|---------|
| `feat` | funcionalidad nueva | `feat(bookings): crear reserva con validación de solape #6` |
| `test` | pruebas | `test(bookings): agregar test concurrente de doble reserva #7` |
| `fix` | corrección | `fix(availability): excluir slots que pasan de las 19:00 #5` |
| `docs` | specs / documentación | `docs(specs): CR-01 tiempo de limpieza entre citas #13` |
| `chore` | config, docker, ci | `chore(ci): agregar GitHub Actions con pytest #1` |
| `refactor` | mejora sin cambiar comportamiento | `refactor(rules): extraer función overlaps #3` |

### Reglas
- ❌ Nunca push directo a `main`.
- ✅ Todo PR lo revisa **alguien distinto** a quien lo hizo.
- ✅ Un PR no se mergea si los tests fallan.
- ✅ Si cambias un endpoint o una regla → **actualiza primero la spec** en el mismo PR.

### Plantilla de PR
```markdown
## Qué hace
Implementa T6 · POST /bookings

## Specs relacionadas
RF-05, RF-06 · BR-01, BR-02 · AC-01…AC-05

## Tests
- [x] test_create_booking_success
- [x] test_double_booking_rejected

## Uso de IA
Registrado en docs/ai-log.md (#7)

Closes #6
```

---

## 🤖 7. Cómo usar la IA (la que quieran)

Pueden usar **cualquier** herramienta: Claude, ChatGPT/Codex, Gemini, Copilot, Cursor, Qwen, DeepSeek, modelos locales… **No importa cuál**, importa **cómo**.

### 🔌 ¿La IA ya conoce el proyecto?
| Herramienta | Contexto |
|---|---|
| **Agentes en el repo** (Claude Code, Codex, Cursor, Copilot VS Code, Gemini CLI, Qwen Code…) | ✅ Cargan solos `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` / `.github/copilot-instructions.md` (ya están en la raíz). |
| **Chats web** (ChatGPT, Gemini, Claude en navegador) | ❌ **Adjunten `AGENTS.md` + las specs de la tarea** al inicio de cada chat. |

⚠️ Si cambian `AGENTS.md`, actualicen también `GEMINI.md` y `.github/copilot-instructions.md` (son copias).

### ✅ Siempre darle contexto con las specs
Plantilla de prompt (contrato con el agente):

```text
Implementa únicamente la tarea T6 del proyecto.

Lee primero:
- specs/architecture.md (sección Constitution)
- specs/requirements.md (RF-05 a RF-09)
- specs/business-rules.md (BR-01 a BR-05, BR-09)
- specs/acceptance-criteria.md (AC-01 a AC-05, AC-07 a AC-10)
- specs/api.md (POST /bookings)

Reglas:
- Primero escribe los tests de los AC indicados, luego el código.
- No cambies contratos de la API sin avisarme.
- Mantén el cambio mínimo.
- Si algo de la spec es ambiguo o contradictorio, PREGUNTA, no inventes.
- Al terminar, dime: archivos cambiados, tests ejecutados y riesgos pendientes.
```

### ❌ No hacer
- *"Hazme el backend completo"* → el profe lo llama *prompt-first* y es justo lo que el tema critica.
- Aceptar el código sin leerlo.
- Aceptar tests de la IA sin verificar que **representan el requisito real** ("false done": los tests pasan pero el requisito no se cumple).

---

## 📝 8. Lo que TENEMOS que registrar

### A) `docs/ai-log.md` — cada vez que usen IA para algo relevante
El profe pide 5 campos: **Actividad · IA utilizada · Solicitud · Resultado · Decisión**.

```markdown
| # | Fecha | Rol | Actividad | IA utilizada | Solicitud (resumen) | Resultado | Decisión humana |
| 3 | 2026-11-12 | Dev Lead (Isalleth) | T2 · Modelos | ChatGPT GPT-5 | Crear modelos SQLAlchemy y migración con exclusion constraint | Modelos + migración | Se aceptó; se corrigió nombre de índice |
```
💡 La columna **"Decisión humana"** es la más importante: demuestra que **nosotros** controlamos, no la IA.
Si la IA se equivocó y lo corregimos → **regístrenlo**, suma puntos.

### B) `docs/decisions.md` — decisiones técnicas
Cuando elijamos algo con alternativas (ej. "usamos X en vez de Y porque…").

### C) `docs/testing.md` — matriz de evidencia
Al terminar cada tarea, el QA Lead cambia ⏳ → ✅ PASS (o ❌ FAIL) en la tabla de AC.

### D) Cambio de requerimiento (CR-01) — obligatorio
A mitad del proyecto llegará (o inventaremos) un cambio. Hay que **mostrar todo el ciclo**:

```
1. Cambio solicitado          → issue "CR-01: ..."
2. Actualizar especificación  → requirements.md / business-rules.md
3. Actualizar criterios       → acceptance-criteria.md (AC nuevos)
4. Actualizar plan/tareas     → implementation-plan.md (T13…)
5. Modificar código           → rama feat/CR-01-...
6. Modificar pruebas          → tests nuevos / ajustados
7. Ver resultados             → tests en verde + captura en decisions.md
```
Todo en **commits y PR separados** para que se vea el historial.
Candidatos (en `outcomes.md` §9): 10 min de limpieza entre citas, "cualquier barbero disponible", máx. 1 reserva por día por cliente, lista de espera.

---

## ✅ 9. Definición de "Terminado" (para cada tarea)

Una tarea está **terminada** solo si:
- [ ] Sus tests existen y pasan (local + CI)
- [ ] Cumple los AC que le tocan
- [ ] PR revisado y aprobado por otro miembro
- [ ] Spec actualizada si algo cambió
- [ ] Uso de IA registrado en `ai-log.md`
- [ ] Matriz de `testing.md` actualizada

---

## 🚀 10. Primeros pasos para cada uno

1. Aceptar la invitación al repo de GitHub.
2. Clonar: `git clone <url-del-repo>`
3. Instalar: **Docker Desktop**, **Python 3.12**, **Node 20+**.
4. Leer en este orden: `outcomes.md` → `business-rules.md` → `acceptance-criteria.md` → `implementation-plan.md`.
5. Revisar las issues de su ciclo y asignarse.
6. Dudas o algo que no les cuadre de las specs → **se discute y se cambia la spec**, no se improvisa en el código.

---

> **Frase para recordar:** *"No especifiques todo el sistema para meses; especifica la próxima entrega valiosa."*
> Y si alguien pregunta en la presentación por qué hicimos algo: **la respuesta está en una spec, un test o el ai-log.**
