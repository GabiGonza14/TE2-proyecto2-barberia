import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "../../src/frontend/src/App";

describe("App", () => {
  it("muestra el nombre del sistema", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "BarberBook" })).toBeTruthy();
  });
});
