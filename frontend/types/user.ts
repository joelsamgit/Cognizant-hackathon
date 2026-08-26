export const petOptions = [
  "No pets",
  "Dogs",
  "Cats",
  "Birds",
  "Fish",
  "Small pets",
  "Reptiles",
  "Other",
] as const;

export type PetType = (typeof petOptions)[number];

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  place: string;
  pets: PetType[];
  timezone: string;
  created_at: string;
  updated_at: string;
  account_current_streak: number;
  account_longest_streak: number;
  account_xp: number;
  account_growth_stage: 1 | 2 | 3 | 4 | 5;
  account_mood: "happy" | "doubtful" | "sad";
  account_total_waterings: number;
}

export interface SignupPayload {
  email: string;
  password: string;
  full_name: string;
  place: string;
  pets: PetType[];
  timezone: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface GoogleAuthPayload {
  credential: string;
  full_name?: string;
  place?: string;
  pets?: PetType[];
}

export interface ProfilePayload {
  full_name: string;
  place: string;
  pets: PetType[];
  timezone: string;
}
