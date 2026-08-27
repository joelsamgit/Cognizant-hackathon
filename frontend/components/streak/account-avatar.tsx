"use client";

import { useState } from "react";
import { Fire, Sparkle } from "@phosphor-icons/react";

import { PlantAvatar } from "@/components/streak/plant-avatar";
import type { UserProfile } from "@/types/user";

export function AccountAvatar({ user }: { user: UserProfile }) {
  const [open, setOpen] = useState(false);
  const stage = user.account_growth_stage ?? 1;
  const mood = user.account_mood ?? "happy";

  return (
    <div className="fixed bottom-10 right-10 z-50">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="group flex size-[5.25rem] items-center justify-center rounded-full border border-[color-mix(in_srgb,var(--accent)_35%,var(--line))] bg-[var(--accent-soft)] shadow-[0_8px_26px_rgba(31,96,61,0.16)] transition-transform duration-200 hover:scale-105 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
        aria-label="Open your growth avatar"
        aria-expanded={open}
      >
        <PlantAvatar stage={stage} mood={mood} size={66} />
      </button>
      {open && (
        <div className="absolute bottom-[calc(100%+0.75rem)] right-0 w-72 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-4 text-left shadow-[var(--shadow)]">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--accent)]">Your garden companion</p>
          <div className="mt-2 flex justify-center rounded-xl bg-[var(--page-muted)] py-2">
            <PlantAvatar stage={stage} mood={mood} size={108} />
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-center">
            <Stat icon={<Fire size={15} weight="fill" />} value={user.account_current_streak ?? 0} label="week streak" />
            <Stat icon={<Sparkle size={15} weight="fill" />} value={user.account_xp ?? 0} label="XP" />
          </div>
          <p className="mt-3 text-xs leading-5 text-[var(--text-muted)]">
            Water at least 70% of your garden each week to grow the streak. One plant alone never advances it.
          </p>
        </div>
      )}
    </div>
  );
}

function Stat({ icon, value, label }: { icon: React.ReactNode; value: number; label: string }) {
  return <div className="rounded-xl bg-[var(--page-muted)] p-2 text-[var(--text)]"><span className="mx-auto flex w-fit items-center gap-1 text-[var(--accent)]">{icon}<b>{value}</b></span><span className="mt-1 block text-[10px] font-semibold text-[var(--text-soft)]">{label}</span></div>;
}
