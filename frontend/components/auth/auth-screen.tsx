"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle,
  Leaf,
  LockKey,
  MapPin,
  SpinnerGap,
  UserCircle,
} from "@phosphor-icons/react";

import { PetSelector } from "@/components/auth/pet-selector";
import { Button } from "@/components/ui/button";
import { googleAuth, login, signup } from "@/services/auth";
import { ApiError } from "@/services/plants";
import type { PetType, UserProfile } from "@/types/user";


type Mode = "login" | "signup";

interface AuthScreenProps {
  onAuthenticated: (user: UserProfile) => void;
  initialError?: string;
}

interface FormValues {
  fullName: string;
  place: string;
  pets: PetType[];
  email: string;
  password: string;
  confirmPassword: string;
}

const inputClass =
  "min-h-12 w-full rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] px-4 py-3 text-sm text-[var(--text)] transition-colors placeholder:text-[var(--text-soft)] hover:border-[var(--line-strong)] focus:border-[var(--accent)] focus:outline-none";

export function AuthScreen({ onAuthenticated, initialError }: AuthScreenProps) {
  const [mode, setMode] = useState<Mode>("login");
  const [values, setValues] = useState<FormValues>({
    fullName: "",
    place: "",
    pets: [],
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState(initialError ?? "");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId || document.querySelector('script[src="https://accounts.google.com/gsi/client"]')) return;
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
  }, []);

  function switchMode(nextMode: Mode) {
    setMode(nextMode);
    setErrors({});
    setServerError("");
  }

  function setField(field: keyof FormValues, value: string | PetType[]) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: "" }));
    setServerError("");
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: Record<string, string> = {};
    if (!values.email.trim()) nextErrors.email = "Enter your email address.";
    if (!values.password) nextErrors.password = "Enter your password.";

    if (mode === "signup") {
      if (values.fullName.trim().length < 2) nextErrors.fullName = "Enter your name.";
      if (values.place.trim().length < 2) nextErrors.place = "Enter your city or place.";
      if (!values.pets.length) nextErrors.pets = "Choose at least one option.";
      if (values.password.length < 8) nextErrors.password = "Use at least 8 characters.";
      if (values.password !== values.confirmPassword) {
        nextErrors.confirmPassword = "Passwords do not match.";
      }
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    setSubmitting(true);
    setServerError("");
    try {
      const user =
        mode === "signup"
          ? await signup({
              email: values.email.trim(),
              password: values.password,
              full_name: values.fullName.trim(),
              place: values.place.trim(),
              pets: values.pets,
              timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
            })
          : await login({
              email: values.email.trim(),
              password: values.password,
            });
      onAuthenticated(user);
    } catch (error) {
      setServerError(
        error instanceof ApiError
          ? error.message
          : "We could not complete that request. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function handleGoogle() {
    if (mode === "signup") {
      const nextErrors: Record<string, string> = {};
      if (values.fullName.trim().length < 2) nextErrors.fullName = "Enter your name first.";
      if (values.place.trim().length < 2) nextErrors.place = "Enter your city or place first.";
      if (!values.pets.length) nextErrors.pets = "Choose your pets first.";
      if (Object.keys(nextErrors).length) {
        setErrors(nextErrors);
        return;
      }
    }
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    const google = (window as Window & { google?: GoogleAccounts }).google;
    if (!clientId || !google?.accounts?.id) {
      setServerError("Google sign-in is not configured yet. Add NEXT_PUBLIC_GOOGLE_CLIENT_ID to the frontend environment.");
      return;
    }
    setSubmitting(true);
    google.accounts.id.initialize({
      client_id: clientId,
      callback: async ({ credential }) => {
        try {
          const user = await googleAuth({
            credential,
            ...(mode === "signup"
              ? { full_name: values.fullName.trim(), place: values.place.trim(), pets: values.pets }
              : {}),
          });
          onAuthenticated(user);
        } catch (error) {
          setServerError(error instanceof ApiError ? error.message : "Google sign-in could not be completed.");
        } finally {
          setSubmitting(false);
        }
      },
    });
    google.accounts.id.prompt(() => setSubmitting(false));
  }

  return (
    <main className="grid min-h-[100dvh] place-items-center px-4 py-8 sm:px-6">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-[2rem] border border-[var(--line)] bg-[var(--surface)] shadow-[var(--shadow)] lg:grid-cols-[0.9fr_1.1fr]">
        <section className="relative hidden overflow-hidden bg-[var(--surface-strong)] p-10 text-[var(--page)] lg:flex lg:flex-col lg:justify-between">
          <div className="absolute -right-24 -top-24 size-72 rounded-full border border-[var(--healthy)]/30" />
          <div className="absolute -bottom-32 -left-20 size-80 rounded-full bg-[var(--healthy)]/15" />
          <div className="relative">
            <div className="flex size-12 items-center justify-center rounded-2xl bg-[var(--healthy)]/25">
              <Leaf size={25} weight="fill" aria-hidden="true" />
            </div>
            <p className="mt-7 text-sm font-semibold uppercase tracking-[0.18em] opacity-70">
              Plant Guardian
            </p>
            <h1 className="mt-3 max-w-sm text-4xl font-bold leading-[1.08] tracking-[-0.045em]">
              Care that understands your home.
            </h1>
            <p className="mt-5 max-w-sm text-sm leading-7 opacity-75">
              Your garden, watering history, reminders, and household profile stay together in one calm place.
            </p>
          </div>
          <ul className="relative space-y-4 text-sm font-medium">
            {[
              "A private plant collection for every account",
              "Urgency scores and care history preserved",
              "Pet-aware context ready for safer guidance",
            ].map((item) => (
              <li key={item} className="flex items-center gap-3">
                <CheckCircle size={19} weight="fill" aria-hidden="true" />
                {item}
              </li>
            ))}
          </ul>
        </section>

        <section className="px-5 py-7 sm:px-10 sm:py-10 lg:px-12">
          <div className="flex items-center gap-3 lg:hidden">
            <div className="flex size-10 items-center justify-center rounded-xl bg-[var(--surface-strong)] text-[var(--healthy)]">
              <Leaf size={21} weight="fill" aria-hidden="true" />
            </div>
            <span className="font-bold tracking-[-0.025em]">Plant Guardian</span>
          </div>

          <div className="mt-7 lg:mt-0">
            <p className="text-sm font-semibold text-[var(--accent)]">
              {mode === "login" ? "Welcome back" : "Create your garden account"}
            </p>
            <h2 className="mt-2 text-3xl font-bold tracking-[-0.04em] text-[var(--text)]">
              {mode === "login" ? "Sign in to your garden" : "Tell us about your home"}
            </h2>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
              {mode === "login"
                ? "Pick up exactly where you left off."
                : "Name, place, and pets help keep your care space personal and relevant."}
            </p>
          </div>

          <div className="mt-6 grid grid-cols-2 rounded-full bg-[var(--page-muted)] p-1" role="tablist" aria-label="Account action">
            {(["login", "signup"] as const).map((option) => (
              <button
                key={option}
                type="button"
                role="tab"
                aria-selected={mode === option}
                onClick={() => switchMode(option)}
                className={`min-h-10 rounded-full px-4 text-sm font-semibold transition-colors ${
                  mode === option
                    ? "bg-[var(--surface-raised)] text-[var(--text)] shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text)]"
                }`}
              >
                {option === "login" ? "Log in" : "Sign up"}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={handleGoogle}
            disabled={submitting}
            className="mt-5 flex min-h-12 w-full items-center justify-center gap-3 rounded-xl border border-[var(--line-strong)] bg-[var(--surface-raised)] px-4 text-sm font-bold text-[var(--text)] transition-colors hover:border-[var(--accent)] hover:bg-[var(--accent-soft)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className="text-lg font-black text-[var(--healthy)]">G</span>
            Continue with Google
          </button>
          <div className="mt-5 flex items-center gap-3 text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-soft)]"><span className="h-px flex-1 bg-[var(--line)]" />or use email<span className="h-px flex-1 bg-[var(--line)]" /></div>

          <form className="mt-6 grid gap-4" onSubmit={handleSubmit} noValidate>
            {serverError && (
              <div role="alert" className="rounded-xl bg-[var(--risk-soft)] px-4 py-3 text-sm font-medium text-[var(--risk)]">
                {serverError}
              </div>
            )}

            {mode === "signup" && (
              <>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Your name" error={errors.fullName} icon={<UserCircle size={17} />}>
                    <input
                      autoFocus
                      autoComplete="name"
                      value={values.fullName}
                      onChange={(event) => setField("fullName", event.target.value)}
                      className={inputClass}
                      placeholder="Asha Nair"
                      maxLength={120}
                    />
                  </Field>
                  <Field label="City or place" error={errors.place} icon={<MapPin size={17} />}>
                    <input
                      autoComplete="address-level2"
                      value={values.place}
                      onChange={(event) => setField("place", event.target.value)}
                      className={inputClass}
                      placeholder="Kochi"
                      maxLength={160}
                    />
                  </Field>
                </div>
                <PetSelector
                  value={values.pets}
                  onChange={(pets) => setField("pets", pets)}
                  error={errors.pets}
                />
              </>
            )}

            <Field label="Email address" error={errors.email}>
              <input
                autoFocus={mode === "login"}
                type="email"
                autoComplete="email"
                value={values.email}
                onChange={(event) => setField("email", event.target.value)}
                className={inputClass}
                placeholder="you@example.com"
                maxLength={320}
              />
            </Field>

            <div className={`grid gap-4 ${mode === "signup" ? "sm:grid-cols-2" : ""}`}>
              <Field label="Password" error={errors.password} icon={<LockKey size={17} />}>
                <input
                  type="password"
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  value={values.password}
                  onChange={(event) => setField("password", event.target.value)}
                  className={inputClass}
                  placeholder={mode === "signup" ? "At least 8 characters" : "Your password"}
                  maxLength={128}
                />
              </Field>
              {mode === "signup" && (
                <Field label="Confirm password" error={errors.confirmPassword}>
                  <input
                    type="password"
                    autoComplete="new-password"
                    value={values.confirmPassword}
                    onChange={(event) => setField("confirmPassword", event.target.value)}
                    className={inputClass}
                    placeholder="Repeat password"
                    maxLength={128}
                  />
                </Field>
              )}
            </div>

            <Button type="submit" disabled={submitting} className="mt-1 w-full">
              {submitting && <SpinnerGap size={18} className="animate-spin" aria-hidden="true" />}
              {submitting ? "Please wait" : mode === "login" ? "Log in" : "Create account"}
            </Button>
          </form>
        </section>
      </div>
    </main>
  );
}

interface GoogleAccounts {
  accounts: {
    id: {
      initialize: (options: { client_id: string; callback: (response: { credential: string }) => void }) => void;
      prompt: (listener?: () => void) => void;
    };
  };
}

function Field({
  label,
  error,
  icon,
  children,
}: {
  label: string;
  error?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <label className="grid gap-2 text-sm font-semibold text-[var(--text)]">
      <span className="flex items-center gap-2">
        {icon}
        {label}
      </span>
      {children}
      {error && <span className="text-xs font-medium text-[var(--risk)]">{error}</span>}
    </label>
  );
}
