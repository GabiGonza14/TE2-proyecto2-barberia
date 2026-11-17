import { useState } from "react";

import { formatDateLong, formatTime } from "../api/dates";
import type { Booking } from "../api/types";

type ConfirmationProps = {
  booking: Booking;
  onReset: () => void;
};

export default function Confirmation({ booking, onReset }: ConfirmationProps) {
  const [copied, setCopied] = useState(false);

  async function copyCode() {
    try {
      await navigator.clipboard?.writeText(booking.code);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section aria-labelledby="step-title" className="step-content">
      <h2 id="step-title">Reserva confirmada</h2>
      <p className="hint">Tu silla está lista.</p>

      <article className="ticket ticket--confirm">
        <div className="pole pole--ticket" aria-hidden="true" />
        <p className="ticket__eyebrow">Código de reserva</p>
        <p className="ticket__code">{booking.code}</p>
        <button type="button" className="button button--small" onClick={copyCode}>
          {copied ? "Código copiado" : "Copiar código"}
        </button>

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
              {formatTime(booking.start_at)} – {formatTime(booking.end_at)}
            </dd>
          </div>
        </dl>

        <p className="ticket__note">
          Guarda tu código: con él y tu teléfono puedes consultar o cancelar.
        </p>
      </article>

      <div className="step-actions">
        <button type="button" className="button button--ghost" onClick={onReset}>
          Hacer otra reserva
        </button>
      </div>
    </section>
  );
}
