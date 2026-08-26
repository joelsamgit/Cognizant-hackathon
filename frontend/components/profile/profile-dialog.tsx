"use client";

import { useEffect, useRef, useState } from "react";
import { Envelope, MapPin, SpinnerGap, UserCircle, X } from "@phosphor-icons/react";

import { PetSelector } from "@/components/auth/pet-selector";
import { Button } from "@/components/ui/button";
import type { PetType, ProfilePayload, UserProfile } from "@/types/user";


interface ProfileDialogProps {
  user: UserProfile;
  saving: boolean;
  error: string | null;
  onSubmit: (payload: ProfilePayload) => Promise<void>;
  onClose: () => void;
}

const inputClass =
  "min-h-11 w-full rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] px-3.5 py-2.5 text-sm text-[var(--text)] transition-colors placeholder:text-[var(--text-soft)] hover:border-[var(--line-strong)] focus:border-[var(--accent)] focus:outline-none";

export function ProfileDialog({
  user,
  saving,
  error,
  onSubmit,
  onClose,
}: ProfileDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [fullName, setFullName] = useState(user.full_name);
  const [place, setPlace] = useState(user.place);
  const [pets, setPets] = useState<PetType[]>(user.pets);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    dialog.showModal();
    return () => dialog.close();
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: Record<string, string> = {};
    if (fullName.trim().length < 2) nextErrors.fullName = "Enter your name.";
    if (place.trim().length < 2) nextErrors.place = "Enter your city or place.";
    if (!pets.length) nextErrors.pets = "Choose at least one option.";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    await onSubmit({
      full_name: fullName.trim(),
      place: place.trim(),
      pets,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || user.timezone,
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
      className="m-auto max-h-[calc(100dvh-2rem)] w-[min(38rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-0 text-[var(--text)] shadow-[var(--shadow)]"
      aria-labelledby="profile-title"
    >
      <form onSubmit={handleSubmit} noValidate>
        <div className="flex items-start justify-between border-b border-[var(--line)] px-5 py-5 sm:px-6">
          <div>
            <p className="text-sm font-semibold text-[var(--accent)]">Your household</p>
            <h2 id="profile-title" className="mt-1 text-xl font-bold tracking-[-0.025em]">
              Profile settings
            </h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              Keep the context behind your garden up to date.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="rounded-full p-2 text-[var(--text-muted)] transition-colors hover:bg-[var(--page-muted)] hover:text-[var(--text)] disabled:opacity-50"
            aria-label="Close profile settings"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        <div className="max-h-[calc(100dvh-13rem)] space-y-5 overflow-y-auto px-5 py-5 sm:px-6">
          {error && (
            <div role="alert" className="rounded-xl bg-[var(--risk-soft)] px-4 py-3 text-sm font-medium text-[var(--risk)]">
              {error}
            </div>
          )}

          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Your name" error={errors.fullName} icon={<UserCircle size={17} />}>
              <input
                autoFocus
                autoComplete="name"
                value={fullName}
                onChange={(event) => {
                  setFullName(event.target.value);
                  setErrors((current) => ({ ...current, fullName: "" }));
                }}
                className={inputClass}
                maxLength={120}
              />
            </Field>
            <Field label="City or place" error={errors.place} icon={<MapPin size={17} />}>
              <input
                autoComplete="address-level2"
                value={place}
                onChange={(event) => {
                  setPlace(event.target.value);
                  setErrors((current) => ({ ...current, place: "" }));
                }}
                className={inputClass}
                maxLength={160}
              />
            </Field>
          </div>

          <Field label="Email address" icon={<Envelope size={17} />} hint="Email changes are not enabled yet.">
            <input value={user.email} readOnly className={`${inputClass} opacity-70`} />
          </Field>

          <PetSelector
            value={pets}
            onChange={(nextPets) => {
              setPets(nextPets);
              setErrors((current) => ({ ...current, pets: "" }));
            }}
            error={errors.pets}
          />

          <div className="rounded-xl border border-[var(--line)] bg-[var(--page-muted)] px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--text-soft)]">
              Local timezone
            </p>
            <p className="mt-1 text-sm font-semibold text-[var(--text)]">{user.timezone}</p>
            <p className="mt-1 text-xs leading-5 text-[var(--text-muted)]">
              Detected from this device for correctly timed reminders.
            </p>
          </div>
        </div>

        <div className="flex flex-col-reverse gap-2 border-t border-[var(--line)] bg-[var(--surface-raised)] px-5 py-4 sm:flex-row sm:justify-end sm:px-6">
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            {saving && <SpinnerGap size={18} className="animate-spin" aria-hidden="true" />}
            {saving ? "Saving" : "Save profile"}
          </Button>
        </div>
      </form>
    </dialog>
  );
}

function Field({
  label,
  error,
  icon,
  hint,
  children,
}: {
  label: string;
  error?: string;
  icon?: React.ReactNode;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="grid gap-2 text-sm font-semibold text-[var(--text)]">
      <span className="flex items-center gap-2">
        {icon}
        {label}
      </span>
      {children}
      {error ? (
        <span className="text-xs font-medium text-[var(--risk)]">{error}</span>
      ) : hint ? (
        <span className="text-xs font-medium text-[var(--text-soft)]">{hint}</span>
      ) : null}
    </label>
  );
}
