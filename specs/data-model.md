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
| status | VARCHAR(12) | `CONFIRMADA` \| `CANCELADA` |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| cancelled_at | TIMESTAMPTZ | NULL |

### Restricción clave (BR-01 · RNF-01)
```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE bookings ADD CONSTRAINT no_double_booking
  EXCLUDE USING gist (barber_id WITH =, tstzrange(start_at, end_at, '[)') WITH &&)
  WHERE (status = 'CONFIRMADA');
```

### Índices
- `bookings(barber_id, start_at)` — disponibilidad y agenda.
- `bookings(code)` — búsqueda por código.

## Datos semilla
| Barberos | Servicios |
|----------|-----------|
| Carlos, Luis, Andrés | Corte 30′ $8 · Barba 20′ $5 · Corte+Barba 45′ $12 · Diseño/Fade 40′ $10 |
