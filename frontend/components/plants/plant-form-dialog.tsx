"use client";

import { useEffect, useRef, useState } from "react";
import { SpinnerGap, X } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import { toDateTimeLocal, toUtcIso } from "@/lib/dates";
import type { Plant, PlantPayload, Sunlight } from "@/types/plant";
import { sunlightOptions } from "@/types/plant";


interface PlantFormDialogProps {
  plant?: Plant;
  saving: boolean;
  error: string | null;
  onSubmit: (payload: PlantPayload) => Promise<void>;
  onClose: () => void;
}

interface FormValues {
  nickname: string;
  species: string;
  room: string;
  sunlight: Sunlight;
  watering_frequency: string;
  last_watered: string;
  notes: string;
}

type FormErrors = Partial<Record<keyof FormValues, string>>;

function initialValues(plant?: Plant): FormValues {
  return {
    nickname: plant?.nickname ?? "",
    species: plant?.species ?? "",
    room: plant?.room ?? "",
    sunlight: plant?.sunlight ?? "Indirect Light",
    watering_frequency: plant ? String(plant.watering_frequency) : "7",
    last_watered: toDateTimeLocal(plant?.last_watered),
    notes: plant?.notes ?? "",
  };
}

function validate(values: FormValues): FormErrors {
  const errors: FormErrors = {};
  if (!values.nickname.trim()) errors.nickname = "Add a nickname.";
  if (!values.species.trim()) errors.species = "Add the plant species.";
  if (!values.room.trim()) errors.room = "Add a room or location.";

  const frequency = Number(values.watering_frequency);
  if (!Number.isInteger(frequency) || frequency < 1 || frequency > 365) {
    errors.watering_frequency = "Use a whole number from 1 to 365.";
  }

  if (!values.last_watered) {
    errors.last_watered = "Choose when this plant was last watered.";
  } else if (new Date(values.last_watered).getTime() > Date.now()) {
    errors.last_watered = "Last watered cannot be in the future.";
  }

  return errors;
}

const inputClass =
  "min-h-11 w-full rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] px-3.5 py-2.5 text-sm text-[var(--text)] transition-colors placeholder:text-[var(--text-soft)] hover:border-[var(--line-strong)] focus:border-[var(--accent)] focus:outline-none";

export function PlantFormDialog({ plant, saving, error, onSubmit, onClose }: PlantFormDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [values, setValues] = useState<FormValues>(() => initialValues(plant));
  const [errors, setErrors] = useState<FormErrors>({});
  const title = plant ? `Edit ${plant.nickname}` : "Add a plant";

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    dialog.showModal();
    return () => dialog.close();
  }, []);

  function setField<K extends keyof FormValues>(field: K, value: FormValues[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    await onSubmit({
      nickname: values.nickname.trim(),
      species: values.species.trim(),
      room: values.room.trim(),
      sunlight: values.sunlight,
      watering_frequency: Number(values.watering_frequency),
      last_watered: toUtcIso(values.last_watered),
      notes: values.notes.trim() || null,
    });
  }

  return (
    <dialog
      ref={dialogRef}
      onCancel={(event) => {
        if (saving) event.preventDefault();
        else onClose();
      }}
      onClose={onClose}
      className="m-auto max-h-[calc(100dvh-2rem)] w-[min(42rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-0 text-[var(--text)] shadow-[var(--shadow)]"
      aria-labelledby="plant-form-title"
    >
      <form onSubmit={handleSubmit} noValidate>
        <div className="flex items-start justify-between border-b border-[var(--line)] px-5 py-5 sm:px-6">
          <div>
            <h2 id="plant-form-title" className="text-xl font-bold tracking-[-0.025em]">
              {title}
            </h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              Watering urgency is calculated automatically.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="rounded-full p-2 text-[var(--text-muted)] transition-colors hover:bg-[var(--page-muted)] hover:text-[var(--text)] disabled:opacity-50"
            aria-label="Close plant form"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        <div className="max-h-[calc(100dvh-13rem)] overflow-y-auto px-5 py-5 sm:px-6">
          {error && (
            <div role="alert" className="mb-5 rounded-xl bg-[var(--risk-soft)] px-4 py-3 text-sm font-medium text-[var(--risk)]">
              {error}
            </div>
          )}

          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Nickname" error={errors.nickname}>
              <input
                autoFocus
                value={values.nickname}
                onChange={(event) => setField("nickname", event.target.value)}
                className={inputClass}
                maxLength={100}
                aria-invalid={Boolean(errors.nickname)}
                placeholder="e.g. Greeny"
              />
            </Field>

            <Field label="Species" error={errors.species}>
              <input
                value={values.species}
                onChange={(event) => setField("species", event.target.value)}
                className={inputClass}
                maxLength={160}
                aria-invalid={Boolean(errors.species)}
                placeholder="e.g. Golden Pothos"
              />
            </Field>

            <Field label="Room or location" error={errors.room}>
              <input
                value={values.room}
                onChange={(event) => setField("room", event.target.value)}
                className={inputClass}
                maxLength={100}
                aria-invalid={Boolean(errors.room)}
                placeholder="e.g. Living Room"
              />
            </Field>

            <Field label="Sunlight" error={errors.sunlight}>
              <select
                value={values.sunlight}
                onChange={(event) => setField("sunlight", event.target.value as Sunlight)}
                className={inputClass}
              >
                {sunlightOptions.map((option) => (
                  <option key={option}>{option}</option>
                ))}
              </select>
            </Field>

            <Field label="Water every (days)" error={errors.watering_frequency}>
              <input
                type="number"
                min={1}
                max={365}
                step={1}
                value={values.watering_frequency}
                onChange={(event) => setField("watering_frequency", event.target.value)}
                className={inputClass}
                aria-invalid={Boolean(errors.watering_frequency)}
              />
            </Field>

            <Field label="Last watered" error={errors.last_watered}>
              <input
                type="datetime-local"
                value={values.last_watered}
                max={toDateTimeLocal()}
                onChange={(event) => setField("last_watered", event.target.value)}
                className={inputClass}
                aria-invalid={Boolean(errors.last_watered)}
              />
            </Field>

            <div className="sm:col-span-2">
              <Field label="Care notes" error={errors.notes} hint="Optional, up to 2,000 characters">
                <textarea
                  value={values.notes}
                  onChange={(event) => setField("notes", event.target.value)}
                  className={`${inputClass} min-h-28 resize-y`}
                  maxLength={2000}
                  placeholder="Growth, placement, soil, or anything worth remembering"
                />
              </Field>
            </div>
          </div>
        </div>

        <div className="flex flex-col-reverse gap-2 border-t border-[var(--line)] bg-[var(--surface-raised)] px-5 py-4 sm:flex-row sm:justify-end sm:px-6">
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            {saving && <SpinnerGap size={18} className="animate-spin" aria-hidden="true" />}
            {saving ? "Saving" : plant ? "Save changes" : "Add plant"}
          </Button>
        </div>
      </form>
    </dialog>
  );
}

function Field({
  label,
  error,
  hint,
  children,
}: {
  label: string;
  error?: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="grid gap-2 text-sm font-semibold text-[var(--text)]">
      <span>{label}</span>
      {children}
      {error ? (
        <span className="text-xs font-medium text-[var(--risk)]">{error}</span>
      ) : hint ? (
        <span className="text-xs font-medium text-[var(--text-soft)]">{hint}</span>
      ) : null}
    </label>
  );
}

