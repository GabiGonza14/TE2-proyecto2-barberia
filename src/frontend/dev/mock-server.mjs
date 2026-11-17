/**
 * Servidor SOLO para demo manual de la UI (issue #26, T10).
 *
 * NO se usa en el build ni en los tests: vive en `dev/` y simula el contrato de
 * `specs/api.md` con datos en memoria para poder recorrer el flujo de reserva
 * cuando no hay backend levantado. Para la demo real usa `docker compose up`.
 *
 * Uso:
 *   node dev/mock-server.mjs          (sirve dist/ + API en http://localhost:8000)
 */
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PORT = Number(process.env.MOCK_PORT ?? 8000);
const ROOT = resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
const DIST = join(ROOT, "dist");

const PANAMA_TZ = "America/Panama";
const API = "/api/v1";

const services = [
  { id: 1, name: "Corte", duration_min: 30, price: 8.0 },
  { id: 2, name: "Barba", duration_min: 20, price: 5.0 },
  { id: 3, name: "Corte+Barba", duration_min: 45, price: 12.0 },
  { id: 4, name: "Diseño/Fade", duration_min: 40, price: 10.0 },
];

const barbers = [
  { id: 1, name: "Carlos" },
  { id: 2, name: "Luis" },
  { id: 3, name: "Andrés" },
];

/** Reservas confirmadas en memoria: clave barber_id|start_at. */
const taken = new Map();

function panamaToday() {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: PANAMA_TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const value = Object.fromEntries(parts.map((p) => [p.type, p.value]));
  return `${value.year}-${value.month}-${value.day}`;
}

function addDays(date, days) {
  const [y, m, d] = date.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d + days)).toISOString().slice(0, 10);
}

function weekday(date) {
  const [y, m, d] = date.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).getUTCDay();
}

function timeToMinutes(time) {
  const [h, m] = time.split(":").map(Number);
  return h * 60 + m;
}

