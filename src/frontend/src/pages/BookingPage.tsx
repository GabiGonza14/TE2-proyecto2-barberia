import { useEffect, useMemo, useState } from "react";

import {
  ApiError,
  createBooking,
  getAvailability,
  getBarbers,
  getServices,
} from "../api/client";
import { bookableDates } from "../api/dates";
import type { Availability, Barber, Booking, Service } from "../api/types";
import { PHONE_RE } from "../api/validation";
import BarberStep from "../components/BarberStep";
import BookingTicket from "../components/BookingTicket";
import Confirmation from "../components/Confirmation";
import DetailsStep, { type DetailsErrors } from "../components/DetailsStep";
import ServiceStep from "../components/ServiceStep";
import StepIndicator from "../components/StepIndicator";
import TimeStep from "../components/TimeStep";

type Step = 1 | 2 | 3 | 4;

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "No pudimos conectar con el servidor. Intenta de nuevo.";
}

export default function BookingPage() {
  const dates = useMemo(() => bookableDates(), []);
  const [step, setStep] = useState<Step>(1);
  const [services, setServices] = useState<Service[]>([]);
  const [barbers, setBarbers] = useState<Barber[]>([]);
  const [service, setService] = useState<Service | null>(null);
  const [barber, setBarber] = useState<Barber | null>(null);
  const [date, setDate] = useState(dates[0]);
  const [availability, setAvailability] = useState<Availability | null>(null);
  const [slot, setSlot] = useState<string | null>(null);
  const [booking, setBooking] = useState<Booking | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [loadingAvailability, setLoadingAvailability] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [clientName, setClientName] = useState("");
  const [clientPhone, setClientPhone] = useState("");
  const [errors, setErrors] = useState<DetailsErrors>({});

  useEffect(() => {
    let cancelled = false;

    Promise.all([getServices(), getBarbers()])
      .then(([loadedServices, loadedBarbers]) => {
        if (cancelled) return;
        setServices(loadedServices);
        setBarbers(loadedBarbers);
      })
      .catch((error) => {
        if (!cancelled) setCatalogError(errorMessage(error));
      })
      .finally(() => {
        if (!cancelled) setLoadingCatalog(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (step !== 3 || !service || !barber) return;

    let cancelled = false;
    setLoadingAvailability(true);
    setAvailability(null);
    setSlot(null);

    getAvailability(barber.id, service.id, date)
      .then((data) => {
        if (!cancelled) setAvailability(data);
      })
      .catch((error) => {
        if (!cancelled) {
          setAvailability(null);
          setNotice(errorMessage(error));
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingAvailability(false);
      });

    return () => {
      cancelled = true;
    };
  }, [step, service, barber, date]);

  function chooseService(next: Service) {
    setService(next);
    setBarber(null);
    setSlot(null);
    setNotice(null);
    setStep(2);
  }

  function chooseBarber(next: Barber) {
    setBarber(next);
    setSlot(null);
    setNotice(null);
    setStep(3);
  }

  function chooseDate(next: string) {
    setDate(next);
    setNotice(null);
  }

  function chooseSlot(next: string) {
    setSlot(next);
    setNotice(null);
  }

  async function submitBooking() {
    if (!service || !barber || !slot) return;

    const trimmedName = clientName.trim();
    const nextErrors: DetailsErrors = {};

    if (trimmedName.length < 2 || trimmedName.length > 60) {
      nextErrors.name = "El nombre debe tener entre 2 y 60 caracteres";
    }
    if (!PHONE_RE.test(clientPhone.trim())) {
      nextErrors.phone =
        "Teléfono inválido: use 8 dígitos que empiecen por 6 (6XXX-XXXX)";
    }
    if (nextErrors.name || nextErrors.phone) {
      setErrors(nextErrors);
      return;
    }

    setErrors({});
    setSubmitting(true);
    try {
      const created = await createBooking({
        barber_id: barber.id,
        service_id: service.id,
        start_at: `${date}T${slot}:00-05:00`,
        client_name: trimmedName,
        client_phone: clientPhone.trim(),
      });
      setBooking(created);
    } catch (error) {
      if (error instanceof ApiError && error.code === "SLOT_TAKEN") {
        setNotice("Ese horario ya no está disponible");
        setStep(3);
        return;
      }
      if (error instanceof ApiError && error.details.field === "client_name") {
        setErrors({ name: error.message });
        return;
      }
      if (error instanceof ApiError && error.details.field === "client_phone") {
        setErrors({ phone: error.message });
        return;
      }
      setErrors({ form: errorMessage(error) });
    } finally {
      setSubmitting(false);
    }
  }

  function reset() {
    setBooking(null);
    setService(null);
    setBarber(null);
    setSlot(null);
    setDate(dates[0]);
    setClientName("");
    setClientPhone("");
    setErrors({});
    setNotice(null);
    setStep(1);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <BookingTicket
          service={service}
          barber={barber}
          date={service && barber ? date : null}
          slot={slot}
          clientName={clientName}
        />

        <p className="sidebar__foot">America/Panama · 09:00–19:00</p>
      </aside>

      <main className="main">
        <div className="main__inner">
          <StepIndicator current={step} />

          {catalogError ? (
            <p className="banner banner--alert" role="alert">
              {catalogError}
            </p>
          ) : null}

          {booking ? (
            <Confirmation booking={booking} onReset={reset} />
          ) : step === 1 ? (
            <ServiceStep
              services={services}
              loading={loadingCatalog}
              selected={service}
              onSelect={chooseService}
            />
          ) : step === 2 ? (
            <BarberStep
              barbers={barbers}
              loading={loadingCatalog}
              selected={barber}
              onSelect={chooseBarber}
            />
          ) : step === 3 ? (
            <TimeStep
              date={date}
              dates={dates}
              availability={availability}
              loading={loadingAvailability}
              notice={notice}
              selectedSlot={slot}
              onDateChange={chooseDate}
              onSelectSlot={chooseSlot}
              onBack={() => setStep(2)}
              onContinue={() => setStep(4)}
            />
          ) : (
            <DetailsStep
              name={clientName}
              phone={clientPhone}
              errors={errors}
              submitting={submitting}
              onNameChange={setClientName}
              onPhoneChange={setClientPhone}
              onBack={() => setStep(3)}
              onSubmit={submitBooking}
            />
          )}
        </div>
      </main>
    </div>
  );
}
