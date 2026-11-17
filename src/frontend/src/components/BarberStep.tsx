import type { Barber } from "../api/types";

type BarberStepProps = {
  barbers: Barber[];
  loading: boolean;
  selected: Barber | null;
  onSelect: (barber: Barber) => void;
};

export default function BarberStep({
  barbers,
  loading,
  selected,
  onSelect,
}: BarberStepProps) {
  return (
    <section aria-labelledby="step-title" className="step-content">
      <h2 id="step-title">¿Con quién?</h2>
      <p className="hint">Elige a tu barbero.</p>
      {loading ? (
        <p className="hint">Cargando barberos…</p>
      ) : barbers.length === 0 ? (
        <p className="hint">No hay barberos disponibles.</p>
      ) : (
        <ul className="barber-grid">
          {barbers.map((barber) => (
            <li key={barber.id}>
              <button
                type="button"
                aria-label={`Elegir ${barber.name}`}
                aria-pressed={selected?.id === barber.id}
                className={`barber${
                  selected?.id === barber.id ? " barber--selected" : ""
                }`}
                onClick={() => onSelect(barber)}
              >
                <span className="barber__initial" aria-hidden="true">
                  {barber.name.slice(0, 1)}
                </span>
                <span className="barber__name">{barber.name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
