/**
 * La clave de admin la escribe el usuario y vive solo en esta pestaña.
 * NUNCA se lee de `import.meta.env`: todo lo que entra al bundle es público.
 */
const STORAGE_KEY = "barberbook.adminKey";

export function readAdminKey(): string {
  try {
    return sessionStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

export function saveAdminKey(key: string): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, key);
  } catch {
    // sessionStorage bloqueado: la clave sigue solo en memoria.
  }
}

export function clearAdminKey(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nada que limpiar.
  }
}
