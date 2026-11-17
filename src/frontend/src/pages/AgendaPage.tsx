import { type FormEvent, useEffect, useMemo, useState } from "react";

import { clearAdminKey, readAdminKey, saveAdminKey } from "../api/adminKey";
import { ApiError, getAgenda, getBarbers } from "../api/client";
import { panamaToday } from "../api/dates";
import type { Agenda, Barber } from "../api/types";

function messageFor(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "No pudimos conectar con el servidor. Intenta de nuevo.";
}

export default function AgendaPage() {
  const today = useMemo(() => panamaToday(), []);
  const [key, setKey] = useState(() => readAdminKey());
  const [keyDraft, setKeyDraft] = useState("");
  const [date, setDate] = useState(today);
  const [barberId, setBarberId] = useState("all");
  const [barbers, setBarbers] = useState<Barber[]>([]);
  const [agenda, setAgenda] = useState<Agenda | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getBarbers()
      .then((loaded) => {
        if (!cancelled) setBarbers(loaded);
      })
      .catch(() => {
        // El filtro es opcional: si falla, la agenda sigue funcionando.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!key) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    getAgenda(date, key, barberId === "all" ? null : Number(barberId))
      .then((data) => {
        if (!cancelled) setAgenda(data);
      })
      .catch((caught) => {
        if (cancelled) return;
        setAgenda(null);
        if (caught instanceof ApiError && caught.code === "UNAUTHORIZED") {
          clearAdminKey();
          setKey("");
          setError("Clave de administrador inválida");
        } else {
          setError(messageFor(caught));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [key, date, barberId]);

  function enter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = keyDraft.trim();
    if (!trimmed) {
      setError("Escribe la clave de administrador");
      return;
    }
    setError(null);
    saveAdminKey(trimmed);
    setKey(trimmed);
    setKeyDraft("");
  }

  function signOut() {
    clearAdminKey();
    setKey("");
    setAgenda(null);
    setError(null);
  }

  return (
    <div className="page page--wide">
      <div className="page__inner">
        <header className="page__head">
          <div>
            <h2>Agenda del día</h2>
            <p className="hint">
              Reservas confirmadas por barbero, en hora de Panamá.
            </p>
          </div>
          {key ? (
            <button
              type="button"
              className="button button--ghost button--small-ghost"
              onClick={signOut}
            >
              Salir
            </button>
          ) : null}
        </header>

        {error ? (
          <p className="banner banner--alert" role="alert">
            {error}
          </p>
        ) : null}

        {!key ? (
          <form className="key-form" onSubmit={enter}>
            <label className="field" htmlFor="admin-key">
              <span>Clave de administrador</span>
              <input
                id="admin-key"
                name="admin_key"
                type="password"
                autoComplete="current-password"
                value={keyDraft}
                onChange={(event) => setKeyDraft(event.target.value)}
              />
            </label>
            <button type="submit" className="button button--primary">
              Entrar
            </button>
            <p className="key-form__hint">
              La clave se guarda solo en esta pestaña y se borra con «Salir».
            </p>
          </form>
        ) : (
          <>
            <div className="agenda-toolbar">
              <label className="field field--inline" htmlFor="agenda-date">
                <span>Fecha</span>
                <input
                  id="agenda-date"
                  type="date"
                  value={date}
                  onChange={(event) => setDate(event.target.value)}
                />
              </label>
              <label className="field field--inline" htmlFor="agenda-barber">
                <span>Barbero</span>
                <select
                  id="agenda-barber"
                  value={barberId}
                  onChange={(event) => setBarberId(event.target.value)}
                >
                  <option value="all">Todos los barberos</option>
                  {barbers.map((barber) => (
                    <option key={barber.id} value={barber.id}>
                      {barber.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {loading ? (
              <p className="hint">Cargando agenda…</p>
            ) : agenda ? (
              <div className="agenda-grid">
                {agenda.barbers.map((entry) => (
                  <section className="agenda-col" key={entry.barber}>
                    <h3 className="agenda-col__title">
                      {entry.barber} ·{" "}
                      {entry.bookings.length === 0
                        ? "sin citas"
                        : `${entry.bookings.length} ${
                            entry.bookings.length === 1 ? "cita" : "citas"
                          }`}
                    </h3>
                    {entry.bookings.length === 0 ? (
                      <p className="agenda-col__empty">Sin citas</p>
                    ) : (
                      <ul className="agenda-list">
                        {entry.bookings.map((booking) => (
                          <li key={`${booking.start}-${booking.code}`}>
                            <article className="agenda-card">
                              <p className="agenda-card__time tabular">
                                {booking.start}
                                <span>{booking.end}</span>
                              </p>
                              <p className="agenda-card__client">
                                {booking.client}
                              </p>
                              <p className="agenda-card__service">
                                {booking.service}
                              </p>
                              <p className="agenda-card__code tabular">
                                {booking.code}
                              </p>
                            </article>
                          </li>
                        ))}
                      </ul>
                    )}
                  </section>
                ))}
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
