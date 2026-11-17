/** Fechas y horas del negocio: siempre America/Panama (BR-11). */

const PANAMA_TZ = "America/Panama";

function partsToISODate(parts: Intl.DateTimeFormatPart[]): string {
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

/** Hoy en America/Panama como `YYYY-MM-DD`. */
export function panamaToday(): string {
  return partsToISODate(
    new Intl.DateTimeFormat("en-US", {
      timeZone: PANAMA_TZ,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).formatToParts(new Date()),
  );
}

/** Suma días a una fecha `YYYY-MM-DD` (sin depender de la zona del navegador). */
export function addDays(date: string, days: number): string {
  const [year, month, day] = date.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day + days))
    .toISOString()
    .slice(0, 10);
}

/** Las 15 fechas reservables: hoy … hoy + 14 días (BR-05). */
export function bookableDates(today = panamaToday()): string[] {
  return Array.from({ length: 15 }, (_, index) => addDays(today, index));
}

/** `2026-12-01` → `martes, 1 de diciembre`. */
export function formatDateLong(date: string): string {
  const [year, month, day] = date.split("-").map(Number);
  return new Intl.DateTimeFormat("es-PA", {
    timeZone: "UTC",
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date(Date.UTC(year, month - 1, day)));
}

/** Hora de pared del ISO del backend (`…T10:00:00-05:00` → `10:00`). */
export function formatTime(iso: string): string {
  return iso.slice(11, 16);
}
