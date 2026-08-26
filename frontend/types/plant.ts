export const speciesSuggestions = [
  "Holy Basil",
  "Golden Pothos",
  "Curry Tree",
  "Aloe Vera",
  "Areca Palm",
  "Snake Plant",
  "Jade Plant",
  "Spider Plant",
  "India Rubber Tree",
  "Peace Lily",
  "Swiss Cheese Plant",
  "ZZ Plant",
  "Arrowhead Vine",
  "Lucky Bamboo",
  "String of Pearls",
  "Red Aglaonema",
  "Fiddle Leaf Fig",
  "Boston Fern",
  "Rattlesnake Calathea",
  "Ginseng Fig Bonsai",
  "Rose",
  "Arabian Jasmine",
] as const;

export const speciesWateringDefaults: Record<string, number> = {
  "Holy Basil": 2,
  "Golden Pothos": 6,
  "Curry Tree": 3,
  "Aloe Vera": 10,
  "Areca Palm": 5,
  "Snake Plant": 15,
  "Jade Plant": 10,
  "Spider Plant": 5,
  "India Rubber Tree": 7,
  "Peace Lily": 5,
  "Swiss Cheese Plant": 7,
  "ZZ Plant": 18,
  "Arrowhead Vine": 5,
  "Lucky Bamboo": 7,
  "String of Pearls": 10,
  "Red Aglaonema": 7,
  "Fiddle Leaf Fig": 7,
  "Boston Fern": 4,
  "Rattlesnake Calathea": 5,
  "Ginseng Fig Bonsai": 6,
  Rose: 2,
  "Arabian Jasmine": 2,
};

export const sunlightOptions = ["Direct Sun", "Indirect Light", "Low Light"] as const;

export type Sunlight = (typeof sunlightOptions)[number];

export type PlantStatus = "Healthy" | "Needs Water Soon" | "Overdue / High Risk";
export type PlantMood = "happy" | "doubtful" | "sad";
export type PetSafety = "safe" | "mild" | "toxic";
export type PetSafetyFilter = "all" | "safe" | "hide-toxic";
export type SeasonOverride = "summer" | "monsoon" | "post-monsoon" | "winter";

export interface WateringHistoryDay {
  date: string;
  status: "watered" | "overdue" | "ontrack";
}

export interface PlantDetails {
  indian_name: string;
  common_name: string;
  scientific_name: string;
  difficulty: string;
  category: string;
  tagline: string;
  image_url: string | null;
  vibe: string;
  ideal_spot: string;
  name_origin: string;
  cultural_context: string;
  fun_fact: string;
  symbolism: string;
}

export interface PlantCareGuide {
  sunlight: string;
  sunlight_detail: string;
  watering_frequency_days: number;
  water_amount_ml: number;
  watering_method: string;
  pro_tip: string;
  common_mistake: string;
}

export interface Plant {
  id: number;
  nickname: string;
  species: string;
  room: string;
  sunlight: Sunlight;
  watering_frequency: number;
  last_watered: string;
  notes: string | null;
  catalog_key: string | null;
  details: PlantDetails | null;
  care_guide: PlantCareGuide | null;
  created_at: string;
  updated_at: string;
  days_since_watered: number;
  days_until_due: number;
  watering_locked?: boolean;
  next_watering_in_days?: number;
  risk_score: number;
  status: PlantStatus;
  current_streak: number;
  longest_streak: number;
  consistency_pct: number;
  total_waterings: number;
  xp: number;
  growth_stage: 1 | 2 | 3 | 4 | 5;
  mood: PlantMood;
  history: WateringHistoryDay[];
  milestone: string | null;
  pet_safety: PetSafety | null;
  pet_severity: PetSafety | null;
  toxic_cats: boolean | null;
  toxic_dogs: boolean | null;
  placement_tip: string | null;
  season: string;
  base_watering_frequency: number;
  effective_watering_frequency: number;
  season_factor: number;
}

export interface PlantPayload {
  nickname: string;
  species: string;
  room: string;
  sunlight: Sunlight;
  watering_frequency: number;
  last_watered: string;
  notes: string | null;
  catalog_key?: string | null;
  details?: PlantDetails | null;
  care_guide?: PlantCareGuide | null;
}

export type PlantSort = "risk-desc" | "risk-asc" | "recent" | "name";
