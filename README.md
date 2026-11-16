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
FastAPI · SQLAlchemy · PostgreSQL 16 · React + Vite + TS · pytest · vitest · Docker Compose · GitHub Actions · SonarCloud

## Ejecutar
`ADMIN_KEY` es **obligatoria**: si no está definida, `docker compose` falla a propósito en lugar de arrancar con una clave pública. Créala en un `.env` (no versionado) a partir de `.env.example`:

```bash
cp .env.example .env             # y edita ADMIN_KEY con una clave larga y aleatoria
docker compose up --build        # api :8000 · web :5173
docker compose exec api pytest -v
```

- **Hot reload:** el código de `src/backend` y `src/frontend` se monta en los contenedores; los cambios se ven sin `--build` (solo hace falta reconstruir si cambian dependencias: `pyproject.toml` o `package.json`).
- **CORS:** la API solo acepta el origen del frontend (`http://localhost:5173`). Para otro origen, define `CORS_ORIGINS` en `.env` (separados por comas; `*` no se permite).
- **Frontend:** `cd src/frontend && npm test` (vitest; los tests están en `tests/frontend/`) · `npm run coverage` para ver la cobertura.
- **Cobertura backend:** `pytest --cov --cov-report=term`.

## Equipo y roles (rotan por ciclo)
| Ciclo | Spec Lead | Dev Lead | QA/DevOps Lead |
|-------|-----------|----------|----------------|
| 1 · Base (T1–T4) | Gabriel González | Isalleth | Derlin |
| 2 · Reservar (T5–T7) | Isalleth | Derlin | Gabriel González |
| 3 · Gestionar (T8–T9) | Derlin | Gabriel González | Isalleth |
| 4 · UI y entrega (T10–T12) | Gabriel González | Isalleth | Derlin |

## Flujo Git
`main` protegida · ramas `feat/T<n>-nombre` · PR con revisión · commits `tipo(alcance): mensaje #issue`
