import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getNotificationConfig,
  removePushSubscription,
  savePushSubscription,
  sendTestNotification,
} from "./notifications";


afterEach(() => {
  vi.unstubAllGlobals();
});

describe("notification API service", () => {
  it("registers, tests, and removes a browser subscription", async () => {
    const jsonResponse = () =>
      new Response(JSON.stringify({ enabled: true, public_key: "public-key" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(jsonResponse()));
    vi.stubGlobal("fetch", fetchMock);

    const subscription = {
      endpoint: "https://push.example.test/1",
      toJSON: () => ({
        endpoint: "https://push.example.test/1",
        keys: { p256dh: "encryption-key", auth: "auth-secret" },
      }),
    } as unknown as PushSubscription;

    await getNotificationConfig();
    await savePushSubscription(subscription, "UTC", "09:00");
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));
    await sendTestNotification(subscription.endpoint);
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));
    await removePushSubscription(subscription.endpoint);

    expect(fetchMock.mock.calls.map(([url, init]) => [url, init?.method ?? "GET"])).toEqual([
      ["/api/notifications/config", "GET"],
      ["/api/notifications/subscriptions", "POST"],
      ["/api/notifications/test", "POST"],
      ["/api/notifications/subscriptions", "DELETE"],
    ]);
  });
});
