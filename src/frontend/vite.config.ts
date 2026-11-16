/// <reference types="vitest/config" />
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

// architecture.md §6: los tests del frontend viven en tests/frontend/, fuera de
// src/frontend. Sus imports de paquetes (react, vitest…) se resuelven como si
// estuvieran aquí, para usar este node_modules.
const frontendEntry = fileURLToPath(new URL("./src/main.tsx", import.meta.url));

function resolveTestsFromFrontend(): Plugin {
  return {
    name: "resolve-tests-from-frontend",
    enforce: "pre",
    async resolveId(source, importer, options) {
      const isBare = !source.startsWith(".") && !source.startsWith("/") && !source.startsWith("\0");
      if (!importer?.includes("/tests/frontend/") || !isBare) return null;
      return this.resolve(source, frontendEntry, { ...options, skipSelf: true });
    },
  };
}

export default defineConfig({
  plugins: [react(), resolveTestsFromFrontend()],
  server: {
    // Permite que vitest cargue tests/frontend/.
    fs: { allow: ["../.."] },
    // Docker en Windows/macOS no propaga eventos de archivos al contenedor:
    // con VITE_USE_POLLING=true Vite revisa los cambios por sondeo (hot reload).
    watch: process.env.VITE_USE_POLLING === "true" ? { usePolling: true, interval: 300 } : undefined,
  },
  test: {
    dir: "../../tests/frontend",
    include: ["**/*.test.{ts,tsx}"],
    environment: "jsdom",
  },
});
