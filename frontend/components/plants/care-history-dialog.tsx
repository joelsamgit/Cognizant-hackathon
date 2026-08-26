"use client";

import { useEffect, useRef, useState } from "react";
import { ClockCounterClockwise, SpinnerGap, X } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import { toDateTimeLocal, toUtcIso } from "@/lib/dates";
import { createCareEvent, getCareEvents } from "@/services/care";
import { ApiError } from "@/services/plants";
import type { CareAction, CareEvent, CareResult } from "@/types/care";
import { careActions } from "@/types/care";
import type { Plant } from "@/types/plant";


interface CareHistoryDialogProps {
  plant: Plant;
  onClose: () => void;
  onRecorded: (event: CareEvent) => void;
  onNotify: (message: string, tone?: "success" | "error") => void;
}

const actionLabels: Record<CareAction, string> = {
  water: "Watered",
  check: "Soil check",
  fertilize: "Fertilized",
  mist: "Misted",
  prune: "Pruned",
  repot: "Repotted",
};

const resultLabels: Record<CareResult, string> = {
  watered: "Watered",
  still_damp: "Still damp",
  completed: "Completed",
  skipped: "Skipped",
};

function defaultResult(action: CareAction): CareResult {
  if (action === "water") return "watered";
  return "completed";
}

function messageFrom(error: unknown): string {
  return error instanceof ApiError ? error.message : "Care history could not be updated.";
}

function formatEventDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

const inputClass =
  "min-h-11 w-full rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] px-3.5 py-2.5 text-sm text-[var(--text)] focus:border-[var(--accent)] focus:outline-none";

