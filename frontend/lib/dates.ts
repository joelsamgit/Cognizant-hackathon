export function formatLastWatered(days: number): string {
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

export function formatNextWatering(daysUntilDue: number): string {
  if (daysUntilDue > 1) return `In ${daysUntilDue} days`;
  if (daysUntilDue === 1) return "Tomorrow";
  if (daysUntilDue === 0) return "Due today";

  const overdue = Math.abs(daysUntilDue);
  return `${overdue} ${overdue === 1 ? "day" : "days"} overdue`;
}

export function toDateTimeLocal(iso?: string): string {
  const date = iso ? new Date(iso) : new Date();
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60_000);
  return local.toISOString().slice(0, 16);
}

export function toUtcIso(localDateTime: string): string {
  return new Date(localDateTime).toISOString();
}

