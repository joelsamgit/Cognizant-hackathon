import { Leaf, Plus } from "@phosphor-icons/react/dist/ssr";

import { Button } from "@/components/ui/button";


interface DashboardHeaderProps {
  onAdd: () => void;
}

export function DashboardHeader({ onAdd }: DashboardHeaderProps) {
  return (
    <header className="flex flex-col gap-6 border-b border-[var(--line)] pb-7 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex items-start gap-4">
        <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--surface-strong)] text-[var(--surface)] shadow-[var(--shadow)] dark:text-[#122018]">
          <Leaf size={25} weight="fill" aria-hidden="true" />
        </div>
        <div>
          <p className="mb-1 text-sm font-semibold text-[var(--accent)]">Your living collection</p>
          <h1 className="text-3xl font-bold tracking-[-0.04em] text-[var(--text)] sm:text-4xl">
            Plant Guardian
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--text-muted)] sm:text-base">
            See what needs care today, before a thirsty plant has to ask.
          </p>
        </div>
      </div>
      <Button onClick={onAdd} className="w-full sm:w-auto">
        <Plus size={18} weight="bold" aria-hidden="true" />
        Add Plant
      </Button>
    </header>
  );
}

