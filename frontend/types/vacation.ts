export type VacationRiskLevel = "low" | "medium" | "high";

export interface VacationPlantInput {
  plant_name: string;
  species: string;
  location: string;
  specific_spot: string;
  frequency_days: number;
  amount_ml: number;
  last_watered: string;
  notes: string | null;
  base_frequency_days: number;
  pet_safety: "safe" | "mild" | "toxic" | null;
  toxic_cats: boolean | null;
  toxic_dogs: boolean | null;
  placement_tip: string | null;
}

export interface VacationModePayload {
  vacation_start: string;
  vacation_end: string;
  plants: VacationPlantInput[];
  risk_level: VacationRiskLevel;
  additional_notes: string | null;
  season: string | null;
  season_factor: number | null;
}

export interface VacationScheduleEntry {
  plant_name: string;
  species: string;
  location: string;
  specific_spot: string;
  frequency_days: number;
  amount_ml: number;
  last_watered: string;
  notes: string | null;
  base_frequency_days: number | null;
  pet_safety: "safe" | "mild" | "toxic" | null;
  toxic_cats: boolean | null;
  toxic_dogs: boolean | null;
  placement_tip: string | null;
}

export interface VacationModeResult {
  vacation_id: string;
  vacation_start: string;
  vacation_end: string;
  plant_count: number;
  risk_level: VacationRiskLevel;
  watering_schedule: VacationScheduleEntry[];
  caretaker_message: string | null;
  created_at: string;
}
