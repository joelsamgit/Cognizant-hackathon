import type { Plant, PlantSort } from "../types/plant";


interface QueryOptions {
  room: string;
  search: string;
  sort: PlantSort;
}

export function queryPlants(plants: Plant[], options: QueryOptions): Plant[] {
  const searchTerm = options.search.trim().toLocaleLowerCase();

  return plants
    .filter((plant) => options.room === "All" || plant.room === options.room)
    .filter((plant) => {
      if (!searchTerm) return true;
      return [plant.nickname, plant.species].some((value) =>
        value.toLocaleLowerCase().includes(searchTerm),
      );
    })
    .toSorted((left, right) => {
      switch (options.sort) {
        case "risk-asc":
          return left.risk_score - right.risk_score || left.nickname.localeCompare(right.nickname);
        case "recent":
          return new Date(right.last_watered).getTime() - new Date(left.last_watered).getTime();
        case "name":
          return left.nickname.localeCompare(right.nickname);
        case "risk-desc":
        default:
          return right.risk_score - left.risk_score || left.nickname.localeCompare(right.nickname);
      }
    });
}

export function getRooms(plants: Plant[]): string[] {
  return [...new Set(plants.map((plant) => plant.room))].toSorted((a, b) => a.localeCompare(b));
}
