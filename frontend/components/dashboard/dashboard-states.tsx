import { ArrowClockwise, MagnifyingGlass, Plant, Plus, Warning } from "@phosphor-icons/react/dist/ssr";

import { Button } from "@/components/ui/button";


export function DashboardSkeleton() {
  return (
    <div aria-label="Loading plant collection" aria-busy="true" className="space-y-8">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => (
          <div key={index} className="skeleton h-32 rounded-2xl" />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }, (_, index) => (
          <div key={index} className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-5">
            <div className="flex justify-between gap-8">
              <div className="skeleton h-6 w-32 rounded-lg" />
              <div className="skeleton h-7 w-24 rounded-full" />
            </div>
            <div className="skeleton mt-3 h-4 w-24 rounded-lg" />
            <div className="skeleton mt-6 h-28 rounded-2xl" />
            <div className="mt-5 grid grid-cols-2 gap-4">
              <div className="skeleton h-10 rounded-xl" />
              <div className="skeleton h-10 rounded-xl" />
              <div className="skeleton h-10 rounded-xl" />
              <div className="skeleton h-10 rounded-xl" />
            </div>
            <div className="skeleton mt-5 h-11 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function LoadError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <section className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-8 text-center sm:p-12" role="alert">
      <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-[var(--risk-soft)] text-[var(--risk)]">
        <Warning size={24} weight="duotone" aria-hidden="true" />
      </div>
      <h2 className="mt-5 text-xl font-bold tracking-[-0.025em]">Your garden could not be loaded</h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[var(--text-muted)]">{message}</p>
      <Button onClick={onRetry} className="mt-6">
        <ArrowClockwise size={17} aria-hidden="true" />
        Try again
      </Button>
    </section>
  );
}

export function EmptyGarden({ onAdd }: { onAdd: () => void }) {
  return (
    <section className="rounded-2xl border border-dashed border-[var(--line-strong)] bg-[var(--surface)] px-6 py-16 text-center">
      <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-[var(--accent-soft)] text-[var(--accent)]">
        <Plant size={28} weight="duotone" aria-hidden="true" />
      </div>
      <h2 className="mt-5 text-2xl font-bold tracking-[-0.035em]">Your garden is waiting.</h2>
      <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-[var(--text-muted)]">
        Add your first plant to start tracking its care and watering urgency.
      </p>
      <Button onClick={onAdd} className="mt-6">
        <Plus size={18} weight="bold" aria-hidden="true" />
        Add Plant
      </Button>
    </section>
  );
}

export function NoResults({ onClear }: { onClear: () => void }) {
  return (
    <section className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] px-6 py-12 text-center">
      <MagnifyingGlass size={28} className="mx-auto text-[var(--text-soft)]" aria-hidden="true" />
      <h2 className="mt-4 text-lg font-bold">No plants match those filters</h2>
      <p className="mt-2 text-sm text-[var(--text-muted)]">Try another room, nickname, or species.</p>
      <Button variant="secondary" onClick={onClear} className="mt-5">
        Clear filters
      </Button>
    </section>
  );
}