export function CareHistoryDialog({
  plant,
  onClose,
  onRecorded,
  onNotify,
}: CareHistoryDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [events, setEvents] = useState<CareEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState<CareAction>("check");
  const [result, setResult] = useState<CareResult>("completed");
  const [occurredAt, setOccurredAt] = useState(() => toDateTimeLocal());
  const [amount, setAmount] = useState("");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    dialog.showModal();
    return () => dialog.close();
  }, []);

  useEffect(() => {
    let active = true;
    getCareEvents(plant.id)
      .then((records) => {
        if (active) setEvents(records);
      })
      .catch((nextError: unknown) => {
        if (active) setError(messageFrom(nextError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [plant.id]);

  function updateAction(nextAction: CareAction) {
    setAction(nextAction);
    setResult(defaultResult(nextAction));
    if (!["water", "fertilize", "mist"].includes(nextAction)) setAmount("");
  }

  async function recordCare(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const numericAmount = amount === "" ? null : Number(amount);
    if (numericAmount !== null && (!Number.isInteger(numericAmount) || numericAmount < 0 || numericAmount > 10000)) {
      setError("Amount must be a whole number from 0 to 10,000 ml.");
      return;
    }

    setSaving(true);
    try {
      const created = await createCareEvent(plant.id, {
        action,
        occurred_at: toUtcIso(occurredAt),
        amount_ml: numericAmount,
        result,
        notes: notes.trim() || null,
      });
      setEvents((current) => [created, ...current]);
      setOccurredAt(toDateTimeLocal());
      setAmount("");
      setNotes("");
      onRecorded(created);
      onNotify(`${actionLabels[action]} care recorded for ${plant.nickname}`);
    } catch (nextError) {
      const message = messageFrom(nextError);
      setError(message);
      onNotify(message, "error");
    } finally {
      setSaving(false);
    }
  }

  const showAmount = ["water", "fertilize", "mist"].includes(action);

  return (
    <dialog
      ref={dialogRef}
      onCancel={(event) => {
        if (saving) event.preventDefault();
        else onClose();
      }}
      onClose={onClose}
      className="m-auto max-h-[calc(100dvh-2rem)] w-[min(48rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-0 text-[var(--text)] shadow-[var(--shadow)]"
      aria-labelledby="care-history-title"
    >
      <div className="flex items-start justify-between border-b border-[var(--line)] px-5 py-5 sm:px-6">
        <div>
          <h2 id="care-history-title" className="flex items-center gap-2 text-xl font-bold tracking-[-0.025em]">
            <ClockCounterClockwise size={22} className="text-[var(--accent)]" aria-hidden="true" />
            {plant.nickname}&apos;s care history
          </h2>
          <p className="mt-1 text-sm text-[var(--text-muted)]">Record care and keep a chronological plant journal.</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          disabled={saving}
          className="rounded-full p-2 text-[var(--text-muted)] hover:bg-[var(--page-muted)] hover:text-[var(--text)]"
          aria-label="Close care history"
        >
          <X size={20} aria-hidden="true" />
        </button>
      </div>

      <div className="grid max-h-[calc(100dvh-9rem)] overflow-y-auto lg:grid-cols-[1fr_1.05fr]">
        <form onSubmit={recordCare} className="border-b border-[var(--line)] p-5 sm:p-6 lg:border-b-0 lg:border-r">
          <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--text-muted)]">Record care</h3>
          {error && <p className="mt-4 rounded-xl bg-[var(--risk-soft)] px-4 py-3 text-sm text-[var(--risk)]" role="alert">{error}</p>}

          <div className="mt-4 grid gap-4">
            <label className="grid gap-2 text-sm font-semibold">
              Action
              <select value={action} onChange={(event) => updateAction(event.target.value as CareAction)} className={inputClass}>
                {careActions.map((value) => <option key={value} value={value}>{actionLabels[value]}</option>)}
              </select>
            </label>

            <label className="grid gap-2 text-sm font-semibold">
              Result
              <select value={result} onChange={(event) => setResult(event.target.value as CareResult)} className={inputClass}>
                {action === "water" && <option value="watered">Watered</option>}
                {action !== "water" && <option value="completed">Completed</option>}
                {action === "check" && <option value="still_damp">Still damp</option>}
                <option value="skipped">Skipped</option>
              </select>
            </label>

            <label className="grid gap-2 text-sm font-semibold">
              When
              <input
                type="datetime-local"
                value={occurredAt}
                max={toDateTimeLocal()}
                onChange={(event) => setOccurredAt(event.target.value)}
                className={inputClass}
                required
              />
            </label>

            {showAmount && (
              <label className="grid gap-2 text-sm font-semibold">
                Amount in ml <span className="text-xs font-normal text-[var(--text-soft)]">Optional</span>
                <input
                  type="number"
                  min={0}
                  max={10000}
                  step={10}
                  value={amount}
                  onChange={(event) => setAmount(event.target.value)}
                  className={inputClass}
                />
              </label>
            )}

            <label className="grid gap-2 text-sm font-semibold">
              Notes <span className="text-xs font-normal text-[var(--text-soft)]">Optional</span>
              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                className={`${inputClass} min-h-24 resize-y`}
                maxLength={2000}
                placeholder="What did you notice?"
              />
            </label>

            <Button type="submit" disabled={saving}>
              {saving && <SpinnerGap size={17} className="animate-spin" aria-hidden="true" />}
              {saving ? "Recording" : "Record care"}
            </Button>
          </div>
        </form>

        <section aria-label="Care timeline" className="p-5 sm:p-6">
          <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--text-muted)]">Timeline</h3>
          {loading ? (
            <div className="mt-8 flex items-center justify-center gap-2 text-sm text-[var(--text-muted)]">
              <SpinnerGap size={18} className="animate-spin" aria-hidden="true" /> Loading history
            </div>
          ) : events.length === 0 ? (
            <p className="mt-8 text-center text-sm leading-6 text-[var(--text-muted)]">No care has been recorded yet.</p>
          ) : (
            <ol className="mt-5 space-y-3">
              {events.map((careEvent) => (
                <li key={careEvent.id} className="rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-bold text-[var(--text)]">{actionLabels[careEvent.action]}</p>
                      <p className="mt-1 text-xs text-[var(--text-muted)]">{formatEventDate(careEvent.occurred_at)}</p>
                    </div>
                    <span className="rounded-full bg-[var(--page-muted)] px-2.5 py-1 text-[11px] font-semibold text-[var(--text-muted)]">
                      {resultLabels[careEvent.result]}
                    </span>
                  </div>
                  {careEvent.amount_ml !== null && <p className="mt-3 text-sm text-[var(--text-muted)]">{careEvent.amount_ml} ml</p>}
                  {careEvent.notes && <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{careEvent.notes}</p>}
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>
    </dialog>
  );
}
