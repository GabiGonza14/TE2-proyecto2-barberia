# 💈 BarberBook — Sistema de Reservas para Barbería

Proyecto 2 · Tópicos Especiales II · Prof. Regis Rivera · UTP

**Problema:** las citas se coordinan por WhatsApp → cruces de horario y espacios perdidos.
**Outcome:** cero cruces y clientes que reservan solos viendo solo horarios reales.

## Recorrido
`ODD → SDD → código → pruebas → valor al usuario`

| Fase | Dónde |
|------|-------|
| Outcomes (ODD) | [`specs/outcomes.md`](specs/outcomes.md) |
| Especificación (SDD) | [`specs/`](specs/) — requirements, business-rules, acceptance-criteria, architecture, data-model, api, implementation-plan |
| Guía para el equipo | [`GUIA-DEL-EQUIPO.md`](GUIA-DEL-EQUIPO.md) |
| Uso de IA | [`docs/ai-log.md`](docs/ai-log.md) |
| Decisiones y cambios | [`docs/decisions.md`](docs/decisions.md) |
| Pruebas y evidencia | [`docs/testing.md`](docs/testing.md) |

## Stack
FastAPI · SQLAlchemy · PostgreSQL 16 · React + Vite + TS · pytest · Docker Compose · GitHub Actions

## Ejecutar
```bash
docker compose up --build        # api :8000 · web :5173
docker compose exec api pytest -v
```

## Equipo y roles (rotan por ciclo)
| Ciclo | Spec Lead | Dev Lead | QA/DevOps Lead |
|-------|-----------|----------|----------------|
| 1 · Base (T1–T4) | Gabriel González | Isalleth | Derlin |
| 2 · Reservar (T5–T7) | Isalleth | Derlin | Gabriel González |
| 3 · Gestionar (T8–T9) | Derlin | Gabriel González | Isalleth |
| 4 · UI y entrega (T10–T12) | Gabriel González | Isalleth | Derlin |

## Flujo Git
`main` protegida · ramas `feat/T<n>-nombre` · PR con revisión · commits `tipo(alcance): mensaje #issue`
