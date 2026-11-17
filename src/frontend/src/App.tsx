import { useEffect, useState } from "react";

import AgendaPage from "./pages/AgendaPage";
import BookingPage from "./pages/BookingPage";
import LookupPage from "./pages/LookupPage";

/** Navegación sin router: tres rutas por hash (issue #27). */
const ROUTES = ["reservar", "mi-reserva", "agenda"] as const;

type Route = (typeof ROUTES)[number];

const NAV: { route: Route; label: string }[] = [
  { route: "reservar", label: "Reservar" },
  { route: "mi-reserva", label: "Mi reserva" },
  { route: "agenda", label: "Agenda" },
];

function routeFromHash(hash: string): Route {
  const value = hash.replace(/^#\/?/, "").replace(/\/+$/, "");
  return (ROUTES as readonly string[]).includes(value)
    ? (value as Route)
    : "reservar";
}

export default function App() {
  const [route, setRoute] = useState<Route>(() =>
    routeFromHash(window.location.hash),
  );

  useEffect(() => {
    const onHashChange = () => setRoute(routeFromHash(window.location.hash));
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  function navigate(next: Route) {
    window.location.hash = `/${next}`;
    setRoute(next);
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__inner">
          <div className="topbar__brand">
            <span className="brand__pole pole" aria-hidden="true" />
            <h1 className="brand__name">BarberBook</h1>
            <span className="brand__tagline">Cortes con hora. Sin esperas.</span>
          </div>

          <nav className="nav" aria-label="Navegación principal">
            {NAV.map((item) => (
              <a
                key={item.route}
                className="nav__link"
                href={`#/${item.route}`}
                aria-current={route === item.route ? "page" : undefined}
                onClick={(event) => {
                  event.preventDefault();
                  navigate(item.route);
                }}
              >
                {item.label}
              </a>
            ))}
          </nav>
        </div>
      </header>

      <div className="app__route">
        {route === "mi-reserva" ? (
          <LookupPage />
        ) : route === "agenda" ? (
          <AgendaPage />
        ) : (
          <BookingPage />
        )}
      </div>
    </div>
  );
}
