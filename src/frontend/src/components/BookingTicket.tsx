import { formatDateLong } from "../api/dates";
import type { Barber, Service } from "../api/types";

type BookingTicketProps = {
  service: Service | null;
  barber: Barber | null;
  date: string | null;
  slot: string | null;
  clientName: string;
};

export default function BookingTicket({
  service,
  barber,
  date,
  slot,
  clientName,
}: BookingTicketProps) {
  const duration = service ? `${service.duration_min} min` : null;

  return (
    <article className="ticket ticket--summary">
      <div className="pole" aria-hidden="true" />
      <p className="ticket__eyebrow">Tu ticket</p>
      <dl className="ticket__rows">
        <div>
          <dt>Servicio</dt>
          <dd>
            {service ? service.name : "—"}
            {service ? (
              <span className="ticket__sub">
                {duration} · ${service.price.toFixed(2)}
              </span>
            ) : null}
          </dd>
        </div>
        <div>
          <dt>Barbero</dt>
          <dd>{barber ? barber.name : "—"}</dd>
        </div>
        <div>
          <dt>Fecha</dt>
          <dd>{date ? formatDateLong(date) : "—"}</dd>
        </div>
        <div>
          <dt>Hora</dt>
          <dd className="tabular">{slot ?? "—"}</dd>
        </div>
        <div>
          <dt>A nombre de</dt>
          <dd>{clientName.trim() || "—"}</dd>
        </div>
      </dl>
    </article>
  );
}
