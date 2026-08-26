import { request } from "./plants";
import type { CareEvent, CareEventPayload } from "../types/care";


export function getCareEvents(plantId: number): Promise<CareEvent[]> {
  return request<CareEvent[]>(`/plants/${plantId}/events`);
}

export function createCareEvent(plantId: number, payload: CareEventPayload): Promise<CareEvent> {
  return request<CareEvent>(`/plants/${plantId}/events`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
