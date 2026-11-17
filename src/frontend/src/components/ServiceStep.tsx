import type { Service } from "../api/types";

type ServiceStepProps = {
  services: Service[];
  loading: boolean;
  selected: Service | null;
  onSelect: (service: Service) => void;
};

export default function ServiceStep({
  services,
  loading,
  selected,
  onSelect,
}: ServiceStepProps) {
  return (
    <section aria-labelledby="step-title" className="step-content">
      <h2 id="step-title">Elige tu corte</h2>
      <p className="hint">Servicio, duración y precio claros, sin sorpresas.</p>
      {loading ? (
        <p className="hint">Cargando servicios…</p>
      ) : services.length === 0 ? (
        <p className="hint">No hay servicios disponibles.</p>
      ) : (
        <ul className="card-grid">
          {services.map((service) => (
            <li key={service.id}>
              <button
                type="button"
                aria-label={`Elegir ${service.name}`}
                aria-pressed={selected?.id === service.id}
                className={`choice${
                  selected?.id === service.id ? " choice--selected" : ""
                }`}
                onClick={() => onSelect(service)}
              >
                <span className="choice__title">{service.name}</span>
                <span className="choice__meta">
                  {service.duration_min} min · ${service.price.toFixed(2)}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
