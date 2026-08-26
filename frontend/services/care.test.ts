import { afterEach, describe, expect, it, vi } from "vitest";

import { createCareEvent, getCareEvents } from "./care";


afterEach(() => {
  vi.unstubAllGlobals();
});

describe("care history API service", () => {
  it("uses the plant event endpoints", async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getCareEvents(4);
    await createCareEvent(4, {
      action: "check",
      occurred_at: "2026-08-25T10:00:00Z",
      amount_ml: null,
      result: "still_damp",
      notes: null,
    });

    expect(fetchMock.mock.calls.map(([url, init]) => [url, init?.method ?? "GET"])).toEqual([
      ["/api/plants/4/events", "GET"],
      ["/api/plants/4/events", "POST"],
    ]);
  });
});
