import { describe, expect, it } from "vitest";

import { getRooms, queryPlants } from "./plant-query";
import type { Plant } from "../types/plant";


const basePlant: Plant = {
  id: 1,
  nickname: "Greeny",
  species: "Golden Pothos",
  room: "Living Room",
  sunlight: "Indirect Light",
  watering_frequency: 7,
  last_watered: "2026-08-21T10:00:00Z",
  notes: null,
  catalog_key: null,
  details: null,
  care_guide: null,
  created_at: "2026-08-01T10:00:00Z",
  updated_at: "2026-08-21T10:00:00Z",
  days_since_watered: 4,
  days_until_due: 3,
  risk_score: 57,
  status: "Needs Water Soon",
  current_streak: 2,
  longest_streak: 4,
  consistency_pct: 75,
  total_waterings: 4,
  xp: 30,
  growth_stage: 2,
  mood: "doubtful",
  history: [],
  milestone: null,
  pet_safety: "toxic",
  pet_severity: "toxic",
  toxic_cats: true,
  toxic_dogs: true,
  placement_tip: "Keep high.",
  season: "Post-monsoon",
  base_watering_frequency: 7,
  effective_watering_frequency: 7,
  season_factor: 1,
};

const plants: Plant[] = [
  basePlant,
  {
    ...basePlant,
    id: 2,
    nickname: "Nori",
    species: "Calathea Orbifolia",
    room: "Office",
    risk_score: 100,
    status: "Overdue / High Risk",
  },
];

describe("queryPlants", () => {
  it("combines room filtering, species search, and risk sorting", () => {
    const result = queryPlants(plants, { room: "Office", search: "calathea", sort: "risk-desc", petSafety: "all" });
    expect(result.map((plant) => plant.nickname)).toEqual(["Nori"]);
  });

  it("sorts the highest risk first by default", () => {
    const result = queryPlants(plants, { room: "All", search: "", sort: "risk-desc", petSafety: "all" });
    expect(result.map((plant) => plant.risk_score)).toEqual([100, 57]);
  });

  it("filters pet-safe plants and can hide toxic records", () => {
    const safe = { ...plants[1], pet_safety: "safe" as const, toxic_cats: false };
    expect(queryPlants([basePlant, safe], { room: "All", search: "", sort: "name", petSafety: "safe" })).toEqual([safe]);
    expect(queryPlants([basePlant, safe], { room: "All", search: "", sort: "name", petSafety: "hide-toxic" })).toEqual([safe]);
  });

  it("builds unique room filters from records", () => {
    expect(getRooms([...plants, { ...basePlant, id: 3 }])).toEqual(["Living Room", "Office"]);
  });
});