function minutesToTime(total) {
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(
    total % 60,
  ).padStart(2, "0")}`;
}

function slotsFor(barberId, serviceId, date) {
  const duration = services.find((s) => s.id === serviceId)?.duration_min ?? 30;
  const slots = [];
  for (let minute = 9 * 60; minute + duration <= 19 * 60; minute += 30) {
    if (minute >= 13 * 60 && minute < 14 * 60) continue; // almuerzo
    const start = minutesToTime(minute);
    const key = `${barberId}|${date}T${start}`;
    // Una cita fija para que la agenda se vea real; el resto libre.
    if (barberId === 1 && start === "10:30" && date === addDays(panamaToday(), 1)) {
      continue;
    }
    if (!taken.has(key)) slots.push(start);
  }
  return slots;
}

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(payload),
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  });
  res.end(payload);
}

function apiError(res, status, code, message, details = {}) {
  json(res, status, { error: { code, message, details } });
}

async function readBody(req) {
  let raw = "";
  for await (const chunk of req) raw += chunk;
  return raw ? JSON.parse(raw) : {};
}

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".png": "image/png",
  ".ico": "image/x-icon",
};

async function serveStatic(res, pathname) {
  const safe = normalize(pathname).replace(/^(\.\.[/\\])+/, "");
  let file = join(DIST, safe);
  try {
    const info = await stat(file);
    if (info.isDirectory()) file = join(file, "index.html");
  } catch {
    file = join(DIST, "index.html"); // SPA fallback
  }
  try {
    const data = await readFile(file);
    res.writeHead(200, {
      "Content-Type": MIME[extname(file)] ?? "application/octet-stream",
    });
    res.end(data);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Ejecuta `npm run build` antes de la demo (falta dist/).");
  }
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", `http://localhost:${PORT}`);
  const { pathname, searchParams } = url;

  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    });
    res.end();
    return;
  }

  if (pathname === `${API}/services` && req.method === "GET") {
    return json(res, 200, services);
  }

  if (pathname === `${API}/barbers` && req.method === "GET") {
    return json(res, 200, barbers);
  }

  if (pathname === `${API}/availability` && req.method === "GET") {
    const barberId = Number(searchParams.get("barber_id"));
    const serviceId = Number(searchParams.get("service_id"));
    const date = searchParams.get("date") ?? "";
    const today = panamaToday();
    const base = { date, barber_id: barberId, service_id: serviceId };

    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return apiError(res, 422, "VALIDATION_ERROR", "Fecha inválida", {
        field: "date",
      });
    }
    if (date < today) return json(res, 200, { ...base, slots: [], reason: "PAST_DATE" });
    if (date > addDays(today, 14)) {
      return json(res, 200, { ...base, slots: [], reason: "TOO_FAR_AHEAD" });
    }
    if (weekday(date) === 0 || weekday(date) === 1) {
      return json(res, 200, { ...base, slots: [], reason: "CLOSED" });
    }
    return json(res, 200, {
      ...base,
      slots: slotsFor(barberId, serviceId, date),
      reason: null,
    });
  }

  if (pathname === `${API}/bookings` && req.method === "POST") {
    let body;
    try {
      body = await readBody(req);
    } catch {
      return apiError(res, 400, "BAD_REQUEST", "JSON inválido");
    }

    const name = String(body.client_name ?? "").trim();
    const phone = String(body.client_phone ?? "").replace(/\s/g, "");
    const barber = barbers.find((b) => b.id === body.barber_id);
    const service = services.find((s) => s.id === body.service_id);
    const start = String(body.start_at ?? "");

    if (name.length < 2 || name.length > 60) {
      return apiError(
        res,
        422,
        "VALIDATION_ERROR",
        "El nombre debe tener entre 2 y 60 caracteres",
        { field: "client_name" },
      );
    }
    if (!/^6\d{3}-?\d{4}$/.test(phone)) {
      return apiError(
        res,
        422,
        "VALIDATION_ERROR",
        "El teléfono debe tener el formato 6XXX-XXXX",
        { field: "client_phone" },
      );
    }
    if (!barber || !service || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:00-05:00$/.test(start)) {
      return apiError(res, 422, "VALIDATION_ERROR", "Datos de la reserva inválidos");
    }

    const date = start.slice(0, 10);
    const time = start.slice(11, 16);
    const key = `${barber.id}|${date}T${time}`;
    if (taken.has(key)) {
      return apiError(
        res,
        409,
        "SLOT_TAKEN",
        "El barbero ya tiene una cita en ese horario",
      );
    }

    const endMinute = timeToMinutes(time) + service.duration_min;
    const code = Array.from({ length: 6 }, () =>
      "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"[Math.floor(Math.random() * 32)],
    ).join("");
    taken.set(key, code);

    return json(res, 201, {
      code,
      status: "CONFIRMADA",
      barber: barber.name,
      service: service.name,
      start_at: start,
      end_at: `${date}T${minutesToTime(endMinute)}:00-05:00`,
    });
  }

  if (pathname === "/__frame") {
    // Solo para capturas: iframe con viewport propio (móvil / escritorio ancho).
    const width = Number(searchParams.get("w") ?? 390);
    const height = Number(searchParams.get("h") ?? 844);
    const scale = Number(searchParams.get("scale") ?? 1);
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(`<!doctype html>
<html lang="es"><head><meta charset="utf-8" /><style>
  html, body { margin: 0; padding: 0; background: #f4f1ec; }
  #frame { width: ${width * scale}px; height: ${height * scale}px; overflow: hidden;
    margin: 20px auto; outline: 1px solid #ddd7ce; }
  iframe { display: block; width: ${width}px; height: ${height}px; border: 0;
    transform: scale(${scale}); transform-origin: top left; }
</style></head>
<body><div id="frame"><iframe id="app" src="/" title="BarberBook"></iframe></div></body></html>`);
    return;
  }

  if (pathname.startsWith(API)) {
    return apiError(res, 404, "NOT_FOUND", "Recurso no encontrado");
  }

  if (req.method === "GET") return serveStatic(res, pathname);

  res.writeHead(405, { "Content-Type": "text/plain; charset=utf-8" });
  res.end("Método no permitido");
});

server.listen(PORT, () => {
  console.log(`Mock API + dist en http://localhost:${PORT}`);
  console.log("Datos en memoria: reinicia el proceso para limpiar reservas.");
});
