"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AirplaneTakeoff, CheckCircle, Copy, SpinnerGap, X } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import { toDateTimeLocal, toUtcIso } from "@/lib/dates";
import { ApiError } from "@/services/plants";
import { createVacationPlan } from "@/services/vacation";
import type { VacationModeResult, VacationRiskLevel } from "@/types/vacation";
import type { Plant } from "@/types/plant";


interface VacationDialogProps {
  plants: Plant[];
  onClose: () => void;
  onNotify: (message: string, tone?: "success" | "error") => void;
}

interface Selection {
  id: number;
  selected: boolean;
  amount_ml: string;
}

const DEFAULT_AMOUNT_ML = 250;
const MAX_FREQUENCY_DAYS = 30;

const riskLabels: Record<VacationRiskLevel, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

function deriveRisk(plants: Plant[]): VacationRiskLevel {
  if (plants.some((plant) => plant.status === "Overdue / High Risk")) return "high";
  if (plants.some((plant) => plant.status === "Needs Water Soon")) return "medium";
  return "low";
}

export function VacationDialog({ plants, onClose, onNotify }: VacationDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [start, setStart] = useState(() => toDateTimeLocal());
  const [end, setEnd] = useState("");
  const [notes, setNotes] = useState("");
  const [selections, setSelections] = useState<Selection[]>(() =>
    plants.map((plant) => ({ id: plant.id, selected: true, amount_ml: String(DEFAULT_AMOUNT_ML) })),
  );
  const [riskOverride, setRiskOverride] = useState<VacationRiskLevel | "auto">("auto");
  const [generating, setGenerating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [result, setResult] = useState<VacationModeResult | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    dialog.showModal();
    return () => dialog.close();
  }, []);

  const byId = useMemo(() => new Map(plants.map((plant) => [plant.id, plant])), [plants]);
  const chosenPlants = useMemo(
    () => selections.filter((entry) => entry.selected && byId.has(entry.id)).map((entry) => byId.get(entry.id)!),
    [selections, byId],
  );
  const derivedRisk = useMemo(() => deriveRisk(chosenPlants), [chosenPlants]);
  const activeRisk: VacationRiskLevel = riskOverride === "auto" ? derivedRisk : riskOverride;
  const unsafePlants = chosenPlants.filter((plant) => plant.pet_safety === "mild" || plant.pet_safety === "toxic");
  const seasonAdjusted = chosenPlants.some(
    (plant) => plant.effective_watering_frequency !== plant.base_watering_frequency,
  );

  function updateSelection(id: number, patch: Partial<Selection>) {
    setSelections((current) =>
      current.map((entry) => (entry.id === id ? { ...entry, ...patch } : entry)),
    );
    setCopied(false);
  }

  function toggleAll(selected: boolean) {
    setSelections((current) => current.map((entry) => ({ ...entry, selected })));
  }

  async function handleGenerate() {
    setFormError(null);

    if (!start || !end) {
      setFormError("Choose both the departure and return dates.");
      return;
    }
    if (new Date(end).getTime() <= new Date(start).getTime()) {
      setFormError("The return date must be after the departure date.");
      return;
    }
    if (chosenPlants.length === 0) {
      setFormError("Select at least one plant to cover.");
      return;
    }
    for (const entry of selections.filter((item) => item.selected)) {
      const amount = Number(entry.amount_ml);
      if (!Number.isInteger(amount) || amount < 0 || amount > 10000) {
        setFormError(`Water amount for ${byId.get(entry.id)?.nickname ?? "a plant"} must be a whole number from 0 to 10,000 ml.`);
        return;
      }
    }

    setGenerating(true);
    try {
      const plan = await createVacationPlan({
        vacation_start: toUtcIso(start),
        vacation_end: toUtcIso(end),
        plants: chosenPlants.map((plant) => ({
          plant_name: plant.nickname,
          species: plant.species,
          location: plant.room,
          specific_spot: plant.sunlight,
          frequency_days: Math.min(plant.effective_watering_frequency, MAX_FREQUENCY_DAYS),
          base_frequency_days: plant.base_watering_frequency,
          amount_ml: Math.round(
            Number(selections.find((entry) => entry.id === plant.id)?.amount_ml ?? DEFAULT_AMOUNT_ML)
            * Math.max(0.1, 2 - plant.season_factor),
          ),
          last_watered: plant.last_watered,
          notes: plant.notes,
          pet_safety: plant.pet_safety,
          toxic_cats: plant.toxic_cats,
          toxic_dogs: plant.toxic_dogs,
          placement_tip: plant.placement_tip,
        })),
        risk_level: activeRisk,
        additional_notes: notes.trim() || null,
        season: chosenPlants[0]?.season ?? null,
        season_factor: chosenPlants[0]?.season_factor ?? null,
      });
      setResult(plan);
      onNotify(`Vacation plan ${plan.vacation_id} is ready`);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Could not create the vacation plan. Please try again.");
    } finally {
      setGenerating(false);
    }
  }

  async function copyMessage() {
    if (!result?.caretaker_message) return;
    try {
      await navigator.clipboard.writeText(result.caretaker_message);
      setCopied(true);
    } catch {
      onNotify("Copying failed. Select the text manually.", "error");
    }
  }

  const busy = generating;

  return (
    <dialog
      ref={dialogRef}
      onCancel={(event) => {
        if (busy) event.preventDefault();
        else onClose();
      }}
      onClose={onClose}
      className="m-auto max-h-[calc(100dvh-2rem)] w-[min(46rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-0 text-[var(--text)] shadow-[var(--shadow)]"
      aria-labelledby="vacation-dialog-title"
    >
      <div className="flex items-start justify-between border-b border-[var(--line)] px-5 py-5 sm:px-6">
        <div>
          <h2 id="vacation-dialog-title" className="flex items-center gap-2 text-xl font-bold tracking-[-0.025em]">
            <AirplaneTakeoff size={22} weight="fill" className="text-[var(--accent)]" aria-hidden="true" />
            Vacation Mode
          </h2>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Generate a caretaker briefing for your plants while you are away.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          disabled={busy}
          className="rounded-full p-2 text-[var(--text-muted)] transition-colors hover:bg-[var(--page-muted)] hover:text-[var(--text)] disabled:opacity-50"
          aria-label="Close vacation mode"
        >
          <X size={20} aria-hidden="true" />
        </button>
      </div>

      <div className="max-h-[calc(100dvh-13rem)] overflow-y-auto px-5 py-5 sm:px-6">
        {formError && (
          <div role="alert" className="mb-5 rounded-xl bg-[var(--risk-soft)] px-4 py-3 text-sm font-medium text-[var(--risk)]">
            {formError}
          </div>
        )}

        {result ? (
          <div className="space-y-5">
            <div className="flex items-start gap-3 rounded-xl bg-[var(--healthy-soft)] px-4 py-3">
              <CheckCircle size={20} weight="fill" className="mt-0.5 shrink-0 text-[var(--healthy)]" aria-hidden="true" />
              <div className="text-sm">
                <p className="font-semibold text-[var(--text)]">Plan {result.vacation_id} covers {result.plant_count} {result.plant_count === 1 ? "plant" : "plants"} at {riskLabels[result.risk_level].toLowerCase()} risk.</p>
                {result.caretaker_message ? (
                  <p className="mt-1 text-[var(--text-muted)]">Share the caretaker message below with whoever waters your plants.</p>
                ) : (
                  <p className="mt-1 text-[var(--text-muted)]">
                    The AI assistant is unreachable, so no caretaker message was generated. The watering schedule above still applies.
                  </p>
                )}
              </div>
            </div>

            {result.caretaker_message && (
              <section aria-label="Caretaker message" className="rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] p-4">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--text-muted)]">Caretaker message</h3>
                  <Button variant="secondary" size="sm" onClick={() => void copyMessage()}>
                    <Copy size={16} aria-hidden="true" />
                    {copied ? "Copied" : "Copy"}
                  </Button>
                </div>
                <p className="whitespace-pre-line text-sm leading-6 text-[var(--text)]">{result.caretaker_message}</p>
              </section>
            )}

            <section aria-label="Watering schedule" className="overflow-hidden rounded-xl border border-[var(--line)]">
              <table className="w-full text-left text-sm">
                <thead className="bg-[var(--page-muted)] text-xs uppercase tracking-wide text-[var(--text-muted)]">
                  <tr>
                    <th className="px-4 py-2.5 font-semibold">Plant</th>
                    <th className="px-4 py-2.5 font-semibold">Every</th>
                    <th className="px-4 py-2.5 font-semibold">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {result.watering_schedule.map((entry) => (
                    <tr key={entry.plant_name} className="border-t border-[var(--line)]">
                      <td className="px-4 py-2.5">
                        <span className="font-medium text-[var(--text)]">{entry.plant_name}</span>
                        <span className="block text-xs text-[var(--text-muted)]">{entry.location}</span>
                      </td>
                      <td className="px-4 py-2.5 text-[var(--text-muted)]">{entry.frequency_days} days</td>
                      <td className="px-4 py-2.5 text-[var(--text-muted)]">{entry.amount_ml} ml</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid gap-5 sm:grid-cols-2">
              <label className="grid gap-2 text-sm font-semibold text-[var(--text)]">
                <span>Leaving on</span>
                <input
                  autoFocus
                  type="datetime-local"
                  value={start}
                  max={toDateTimeLocal()}
                  onChange={(event) => setStart(event.target.value)}
                  className={inputClass}
                />
              </label>
              <label className="grid gap-2 text-sm font-semibold text-[var(--text)]">
                <span>Back on</span>
                <input
                  type="datetime-local"
                  value={end}
                  onChange={(event) => setEnd(event.target.value)}
                  className={inputClass}
                />
              </label>
            </div>

            <section aria-label="Plants to cover" className="rounded-xl border border-[var(--line)]">
              <div className="flex items-center justify-between border-b border-[var(--line)] bg-[var(--page-muted)] px-4 py-2.5">
                <h3 className="text-sm font-bold text-[var(--text)]">Plants to cover ({chosenPlants.length})</h3>
                <div className="flex gap-2 text-xs font-semibold text-[var(--accent)]">
                  <button type="button" onClick={() => toggleAll(true)} className="hover:underline">All</button>
                  <button type="button" onClick={() => toggleAll(false)} className="hover:underline">None</button>
                </div>
              </div>
              <ul className="divide-y divide-[var(--line)]">
                {plants.map((plant) => {
                  const entry = selections.find((item) => item.id === plant.id);
                  if (!entry) return null;
                  return (
                    <li key={plant.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
                      <label className="flex min-w-0 flex-1 items-center gap-3">
                        <input
                          type="checkbox"
                          checked={entry.selected}
                          onChange={(event) => updateSelection(plant.id, { selected: event.target.checked })}
                          className="size-4 shrink-0 accent-[var(--accent)]"
                        />
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium text-[var(--text)]">{plant.nickname}</span>
                          <span className="block truncate text-xs text-[var(--text-muted)]">
                            {plant.room} · every {Math.min(plant.effective_watering_frequency, MAX_FREQUENCY_DAYS)} days
                          </span>
                        </span>
                      </label>
                      <label className="flex items-center gap-2 text-xs font-medium text-[var(--text-muted)]">
                        Water
                        <input
                          type="number"
                          min={0}
                          max={10000}
                          step={10}
                          value={entry.amount_ml}
                          onChange={(event) => updateSelection(plant.id, { amount_ml: event.target.value })}
                          disabled={!entry.selected}
                          className={`${inputClass} w-24 !min-h-9 !py-1.5`}
                          aria-label={`Water amount in ml for ${plant.nickname}`}
                        />
                        ml
                      </label>
                    </li>
                  );
                })}
              </ul>
            </section>

            {unsafePlants.length > 0 && (
              <div className="rounded-xl bg-[var(--soon-soft)] px-4 py-3 text-sm text-[var(--soon)]" role="note">
                <strong>Pet handling notice:</strong> wear gloves and wash hands after handling {unsafePlants.map((plant) => plant.nickname).join(", ")}.
              </div>
            )}

            {seasonAdjusted && (
              <p className="text-sm font-semibold text-[var(--accent)]">
                {chosenPlants[0]?.season} adjustments applied to intervals and water amounts.
              </p>
            )}

            <div className="grid gap-5 sm:grid-cols-2">
              <label className="grid gap-2 text-sm font-semibold text-[var(--text)]">
                <span>Risk level</span>
                <select
                  value={riskOverride}
                  onChange={(event) => setRiskOverride(event.target.value as VacationRiskLevel | "auto")}
                  className={inputClass}
                >
                  <option value="auto">Auto ({riskLabels[derivedRisk]})</option>
                  {Object.entries(riskLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
              <label className="grid gap-2 text-sm font-semibold text-[var(--text)]">
                <span>Extra caretaker notes</span>
                <input
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  maxLength={1000}
                  placeholder="e.g. Key is with the neighbour"
                  className={inputClass}
                />
              </label>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-col-reverse gap-2 border-t border-[var(--line)] bg-[var(--surface-raised)] px-5 py-4 sm:flex-row sm:justify-end sm:px-6">
        {result ? (
          <>
            <Button variant="secondary" onClick={() => setResult(null)} disabled={busy}>
              Edit details
            </Button>
            <Button onClick={onClose}>Done</Button>
          </>
        ) : (
          <>
            <Button variant="secondary" onClick={onClose} disabled={busy}>
              Cancel
            </Button>
            <Button onClick={() => void handleGenerate()} disabled={busy}>
              {busy && <SpinnerGap size={18} className="animate-spin" aria-hidden="true" />}
              {busy ? "Preparing briefing" : `Generate for ${chosenPlants.length} ${chosenPlants.length === 1 ? "plant" : "plants"}`}
            </Button>
          </>
        )}
      </div>
    </dialog>
  );
}

const inputClass =
  "min-h-11 w-full rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] px-3.5 py-2.5 text-sm text-[var(--text)] transition-colors placeholder:text-[var(--text-soft)] hover:border-[var(--line-strong)] focus:border-[var(--accent)] focus:outline-none disabled:opacity-55";
