export const careActions = ["water", "check", "fertilize", "mist", "prune", "repot"] as const;

export type CareAction = (typeof careActions)[number];
export type CareResult = "watered" | "still_damp" | "completed" | "skipped";

export interface CareEvent {
  id: number;
  plant_id: number;
  action: CareAction;
  occurred_at: string;
  amount_ml: number | null;
  result: CareResult;
  notes: string | null;
  created_at: string;
}

export interface CareEventPayload {
  action: CareAction;
  occurred_at: string;
  amount_ml: number | null;
  result: CareResult;
  notes: string | null;
}
