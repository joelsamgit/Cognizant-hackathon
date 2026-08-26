"use client";

import { CloudRain, Leaf, Snowflake, Sun, X } from "@phosphor-icons/react";
import { useState } from "react";


const copy: Record<string, { icon: typeof Leaf; title: string; body: string }> = {
  Winter: { icon: Snowflake, title: "Winter mode", body: "Your plants are drinking about 40% less." },
  Summer: { icon: Sun, title: "Summer mode", body: "Shorter watering intervals help with faster evaporation." },
  Monsoon: { icon: CloudRain, title: "Monsoon mode", body: "Water less often and watch for fungus gnats and root rot." },
  "Post-monsoon": { icon: Leaf, title: "Post-monsoon mode", body: "Your configured watering rhythm is in effect." },
};

export function SeasonBanner({ season }: { season: string }) {
  const storageKey = `plant-guardian:season-dismissed:${season}`;
  const [visible, setVisible] = useState(
    () => typeof window === "undefined" || localStorage.getItem(storageKey) !== "true",
  );
  const message = copy[season] ?? copy["Post-monsoon"];
  if (!visible) return null;

  return (
    <aside className="flex items-center gap-3 rounded-2xl border border-[color-mix(in_srgb,var(--accent)_25%,var(--line))] bg-[var(--accent-soft)] px-4 py-3" aria-label={`${season} watering mode`}>
      <message.icon size={24} weight="duotone" className="shrink-0 text-[var(--healthy)]" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold text-[var(--text)]">{message.title}</p>
        <p className="text-xs leading-5 text-[var(--text-muted)]">{message.body}</p>
      </div>
      <button
        type="button"
        onClick={() => {
          localStorage.setItem(storageKey, "true");
          setVisible(false);
        }}
        className="rounded-full p-2 text-[var(--text-muted)] hover:bg-[var(--surface)] hover:text-[var(--text)]"
        aria-label={`Dismiss ${season} notice`}
      >
        <X size={16} aria-hidden="true" />
      </button>
    </aside>
  );
}
