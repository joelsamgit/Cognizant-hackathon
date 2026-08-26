"use client";

import type { SeasonOverride } from "@/types/plant";


export function SeasonSimulator({ value, onChange }: { value?: SeasonOverride; onChange: (value?: SeasonOverride) => void }) {
  if (process.env.NODE_ENV === "production") return null;
  return (
    <label className="fixed bottom-4 left-4 z-40 rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] p-3 text-xs font-bold text-[var(--text-muted)] shadow-[var(--shadow)]">
      Demo season
      <select
        value={value ?? ""}
        onChange={(event) => {
          const season = (event.target.value || undefined) as SeasonOverride | undefined;
          if (season) localStorage.setItem("plant-guardian:season-simulator", season);
          else localStorage.removeItem("plant-guardian:season-simulator");
          onChange(season);
        }}
        className="mt-1 block rounded-lg border border-[var(--line)] bg-[var(--surface)] px-2 py-1.5 text-[var(--text)]"
      >
        <option value="">Calendar</option>
        <option value="summer">Summer</option>
        <option value="monsoon">Monsoon</option>
        <option value="post-monsoon">Post-monsoon</option>
        <option value="winter">Winter</option>
      </select>
    </label>
  );
}
