/** Tipos del contrato de `specs/api.md`. */

export type Barber = {
  id: number;
  name: string;
};

export type Service = {
  id: number;
  name: string;
  duration_min: number;
  price: number;
};

export type Availability = {
  date: string;
  barber_id: number;
  service_id: number;
  slots: string[];
  reason: "CLOSED" | "PAST_DATE" | "TOO_FAR_AHEAD" | null;
};

export type BookingRequest = {
  barber_id: number;
  service_id: number;
  start_at: string;
  client_name: string;
  client_phone: string;
};

export type Booking = {
  code: string;
  status: string;
  barber: string;
  service: string;
  start_at: string;
  end_at: string;
};

/** POST /bookings/{code}/cancel → 200 solo devuelve código y estado. */
export type CancelledBooking = {
  code: string;
  status: string;
};

export type AgendaBooking = {
  start: string;
  end: string;
  service: string;
  client: string;
  code: string;
};

export type AgendaBarber = {
  barber: string;
  bookings: AgendaBooking[];
};

export type Agenda = {
  date: string;
  barbers: AgendaBarber[];
};

export type ApiErrorDetails = {
  field?: string;
  [key: string]: unknown;
};

export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    details?: ApiErrorDetails;
  };
};
