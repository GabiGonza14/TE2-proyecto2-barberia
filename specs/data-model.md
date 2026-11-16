# Data Model — Barbería

```
barbers 1 ──── * bookings * ──── 1 services
```

## barbers
| Campo | Tipo | Reglas |
|-------|------|--------|
| id | SERIAL PK | |
| name | VARCHAR(60) | NOT NULL |
| active | BOOLEAN | DEFAULT true (BR-08) |

## services
| Campo | Tipo | Reglas |
|-------|------|--------|
| id | SERIAL PK | |
| name | VARCHAR(60) | UNIQUE |
| duration_min | SMALLINT | CHECK > 0 (BR-03) |
| price | NUMERIC(6,2) | CHECK ≥ 0 |

## bookings
| Campo | Tipo | Reglas |
|-------|------|--------|
| id | SERIAL PK | |
| code | CHAR(6) | UNIQUE (BR-10) |
| barber_id | FK → barbers | NOT NULL |
| service_id | FK → services | NOT NULL |
| client_name | VARCHAR(60) | NOT NULL (BR-09) |
| client_phone | VARCHAR(8) | solo dígitos, normalizado (BR-09) |
| start_at | TIMESTAMPTZ | NOT NULL |
| end_at | TIMESTAMPTZ | NOT NULL, CHECK end_at > start_at |
| blocked_until 🆕 CR-01 | TIMESTAMPTZ | NOT NULL, CHECK `blocked_until = end_at + interval '10 minutes'` (BR-12). Fin real de la cita **más** la limpieza; lo calcula la app al crear la reserva. No se expone en la API. |
| status | VARCHAR(12) | `CONFIRMADA` \| `CANCELADA` |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| cancelled_at | TIMESTAMPTZ | NULL |

### Restricción clave (BR-01 · BR-12 · RNF-01)
```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE bookings ADD CONSTRAINT no_double_booking
  EXCLUDE USING gist (barber_id WITH =, tstzrange(start_at, blocked_until, '[)') WITH &&)
  WHERE (status = 'CONFIRMADA');
```
**CR-01:** antes el rango era `tstzrange(start_at, end_at, '[)')`. No se puede escribir `end_at + interval '10 minutes'` dentro de la restricción porque PostgreSQL exige funciones `IMMUTABLE` en expresiones de índice y `timestamptz + interval` es `STABLE` (*"functions in index expression must be marked IMMUTABLE"*). Por eso se guarda `blocked_until` y un `CHECK` garantiza que siempre sea `end_at + 10 min` (D9).

Al comparar `[inicio, fin + 10)` de ambas reservas, la limpieza se respeta **en los dos sentidos**: la nueva no puede empezar dentro de la limpieza de la existente, ni terminar (más su limpieza) después del inicio de la existente.

**Migración CR-01 (Alembic):** agregar `blocked_until` → rellenar con `end_at + interval '10 minutes'` → `NOT NULL` + `CHECK` → recrear `no_double_booking` sobre `blocked_until`. Si alguna reserva `CONFIRMADA` existente viola BR-12, la migración **falla** (no se cancela nada automáticamente). El `downgrade` vuelve al rango con `end_at`.

### Índices
- `bookings(barber_id, start_at)` — disponibilidad y agenda.
- `bookings(code)` — búsqueda por código.

## Datos semilla
| Barberos | Servicios |
|----------|-----------|
| Carlos, Luis, Andrés | Corte 30′ $8 · Barba 20′ $5 · Corte+Barba 45′ $12 · Diseño/Fade 40′ $10 |
