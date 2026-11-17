import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "../../src/frontend/src/App";
import agendaSource from "../../src/frontend/src/pages/AgendaPage.tsx?raw";
import clientSource from "../../src/frontend/src/api/client.ts?raw";

/**
 * T11 · Agenda del admin (issue #27).
 * La clave se escribe en pantalla: nunca se lee de `import.meta.env`.
 */

const agenda = {
  date: "2026-12-01",
  barbers: [
    {
      barber: "Carlos",
      bookings: [
        {
          start: "10:00",
          end: "10:30",
          service: "Corte",
          client: "Ana Pérez",
          code: "K7P2QX",
        },
      ],
    },
    { barber: "Luis", bookings: [] },
  ],
};

function reply(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function mockApi(options: { unauthorized?: boolean } = {}) {
  const calls = { agenda: 0, headers: [] as Record<string, string>[] };
  const fetchMock = vi.fn(
    async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/barbers")) {
        return reply([
          { id: 1, name: "Carlos" },
          { id: 2, name: "Luis" },
        ]);
      }
      if (url.includes("/admin/agenda")) {
        calls.agenda += 1;
        calls.headers.push((init?.headers ?? {}) as Record<string, string>);
        if (options.unauthorized) {
          return reply(
            {
              error: {
                code: "UNAUTHORIZED",
                message: "Clave de administrador inválida",
                details: {},
              },
            },
            401,
          );
        }
        return reply(agenda);
      }
      throw new Error(`URL no simulada: ${url}`);
    },
  );
  vi.stubGlobal("fetch", fetchMock);
  return calls;
}

async function openAgenda() {
  fireEvent.click(screen.getByRole("link", { name: "Agenda" }));
  return screen.findByRole("heading", { name: "Agenda del día" });
}

function enterKey(key = "clave-demo") {
  fireEvent.change(screen.getByLabelText("Clave de administrador"), {
    target: { value: key },
  });
  fireEvent.click(screen.getByRole("button", { name: "Entrar" }));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  sessionStorage.clear();
});

describe("Agenda del admin", () => {
  it("envía la clave en X-Admin-Key y muestra los barberos sin citas", async () => {
    const calls = mockApi();
    render(<App />);
    await openAgenda();

    enterKey();

    expect(await screen.findByText("Ana Pérez")).toBeTruthy();
    expect(screen.getByText("Carlos")).toBeTruthy();
    expect(screen.getByText("Luis")).toBeTruthy();
    expect(screen.getByText("Sin citas")).toBeTruthy();
    expect(screen.getByText("10:00")).toBeTruthy();
    expect(calls.agenda).toBe(1);
    expect(calls.headers[0]?.["X-Admin-Key"]).toBe("clave-demo");
  });

  it("con 401 avisa y vuelve a pedir la clave", async () => {
    mockApi({ unauthorized: true });
    render(<App />);
    await openAgenda();

    enterKey("clave-mala");

    expect(
      await screen.findByText("Clave de administrador inválida")
    ).toBeTruthy();
    expect(screen.getByLabelText("Clave de administrador")).toBeTruthy();
    expect(screen.queryByText("Ana Pérez")).toBeNull();
  });

  it("la clave no sale de import.meta.env y 'Salir' la borra", async () => {
    expect(agendaSource).not.toMatch(/VITE_ADMIN_KEY/);
    expect(agendaSource).not.toMatch(/import\.meta\.env/);
    expect(clientSource).not.toMatch(/VITE_ADMIN_KEY/);

    mockApi();
    render(<App />);
    await openAgenda();
    enterKey("clave-demo");
    await screen.findByText("Ana Pérez");

    expect(sessionStorage.getItem("barberbook.adminKey")).toBe("clave-demo");

    fireEvent.click(screen.getByRole("button", { name: "Salir" }));

    await waitFor(() =>
      expect(screen.getByLabelText("Clave de administrador")).toBeTruthy()
    );
    expect(sessionStorage.getItem("barberbook.adminKey")).toBeNull();
    expect(screen.queryByRole("button", { name: "Salir" })).toBeNull();
  });
});
