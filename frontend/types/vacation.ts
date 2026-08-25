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
}

export interface VacationModePayload {
  vacation_start: string;
  vacation_end: string;
  plants: VacationPlantInput[];
  risk_level: VacationRiskLevel;
  additional_notes: string | null;
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
