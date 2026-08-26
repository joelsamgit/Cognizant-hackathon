import type { Plant, PlantPayload, SeasonOverride } from "../types/plant";


interface ApiValidationItem {
  loc?: Array<string | number>;
  msg?: string;
}

interface ApiErrorBody {
  detail?: string | ApiValidationItem[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getErrorMessage(body: ApiErrorBody | null, fallback: string): string {
  if (typeof body?.detail === "string") {
    return body.detail;
  }

  if (Array.isArray(body?.detail)) {
    return body.detail
      .map((item) => {
        const field = item.loc?.at(-1);
        return `${field ? `${String(field).replaceAll("_", " ")}: ` : ""}${item.msg ?? "Invalid value"}`;
      })
      .join(". ");
  }

  return fallback;
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`/api${path}`, {
      ...options,
      cache: "no-store",
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        ...(options?.body ? { "Content-Type": "application/json" } : {}),
        ...options?.headers,
      },
    });
  } catch {
    throw new ApiError("Plant Guardian cannot reach the care service. Check that the backend is running.", 0);
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null;
    throw new ApiError(getErrorMessage(body, "The request could not be completed"), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function queryString(room?: string, season?: SeasonOverride): string {
  const params = new URLSearchParams();
  if (room) params.set("room", room);
  if (season) params.set("season", season);
  const value = params.toString();
  return value ? `?${value}` : "";
}

export function getPlants(room?: string, season?: SeasonOverride): Promise<Plant[]> {
  const query = queryString(room, season);
  return request<Plant[]>(`/plants${query}`);
}

export function getPlant(id: number): Promise<Plant> {
  return request<Plant>(`/plants/${id}`);
}

export function createPlant(payload: PlantPayload, season?: SeasonOverride): Promise<Plant> {
  return request<Plant>(`/plants${queryString(undefined, season)}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updatePlant(id: number, payload: Partial<PlantPayload>, season?: SeasonOverride): Promise<Plant> {
  return request<Plant>(`/plants/${id}${queryString(undefined, season)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deletePlant(id: number): Promise<void> {
  return request<void>(`/plants/${id}`, { method: "DELETE" });
}

export function waterPlant(id: number, season?: SeasonOverride): Promise<Plant> {
  return request<Plant>(`/plants/${id}/water${queryString(undefined, season)}`, { method: "POST" });
}
