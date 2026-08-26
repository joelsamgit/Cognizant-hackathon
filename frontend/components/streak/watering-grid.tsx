import type { WateringHistoryDay } from "@/types/plant";


export function WateringGrid({ history }: { history: WateringHistoryDay[] }) {
  return (
    <div className="mt-4 rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--text-soft)]">Last 28 days</p>
        <div className="flex gap-2 text-[9px] font-semibold text-[var(--text-soft)]" aria-label="History legend">
          <span className="flex items-center gap-1"><i className="size-1.5 rounded-full bg-[var(--healthy)]" />Watered</span>
          <span className="flex items-center gap-1"><i className="size-1.5 rounded-full bg-[var(--risk)]" />Overdue</span>
        </div>
      </div>
      <div className="mt-2 grid grid-cols-14 gap-1.5" aria-label="Watering history heatmap">
        {history.map((day) => (
          <span
            key={day.date}
            title={`${day.date}: ${day.status}`}
            className={`aspect-square rounded-full ${
              day.status === "watered"
                ? "bg-[var(--healthy)]"
                : day.status === "overdue"
                  ? "bg-[var(--risk)]"
                  : "bg-[var(--line)]"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
