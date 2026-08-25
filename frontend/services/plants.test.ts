import { afterEach, describe, expect, it, vi } from "vitest";

import { createPlant, deletePlant, getPlants, updatePlant, waterPlant } from "./plants";
import type { PlantPayload } from "../types/plant";


const payload: PlantPayload = {
  nickname: "Moss",
  species: "Fern",
  room: "Office",
  sunlight: "Indirect Light",
  watering_frequency: 7,
  last_watered: "2026-08-25T10:00:00Z",
  notes: null,
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("plant API service", () => {
  it("uses the expected CRUD and watering endpoints", async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ id: 4 }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getPlants("Office");
    await createPlant(payload);
    await updatePlant(4, { nickname: "Mossy" });
    await waterPlant(4);

    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));
    await deletePlant(4);

    expect(fetchMock.mock.calls.map(([url, init]) => [url, init?.method ?? "GET"])).toEqual([
      ["/api/plants?room=Office", "GET"],
      ["/api/plants", "POST"],
      ["/api/plants/4", "PATCH"],
      ["/api/plants/4/water", "POST"],
      ["/api/plants/4", "DELETE"],
    ]);
  });
});
