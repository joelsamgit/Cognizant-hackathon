import { afterEach, describe, expect, it, vi } from "vitest";

import { getCurrentUser, login, logout, signup, updateProfile } from "./auth";


afterEach(() => {
  vi.unstubAllGlobals();
});

describe("account API service", () => {
  it("uses cookie-backed account endpoints", async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ id: 1 }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getCurrentUser();
    await signup({
      email: "asha@example.com",
      password: "strong-password",
      full_name: "Asha Nair",
      place: "Kochi",
      pets: ["Cats"],
      timezone: "Asia/Kolkata",
    });
    await login({ email: "asha@example.com", password: "strong-password" });
    await updateProfile({
      full_name: "Asha Nair",
      place: "Kochi",
      pets: ["Cats", "Dogs"],
      timezone: "Asia/Kolkata",
    });
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));
    await logout();

    expect(fetchMock.mock.calls.map(([url, init]) => [url, init?.method ?? "GET"])).toEqual([
      ["/api/auth/me", "GET"],
      ["/api/auth/signup", "POST"],
      ["/api/auth/login", "POST"],
      ["/api/profile", "PATCH"],
      ["/api/auth/logout", "POST"],
    ]);
    expect(fetchMock.mock.calls.every(([, init]) => init?.credentials === "same-origin")).toBe(true);
  });
});
