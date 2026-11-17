import type { FormEvent } from "react";

export type DetailsErrors = {
  name?: string;
  phone?: string;
  form?: string;
};

type DetailsStepProps = {
  name: string;
  phone: string;
  errors: DetailsErrors;
  submitting: boolean;
  onNameChange: (value: string) => void;
  onPhoneChange: (value: string) => void;
  onBack: () => void;
  onSubmit: () => void;
};

export default function DetailsStep({
  name,
  phone,
  errors,
  submitting,
  onNameChange,
  onPhoneChange,
  onBack,
  onSubmit,
}: DetailsStepProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <section aria-labelledby="step-title" className="step-content">
      <h2 id="step-title">Tus datos</h2>
      <p className="hint">Así sabemos a nombre de quién va la silla.</p>

      <form className="form" onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="client-name">Nombre</label>
          <input
            id="client-name"
            name="client_name"
            type="text"
            autoComplete="name"
            value={name}
            aria-invalid={Boolean(errors.name)}
            aria-describedby={errors.name ? "client-name-error" : undefined}
            onChange={(event) => onNameChange(event.target.value)}
          />
          {errors.name ? (
            <p className="field-error" id="client-name-error" role="alert">
              {errors.name}
            </p>
          ) : null}
        </div>

        <div className="field">
          <label htmlFor="client-phone">Teléfono</label>
          <input
            id="client-phone"
            name="client_phone"
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            placeholder="6123-4567"
            value={phone}
            aria-invalid={Boolean(errors.phone)}
            aria-describedby={errors.phone ? "client-phone-error" : undefined}
            onChange={(event) => onPhoneChange(event.target.value)}
          />
          {errors.phone ? (
            <p className="field-error" id="client-phone-error" role="alert">
              {errors.phone}
            </p>
          ) : null}
        </div>

        {errors.form ? (
          <p className="banner banner--alert" role="alert">
            {errors.form}
          </p>
        ) : null}

        <div className="step-actions">
          <button
            type="button"
            className="button button--ghost"
            onClick={onBack}
            disabled={submitting}
          >
            Atrás
          </button>
          <button
            type="submit"
            className="button button--primary"
            disabled={submitting}
          >
            {submitting ? "Confirmando…" : "Confirmar reserva"}
          </button>
        </div>
      </form>
    </section>
  );
}
