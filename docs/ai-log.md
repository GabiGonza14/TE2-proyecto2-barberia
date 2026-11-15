# AI Development Log

| # | Fecha | Rol | Actividad | IA utilizada | Solicitud (resumen) | Resultado | Decisión humana |
|---|-------|-----|-----------|--------------|---------------------|-----------|-----------------|
| 1 | 2026-11-09 | Spec Lead | ODD: outcomes | Claude (Opus 5.5) | Definir problema, actores y outcomes medibles para barbería | `specs/outcomes.md` con 5 outcomes y 5 slices | Aprobado; se fijan 3 barberos y horario Mar–Sáb 9–19 |
| 2 | 2026-11-09 | Spec Lead | SDD: specs | Claude (Opus 5.5) | Convertir outcomes en requisitos EARS, reglas, AC, arquitectura, modelo, API y plan | 8 archivos en `specs/` | Se corrigió AC-11 (09:45 sí choca con 10:00) tras revisión |
| 3 | 2026-11-09 | Spec Lead | Guía del equipo | Claude (Opus 5.5) | Documento de onboarding: proyecto, ODD/SDD/TDD, flujo Git, qué registrar | `GUIA-DEL-EQUIPO.md` | Aprobado; roles asignados (Gabriel, Isalleth, Derlin) |
| 4 | 2026-11-09 | Spec Lead | Contexto para agentes | Claude (Opus 5.5) | Archivos de instrucciones para que cualquier agente cargue specs y metodología | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` | Aprobado; se aclaró ODD = Outcome-Driven para evitar ambigüedad |
| 5 | 2026-11-12 | QA/DevOps Lead | T1 · Setup, Docker Compose y CI | Codex (GPT-5) | Implementar el issue #1 con TDD después de revisar y aprobar el plan | Backend `/health`, frontend React/Vite, Compose con 3 servicios, CI y `test_health` en verde | Plan aprobado; pendiente revisión humana del diff y PR |
