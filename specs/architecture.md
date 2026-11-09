# Architecture — Barbería

## 1. Constitution (principios no negociables)

1. **Backend:** Python 3.12 + **FastAPI** + SQLAlchemy 2 + Alembic.
2. **Base de datos:** **PostgreSQL 16** es la única persistencia.
3. **Frontend:** **React 18 + Vite + TypeScript**.
4. **Tests:** `pytest` (backend) · `vitest` (frontend). Toda regla BR-xx tiene test.
5. La regla **no doble reserva** se garantiza en la BD con una *exclusion constraint* (no solo en código).
6. Ningún agente IA cambia un contrato de `api.md` sin actualizar primero la spec.
7. Si hay contradicción entre spec y código: **detenerse y preguntar**.
8. Cambios de esquema solo vía migración Alembic versionada.
9. No se guardan teléfonos completos en logs.
10. Commits con formato `tipo(alcance): mensaje #issue` (ej. `feat(bookings): crear reserva #5`).

## 2. Stack (libertad tecnológica)

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| API | FastAPI | Validación con Pydantic, OpenAPI automático, experiencia previa del equipo. |
| ORM / migraciones | SQLAlchemy 2 + Alembic | Transacciones explícitas, migraciones versionadas. |
| BD | PostgreSQL 16 | `EXCLUDE USING gist` con `tstzrange` → imposible guardar 2 citas solapadas. |
| UI | React + Vite + TS | Rápido de montar, tipado. |
| Tests | pytest, httpx, vitest | Unit + integración + concurrencia. |
| Infra | Docker Compose | `db` + `api` + `web` con un comando. |
| CI | GitHub Actions | Corre tests en cada PR. |

## 3. Componentes

```
┌──────────┐   HTTP/JSON   ┌────────────────────────────────────────┐    SQL    ┌──────────────┐
│  React   │ ────────────► │ FastAPI                                │ ────────► │ PostgreSQL   │
│  (web)   │               │  routers/  → services/ → repositories/ │           │ + EXCLUDE    │
└──────────┘               │  (HTTP)      (reglas BR)   (SQL)       │           │   constraint │
                           └────────────────────────────────────────┘           └──────────────┘
```

| Módulo | Responsabilidad |
|--------|-----------------|
| `routers/` | Endpoints HTTP, traducción de errores de dominio a HTTP. |
| `services/availability.py` | Cálculo de slots libres (BR-02, BR-03, BR-04, BR-05). |
| `services/booking.py` | Crear / cancelar / consultar reservas (BR-01, BR-06, BR-07, BR-10). |
| `domain/rules.py` | Funciones puras: `overlaps()`, `is_within_hours()`, `on_grid()`… (fáciles de testear). |
| `repositories/` | Acceso a datos. |
| `core/errors.py` | Excepciones de dominio → códigos de `business-rules.md`. |

## 4. Concurrencia (O1 / RF-07)

Dos capas de defensa:
1. **Aplicación:** dentro de una transacción, se verifica solapamiento antes de insertar → error amigable `SLOT_TAKEN`.
2. **Base de datos (garantía final):**
   ```sql
   EXCLUDE USING gist (barber_id WITH =, tstzrange(start_at, end_at, '[)') WITH &&)
   WHERE (status = 'CONFIRMADA')
   ```
   Si dos peticiones pasan el paso 1 a la vez, la segunda falla al hacer `INSERT` → se captura `ExclusionViolation` y se responde **409 `SLOT_TAKEN`**.

## 5. Seguridad
- Admin: header `X-Admin-Key` comparado contra variable de entorno.
- Cliente: código + teléfono para consultar/cancelar.
- CORS limitado al origen del frontend.

## 6. Estructura del repo
```
src/backend/app/{main.py, routers/, services/, domain/, repositories/, models/, core/}
src/backend/alembic/
src/frontend/src/{pages/, components/, api/}
tests/backend/{unit/, integration/}
tests/frontend/
docker-compose.yml
```
