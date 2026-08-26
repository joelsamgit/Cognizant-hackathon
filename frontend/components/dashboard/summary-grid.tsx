import { ChartBar, Drop, Leaf, Plant as PlantIcon, WarningCircle } from "@phosphor-icons/react/dist/ssr";

import type { Plant } from "@/types/plant";
import type { UserProfile } from "@/types/user";


interface SummaryGridProps {
  plants: Plant[];
  user: UserProfile;
}

const metrics = [
  {
    key: "healthy",
    label: "Healthy",
    Icon: Leaf,
    className: "text-[var(--healthy)]",
  },
  {
    key: "soon",
    label: "Water soon",
    Icon: Drop,
    className: "text-[var(--soon)]",
  },
  {
    key: "overdue",
    label: "High risk",
    Icon: WarningCircle,
    className: "text-[var(--risk)]",
  },
] as const;

export function SummaryGrid({ plants, user }: SummaryGridProps) {
  const values = {
    healthy: plants.filter((plant) => plant.status === "Healthy").length,
    soon: plants.filter((plant) => plant.status === "Needs Water Soon").length,
    overdue: plants.filter((plant) => plant.status === "Overdue / High Risk").length,
  };

  const attention = values.soon + values.overdue;
  const averageConsistency = plants.length
    ? Math.round(plants.reduce((total, plant) => total + plant.consistency_pct, 0) / plants.length)
    : 0;
  const unsafeForCats = plants.filter((plant) => plant.toxic_cats).length;

  return (
    <section aria-label="Garden summary" className="grid grid-cols-2 gap-3 lg:grid-cols-[1.35fr_1fr_1fr_1fr_1fr]">
      <div className="col-span-2 flex min-h-32 items-center justify-between overflow-hidden rounded-2xl bg-[var(--surface-strong)] p-5 text-[var(--page)] shadow-[var(--shadow)] lg:col-span-1">
        <div>
          <p className="text-sm font-semibold opacity-75">Total plants</p>
          <p className="mt-2 text-4xl font-bold tracking-[-0.04em] tabular-nums">{plants.length}</p>
          <p className="mt-1 text-xs font-medium opacity-70">
            {user.account_current_streak ? `🔥 ${user.account_current_streak}-week garden streak` : "Water 70% of your garden to start a streak"}
          </p>
          {unsafeForCats > 0 && (
            <span className="mt-2 inline-flex rounded-full bg-[var(--soon-soft)] px-2 py-1 text-[10px] font-bold text-[var(--soon)]">
              {unsafeForCats} unsafe for cats
            </span>
          )}
        </div>
        <PlantIcon size={44} weight="duotone" className="opacity-75" aria-hidden="true" />
      </div>

      {metrics.map(({ key, label, Icon, className }) => (
        <div
          key={key}
          className="flex min-h-32 flex-col justify-between rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-4 shadow-[0_12px_32px_rgba(31,96,61,0.045)] sm:p-5"
        >
          <Icon size={22} weight="duotone" className={className} aria-hidden="true" />
          <div>
            <p className="text-3xl font-bold tracking-[-0.04em] tabular-nums text-[var(--text)]">
              {values[key]}
            </p>
            <p className="mt-1 text-xs font-semibold text-[var(--text-muted)] sm:text-sm">{label}</p>
          </div>
        </div>
      ))}
      <div className="flex min-h-32 flex-col justify-between rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-4 shadow-[0_12px_32px_rgba(31,96,61,0.045)] sm:p-5">
        <ChartBar size={22} weight="duotone" className="text-[var(--accent)]" aria-hidden="true" />
        <div>
          <p className="text-3xl font-bold tracking-[-0.04em] tabular-nums text-[var(--text)]">{averageConsistency}%</p>
          <p className="mt-1 text-xs font-semibold text-[var(--text-muted)] sm:text-sm">Avg on-time</p>
          <p className="sr-only">{attention} plants need attention</p>
        </div>
      </div>
    </section>
  );
}
