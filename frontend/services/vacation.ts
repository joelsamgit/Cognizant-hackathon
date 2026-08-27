import type { VacationModePayload, VacationModeResult } from "../types/vacation";
import { request } from "./plants";

export function createVacationPlan(payload: VacationModePayload): Promise<VacationModeResult> {
  return request<VacationModeResult>("/vacation-mode", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getGmailComposeUrl(): string {
  return "https://mail.google.com/mail/u/0/?view=cm&fs=1&tf=1";
}

export function validateVacationWindow(start: string, end: string): string | null {
  if (!start || !end) return "Choose both the departure and return dates.";
  if (new Date(end).getTime() <= new Date(start).getTime()) {
    return "The return date must be after the departure date.";
  }
  return null;
}
