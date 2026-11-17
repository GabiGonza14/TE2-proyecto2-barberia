import type {
  Agenda,
  ApiErrorBody,
  ApiErrorDetails,
  Availability,
  Barber,
  Booking,
  BookingRequest,
  CancelledBooking,
  Service,
} from "./types";

const DEFAULT_API_URL = "http://localhost:8000/api/v1";

/** URL de la API configurable con `VITE_API_URL` (Clarify #26). */
export const API_URL = (
  (import.meta.env.VITE_API_URL as string | undefined) ?? DEFAULT_API_URL
).replace(/\/+$/, "");

/** Error del backend con el formato común `{ error: { code, message, details } }`. */
export class ApiError extends Error {
  readonly code: string;
  readonly details: ApiErrorDetails;
  readonly status: number;

  constructor(
    code: string,
    message: string,
    details: ApiErrorDetails = {},
    status = 0,
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  const body = (await response.json().catch(() => null)) as unknown;

  if (!response.ok) {
    const error = (body as ApiErrorBody | null)?.error;
    throw new ApiError(
      error?.code ?? "UNKNOWN",
      error?.message ?? "No se pudo completar la solicitud",
      error?.details ?? {},
      response.status,
    );
  }

  return body as T;
}

export function getServices(): Promise<Service[]> {
  return request<Service[]>("/services");
}

export function getBarbers(): Promise<Barber[]> {
  return request<Barber[]>("/barbers");
}

export function getAvailability(
  barberId: number,
  serviceId: number,
  date: string,
): Promise<Availability> {
  const query = new URLSearchParams({
    barber_id: String(barberId),
    service_id: String(serviceId),
    date,
  });
  return request<Availability>(`/availability?${query.toString()}`);
}

export function createBooking(payload: BookingRequest): Promise<Booking> {
  return request<Booking>("/bookings", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** RF-10 / BR-10: código + teléfono; el backend normaliza el código. */
export function getBooking(code: string, phone: string): Promise<Booking> {
  const query = new URLSearchParams({ phone });
  return request<Booking>(
    `/bookings/${encodeURIComponent(code)}?${query.toString()}`,
  );
}

/** RF-11 / BR-06: cancelar con código + teléfono. */
export function cancelBooking(
  code: string,
  phone: string,
): Promise<CancelledBooking> {
  return request<CancelledBooking>(
    `/bookings/${encodeURIComponent(code)}/cancel`,
    { method: "POST", body: JSON.stringify({ phone }) },
  );
}

/** RF-13 / RF-14: la clave de admin viaja solo en la cabecera. */
export function getAgenda(
  date: string,
  adminKey: string,
  barberId?: number | null,
): Promise<Agenda> {
  const query = new URLSearchParams({ date });
  if (barberId != null) query.set("barber_id", String(barberId));
  return request<Agenda>(`/admin/agenda?${query.toString()}`, {
    headers: { "X-Admin-Key": adminKey },
  });
}
