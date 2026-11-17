import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "../../src/frontend/src/App";

/**
 * T11 · Consultar y cancelar la reserva (issue #27).
 * API simulada con `fetch`; nunca se llama al backend real.
 */

const booking = {
  code: "K7P2QX",
  status: "CONFIRMADA",
  barber: "Carlos",
  service: "Corte",
  start_at: "2026-12-01T10:00:00-05:00",
  end_at: "2026-12-01T10:30:00-05:00",
};

const notFound = {
  error: {
    code: "NOT_FOUND",
    message: "No encontramos una reserva con esos datos",
    details: {},
  },
};

const windowClosed = {
  error: {
    code: "CANCEL_WINDOW_CLOSED",
    message: "Ya no se puede cancelar: faltan menos de 2 horas para tu cita",
    details: {},
  },
};

function reply(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

type Options = {
  found?: boolean;
  cancelError?: unknown;
};

function mockApi(options: Options = {}) {
  const calls = { lookup: 0, cancel: 0, phones: [] as string[] };
  const fetchMock = vi.fn(
    async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/bookings/") && url.endsWith("/cancel")) {
        calls.cancel += 1;
        const body = JSON.parse(String(init?.body ?? "{}"));
        calls.phones.push(String(body.phone));
        if (options.cancelError) return reply(options.cancelError, 409);
        return reply({ code: "K7P2QX", status: "CANCELADA" });
      }
      if (url.includes("/bookings/")) {
        calls.lookup += 1;
        const phone = new URL(url).searchParams.get("phone") ?? "";
        calls.phones.push(phone);
        if (options.found === false) return reply(notFound, 404);
        return reply(booking);
      }
      throw new Error(`URL no simulada: ${url}`);
    },
  );
  vi.stubGlobal("fetch", fetchMock);
  return calls;
}

async function openLookup() {
  fireEvent.click(screen.getByRole("link", { name: "Mi reserva" }));
  return screen.findByRole("heading", { name: "Tu reserva" });
}

function fillLookup(code = "k7p2qx", phone = "6123-4567") {
  fireEvent.change(screen.getByLabelText("Código de reserva"), {
    target: { value: code },
  });
  fireEvent.change(screen.getByLabelText("Teléfono"), {
    target: { value: phone },
  });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  sessionStorage.clear();
});

describe("Mi reserva", () => {
  it("con código y teléfono correctos muestra el detalle de la reserva", async () => {
    const calls = mockApi();
    render(<App />);
    await openLookup();

    fillLookup();
    fireEvent.click(screen.getByRole("button", { name: "Buscar reserva" }));

    expect(await screen.findByText("K7P2QX")).toBeTruthy();
    expect(screen.getByText("Carlos")).toBeTruthy();
    expect(screen.getByText("Corte")).toBeTruthy();
    expect(screen.getByText("CONFIRMADA")).toBeTruthy();
    expect(screen.getByText("10:00 – 10:30")).toBeTruthy();
    expect(calls.lookup).toBe(1);
    expect(calls.phones[0]).toBe("6123-4567");
  });

  it("con datos incorrectos muestra el mensaje del 404", async () => {
    mockApi({ found: false });
    render(<App />);
    await openLookup();

    fillLookup("K7P2QX", "6000-0000");
    fireEvent.click(screen.getByRole("button", { name: "Buscar reserva" }));

    expect(
      await screen.findByText("No encontramos una reserva con esos datos")
    ).toBeTruthy();
    expect(screen.queryByText("K7P2QX")).toBeNull();
  });

  it("cancelar pide confirmación y deja la reserva en CANCELADA sin botón", async () => {
    const calls = mockApi();
    render(<App />);
    await openLookup();
    fillLookup();
    fireEvent.click(screen.getByRole("button", { name: "Buscar reserva" }));
    await screen.findByText("K7P2QX");

    fireEvent.click(screen.getByRole("button", { name: "Cancelar mi cita" }));
    expect(
      screen.getByText("¿Seguro? Liberarás el horario para otro cliente")
    ).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Sí, cancelar" }));

    await waitFor(() =>
      expect(screen.getByText("CANCELADA")).toBeTruthy()
    );
    expect(calls.cancel).toBe(1);
    expect(calls.phones.at(-1)).toBe("6123-4567");
    expect(
      screen.queryByRole("button", { name: "Cancelar mi cita" })
    ).toBeNull();
  });

  it("si faltan menos de 2 horas muestra el mensaje del 409", async () => {
    mockApi({ cancelError: windowClosed });
    render(<App />);
    await openLookup();
    fillLookup();
    fireEvent.click(screen.getByRole("button", { name: "Buscar reserva" }));
    await screen.findByText("K7P2QX");

    fireEvent.click(screen.getByRole("button", { name: "Cancelar mi cita" }));
    fireEvent.click(screen.getByRole("button", { name: "Sí, cancelar" }));

    expect(
      await screen.findByText(
        "Ya no se puede cancelar: faltan menos de 2 horas para tu cita"
      )
    ).toBeTruthy();
    expect(screen.getByText("CONFIRMADA")).toBeTruthy();
  });
});
