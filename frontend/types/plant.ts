export const sunlightOptions = ["Direct Sun", "Indirect Light", "Low Light"] as const;

export type Sunlight = (typeof sunlightOptions)[number];

export type PlantStatus = "Healthy" | "Needs Water Soon" | "Overdue / High Risk";

export interface Plant {
  id: number;
  nickname: string;
  species: string;
  room: string;
  sunlight: Sunlight;
  watering_frequency: number;
  last_watered: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  days_since_watered: number;
  days_until_due: number;
  risk_score: number;
  status: PlantStatus;
}

export interface PlantPayload {
  nickname: string;
  species: string;
  room: string;
  sunlight: Sunlight;
  watering_frequency: number;
  last_watered: string;
  notes: string | null;
}

export type PlantSort = "risk-desc" | "risk-asc" | "recent" | "name";

