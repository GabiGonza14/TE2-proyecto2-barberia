import { type FormEvent, useState } from "react";

import { ApiError, cancelBooking, getBooking } from "../api/client";
import { formatDateLong, formatTime } from "../api/dates";
import type { Booking } from "../api/types";
import { PHONE_RE } from "../api/validation";

const NOT_FOUND_MESSAGE = "No encontramos una reserva con esos datos";
const WINDOW_CLOSED_MESSAGE =
  "Ya no se puede cancelar: faltan menos de 2 horas para tu cita";
const ALREADY_CANCELLED_MESSAGE = "Esta reserva ya estaba cancelada";

type LookupErrors = {
  code?: string;
  phone?: string;
  form?: string;
};

export default function LookupPage() {
  const [code, setCode] = useState("");
  const [phone, setPhone] = useState("");
  const [booking, setBooking] = useState<Booking | null>(null);
  const [errors, setErrors] = useState<LookupErrors>({});
  const [loading, setLoading] = useState(false);
  const [confirmingCancel, setConfirmingCancel] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  function resetSearch() {
    setBooking(null);
    setErrors({});
    setNotice(null);
    setConfirmingCancel(false);
  }

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors: LookupErrors = {};
    if (!code.trim()) nextErrors.code = "Escribe tu código de reserva";
    if (!PHONE_RE.test(phone.trim())) {
      nextErrors.phone = "Teléfono inválido: usa 6XXX-XXXX";
    }
    if (nextErrors.code || nextErrors.phone) {
      setErrors(nextErrors);
      return;
    }

    setErrors({});
    setNotice(null);
    setLoading(true);
    try {
      // BR-10: el backend normaliza, pero se envía en mayúsculas por claridad.
      const found = await getBooking(code.trim().toUpperCase(), phone.trim());
      setBooking(found);
      setConfirmingCancel(false);
    } catch (error) {
      if (error instanceof ApiError && error.code === "NOT_FOUND") {
        setErrors({ form: NOT_FOUND_MESSAGE });
      } else if (error instanceof ApiError && error.details.field === "phone") {
        setErrors({ phone: error.message });
      } else if (error instanceof ApiError && error.details.field === "code") {
        setErrors({ code: error.message });
      } else {
        setErrors({
          form:
            error instanceof ApiError
              ? error.message
              : "No pudimos conectar con el servidor. Intenta de nuevo.",
        });
      }
    } finally {
      setLoading(false);
    }
  }

  async function confirmCancel() {
    if (!booking) return;

    setCancelling(true);
    setErrors({});
    try {
      await cancelBooking(booking.code, phone.trim());
      setBooking({ ...booking, status: "CANCELADA" });
      setConfirmingCancel(false);
      setNotice("Reserva cancelada. El horario quedó libre para otro cliente.");
    } catch (error) {
      if (error instanceof ApiError && error.code === "CANCEL_WINDOW_CLOSED") {
        setConfirmingCancel(false);
        setErrors({ form: WINDOW_CLOSED_MESSAGE });
      } else if (
        error instanceof ApiError &&
        error.code === "ALREADY_CANCELLED"
      ) {
        setBooking({ ...booking, status: "CANCELADA" });
        setConfirmingCancel(false);
        setErrors({ form: ALREADY_CANCELLED_MESSAGE });
      } else if (error instanceof ApiError && error.code === "NOT_FOUND") {
        setConfirmingCancel(false);
        setErrors({ form: NOT_FOUND_MESSAGE });
      } else {
        setErrors({
          form:
            error instanceof ApiError
              ? error.message
              : "No pudimos conectar con el servidor. Intenta de nuevo.",
        });
      }
    } finally {
      setCancelling(false);
    }
  }

  return (
    <div className="page">
      <div className="page__inner">
        <h2>Tu reserva</h2>
        <p className="hint">
          Busca con el código y el teléfono que usaste al reservar.
        </p>

        {errors.form ? (
          <p className="banner banner--alert" role="alert">
            {errors.form}
          </p>
        ) : null}

        {notice ? (
          <p className="banner" role="status">
            {notice}
          </p>
        ) : null}

        {booking ? (
          <>
            <article className="ticket ticket--confirm">
              <div className="pole pole--ticket" aria-hidden="true" />
              <div className="ticket__topline">
                <p className="ticket__eyebrow">Código de reserva</p>
                <span
                  className={`badge ${
                    booking.status === "CANCELADA"
                      ? "badge--cancelled"
                      : "badge--confirmed"
                  }`}
                >
                  {booking.status}
                </span>
              </div>
              <p className="ticket__code">{booking.code}</p>
              <dl className="ticket__rows">
                <div>
                  <dt>Barbero</dt>
                  <dd>{booking.barber}</dd>
                </div>
                <div>
                  <dt>Servicio</dt>
                  <dd>{booking.service}</dd>
                </div>
                <div>
                  <dt>Fecha</dt>
                  <dd>{formatDateLong(booking.start_at.slice(0, 10))}</dd>
                </div>
                <div>
                  <dt>Hora</dt>
                  <dd className="tabular">
                    {formatTime(booking.start_at)} –{" "}
                    {formatTime(booking.end_at)}
                  </dd>
                </div>
              </dl>
              <p className="ticket__note">
                Guarda tu código: con él y tu teléfono puedes consultar o
                cancelar.
              </p>
            </article>

            <div className="lookup-actions">
              <button
                type="button"
                className="button button--ghost"
                onClick={resetSearch}
              >
                Buscar otra reserva
              </button>
              {booking.status !== "CANCELADA" && !confirmingCancel ? (
                <button
                  type="button"
                  className="button button--primary"
                  onClick={() => setConfirmingCancel(true)}
                >
                  Cancelar mi cita
                </button>
              ) : null}
            </div>

            {confirmingCancel ? (
              <div
                className="confirm-box"
                role="group"
                aria-label="Confirmar cancelación"
              >
                <p>¿Seguro? Liberarás el horario para otro cliente</p>
                <div className="confirm-box__actions">
                  <button
                    type="button"
                    className="button button--primary"
                    onClick={confirmCancel}
                    disabled={cancelling}
                  >
                    {cancelling ? "Cancelando…" : "Sí, cancelar"}
                  </button>
                  <button
                    type="button"
                    className="button button--ghost"
                    onClick={() => setConfirmingCancel(false)}
                    disabled={cancelling}
                  >
                    No, mantener
                  </button>
                </div>
              </div>
            ) : null}
          </>
        ) : (
          <form className="form lookup-form" onSubmit={search} noValidate>
            <label className="field" htmlFor="lookup-code">
              <span>Código de reserva</span>
              <input
                id="lookup-code"
                name="code"
                type="text"
                autoComplete="off"
                autoCapitalize="characters"
                placeholder="K7P2QX"
                value={code}
                aria-invalid={Boolean(errors.code)}
                aria-describedby={errors.code ? "lookup-code-error" : undefined}
                onChange={(event) => setCode(event.target.value)}
              />
              {errors.code ? (
                <p className="field-error" id="lookup-code-error" role="alert">
                  {errors.code}
                </p>
              ) : null}
            </label>

            <label className="field" htmlFor="lookup-phone">
              <span>Teléfono</span>
              <input
                id="lookup-phone"
                name="phone"
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                placeholder="6123-4567"
                value={phone}
                aria-invalid={Boolean(errors.phone)}
                aria-describedby={
                  errors.phone ? "lookup-phone-error" : undefined
                }
                onChange={(event) => setPhone(event.target.value)}
              />
              {errors.phone ? (
                <p className="field-error" id="lookup-phone-error" role="alert">
                  {errors.phone}
                </p>
              ) : null}
            </label>

            <div className="lookup-actions">
              <button
                type="submit"
                className="button button--primary"
                disabled={loading}
              >
                {loading ? "Buscando…" : "Buscar reserva"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
