type StepIndicatorProps = {
  current: 1 | 2 | 3 | 4;
};

const STEP_LABELS = ["Servicio", "Barbero", "Hora", "Datos"] as const;

export default function StepIndicator({ current }: StepIndicatorProps) {
  return (
    <div className="steps">
      <p className="steps__count">Paso {current} de 4</p>
      <ol className="steps__list">
        {STEP_LABELS.map((label, index) => {
          const step = index + 1;
          const state =
            step < current ? "done" : step === current ? "current" : "pending";
          return (
            <li key={label} className={`steps__item steps__item--${state}`}>
              <span className="steps__number">{step}</span>
              <span className="steps__label">{label}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
