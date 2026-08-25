import type { VacationModePayload, VacationModeResult } from "../types/vacation";
import { request } from "./plants";

export function createVacationPlan(payload: VacationModePayload): Promise<VacationModeResult> {
  return request<VacationModeResult>("/vacation-mode", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
