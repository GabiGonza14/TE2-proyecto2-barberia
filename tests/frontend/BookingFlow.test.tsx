import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "../../src/frontend/src/App";

/**
 * T10 · UI de reserva en 4 pasos (issue #26).
 * API simulada con `fetch`; nunca se llama al backend real.
 */

const services = [
  { id: 1, name: "Corte", duration_min: 30, price: 8 },
  { id: 2, name: "Barba", duration_min: 20, price: 5 },
];

const barbers = [
  { id: 1, name: "Carlos" },
  { id: 2, name: "Luis" },
];

const availableDay = {
  date: "2026-12-01",
  barber_id: 1,
  service_id: 1,
  slots: ["10:00", "10:30"],
  reason: null,
};

const createdBooking = {
  code: "K7P2QX",
  status: "CONFIRMADA",
  barber: "Carlos",
  service: "Corte",
  start_at: "2026-12-01T10:00:00-05:00",
  end_at: "2026-12-01T10:30:00-05:00",
};

const slotTaken = {
  error: {
    code: "SLOT_TAKEN",
    message: "El barbero ya tiene una cita en ese horario",
    details: {},
  },
};

type MockOptions = {
  availability?: typeof availableDay;
  bookingError?: unknown;
};

function reply(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function mockApi(options: MockOptions = {}) {
  const calls = { availability: 0, bookings: 0 };
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/services")) return reply(services);
    if (url.endsWith("/barbers")) return reply(barbers);
    if (url.includes("/availability")) {
      calls.availability += 1;
      return reply(options.availability ?? availableDay);
    }
    if (url.endsWith("/bookings")) {
      calls.bookings += 1;
      if (options.bookingError) return reply(options.bookingError, 409);
      return reply(createdBooking, 201);
    }
    throw new Error(`URL no simulada: ${url}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return calls;
}

async function goToStep4() {
  fireEvent.click(
    await screen.findByRole("button", { name: "Elegir Corte" })
  );
  fireEvent.click(
    await screen.findByRole("button", { name: "Elegir Carlos" })
  );
  fireEvent.click(
    await screen.findByRole("button", { name: "Reservar a las 10:00" })
  );
  fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
}

async function fillClientData(name = "Ana Pérez", phone = "6123-4567") {
  fireEvent.change(screen.getByLabelText("Nombre"), {
    target: { value: name },
  });
  fireEvent.change(screen.getByLabelText("Teléfono"), {
    target: { value: phone },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Flujo de reserva en 4 pasos", () => {
  it("llega a la confirmación en 4 pasos y muestra el código", async () => {
    mockApi();
    render(<App />);

    expect(screen.getByText("Paso 1 de 4")).toBeTruthy();
    fireEvent.click(
      await screen.findByRole("button", { name: "Elegir Corte" })
    );

    expect(screen.getByText("Paso 2 de 4")).toBeTruthy();
    fireEvent.click(
      await screen.findByRole("button", { name: "Elegir Carlos" })
    );

    expect(screen.getByText("Paso 3 de 4")).toBeTruthy();
    fireEvent.click(
      await screen.findByRole("button", { name: "Reservar a las 10:00" })
    );
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));

    expect(screen.getByText("Paso 4 de 4")).toBeTruthy();
    await fillClientData();
    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar reserva" })
    );

    expect(await screen.findByText("K7P2QX")).toBeTruthy();
    expect(screen.getByText(/Guarda tu código/i)).toBeTruthy();
    expect(screen.getByText("Carlos")).toBeTruthy();
    expect(screen.getByText("Corte")).toBeTruthy();
  });

  it("ante un 409 SLOT_TAKEN avisa, vuelve al paso 3 y recarga la disponibilidad", async () => {
    const calls = mockApi({ bookingError: slotTaken });
    render(<App />);
    await goToStep4();
    await fillClientData();

    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar reserva" })
    );

    expect(
      await screen.findByText("Ese horario ya no está disponible")
    ).toBeTruthy();
    expect(screen.getByText("Paso 3 de 4")).toBeTruthy();
    await waitFor(() => expect(calls.availability).toBe(2));
  });

  it("un teléfono inválido no permite enviar y muestra el error junto al campo", async () => {
    const calls = mockApi();
    render(<App />);
    await goToStep4();
    await fillClientData("Ana Pérez", "1234");

    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar reserva" })
    );

    expect(await screen.findByText(/Teléfono inválido/i)).toBeTruthy();
    expect(screen.getByText("Paso 4 de 4")).toBeTruthy();
    expect(calls.bookings).toBe(0);
  });

  it("un día cerrado muestra el motivo CLOSED y no una lista vacía", async () => {
    mockApi({
      availability: { ...availableDay, slots: [], reason: "CLOSED" },
    });
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Elegir Corte" })
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Elegir Carlos" })
    );

    expect(await screen.findByText(/cerrad/i)).toBeTruthy();
    expect(
      screen.queryByRole("button", { name: /Reservar a las/ })
    ).toBeNull();
  });
});
