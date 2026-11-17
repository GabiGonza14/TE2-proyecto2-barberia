import { formatDateLong } from "../api/dates";
import type { Availability } from "../api/types";

type TimeStepProps = {
  date: string;
  dates: string[];
  availability: Availability | null;
  loading: boolean;
  notice: string | null;
  selectedSlot: string | null;
  onDateChange: (date: string) => void;
  onSelectSlot: (slot: string) => void;
  onBack: () => void;
  onContinue: () => void;
};

const REASON_MESSAGES: Record<string, string> = {
  CLOSED: "La barbería está cerrada ese día (domingo o lunes). Elige otra fecha.",
  PAST_DATE: "Esa fecha ya pasó. Elige una fecha de hoy en adelante.",
  TOO_FAR_AHEAD:
    "Solo se puede reservar hasta con 14 días de anticipación. Elige una fecha más cercana.",
};

function groupSlots(slots: string[]) {
  return {
    morning: slots.filter((slot) => Number(slot.slice(0, 2)) < 12),
    afternoon: slots.filter((slot) => Number(slot.slice(0, 2)) >= 12),
  };
}

export default function TimeStep({
  date,
  dates,
  availability,
  loading,
  notice,
  selectedSlot,
  onDateChange,
  onSelectSlot,
  onBack,
  onContinue,
}: TimeStepProps) {
  const groups = availability ? groupSlots(availability.slots) : null;
  const reason = availability?.reason ?? null;

  return (
    <section aria-labelledby="step-title" className="step-content">
      <h2 id="step-title">Escoge tu hora</h2>
      <p className="hint">Solo mostramos horarios reales, con su limpieza incluida.</p>

      <label className="field field--inline" htmlFor="date">
        <span>Fecha</span>
        <select
          id="date"
          value={date}
          onChange={(event) => onDateChange(event.target.value)}
        >
          {dates.map((option) => (
            <option key={option} value={option}>
              {formatDateLong(option)}
            </option>
          ))}
        </select>
      </label>

      <div aria-live="polite">
        {notice ? (
          <p className="banner banner--alert" role="alert">
            {notice}
          </p>
        ) : null}

        {loading ? (
          <p className="hint">Buscando horarios…</p>
        ) : reason ? (
          <p className="banner" role="status">
            {REASON_MESSAGES[reason] ?? "No hay horarios para esa fecha."}
          </p>
        ) : groups && groups.morning.length + groups.afternoon.length > 0 ? (
          <div className="slot-groups">
            {groups.morning.length > 0 ? (
              <div>
                <h3 className="slot-group__title">Mañana</h3>
                <ul className="slot-grid">
                  {groups.morning.map((slot) => (
                    <li key={slot}>
                      <button
                        type="button"
                        aria-label={`Reservar a las ${slot}`}
                        aria-pressed={selectedSlot === slot}
                        className={`slot${
                          selectedSlot === slot ? " slot--selected" : ""
                        }`}
                        onClick={() => onSelectSlot(slot)}
                      >
                        {slot}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {groups.afternoon.length > 0 ? (
              <div>
                <h3 className="slot-group__title">Tarde</h3>
                <ul className="slot-grid">
                  {groups.afternoon.map((slot) => (
                    <li key={slot}>
                      <button
                        type="button"
                        aria-label={`Reservar a las ${slot}`}
                        aria-pressed={selectedSlot === slot}
                        className={`slot${
                          selectedSlot === slot ? " slot--selected" : ""
                        }`}
                        onClick={() => onSelectSlot(slot)}
                      >
                        {slot}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : (
          <p className="banner" role="status">
            No quedan horarios disponibles para esa fecha. Prueba con otro día.
          </p>
        )}
      </div>

      <div className="step-actions">
        <button type="button" className="button button--ghost" onClick={onBack}>
          Atrás
        </button>
        <button
          type="button"
          className="button button--primary"
          disabled={!selectedSlot}
          onClick={onContinue}
        >
          Continuar
        </button>
      </div>
    </section>
  );
}
