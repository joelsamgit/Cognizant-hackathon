
interface XpBarProps {
  xp: number;
  stage: 1 | 2 | 3 | 4 | 5;
}

const thresholds = [0, 20, 60, 120, 200];

export function XpBar({ xp, stage }: XpBarProps) {
  const current = thresholds[stage - 1];
  const next = thresholds[stage] ?? thresholds[4];
  const remaining = Math.max(0, next - xp);
  const progress = stage === 5 ? 100 : Math.min(100, ((xp - current) / (next - current)) * 100);

  return (
    <div className="mt-3">
      <div className="mb-1.5 flex items-center justify-between gap-3 text-[10px] font-bold text-[var(--text-soft)]">
        <span>{xp} XP</span>
        <span>{stage === 5 ? "Peak growth" : `next stage in ${remaining}`}</span>
      </div>
      <div
        className="h-1.5 overflow-hidden rounded-full bg-[var(--line)]"
        role="progressbar"
        aria-label="Growth stage progress"
        aria-valuemin={current}
        aria-valuemax={next}
        aria-valuenow={Math.min(xp, next)}
      >
        <div className="h-full rounded-full bg-[var(--accent)] transition-[width] duration-500" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}
