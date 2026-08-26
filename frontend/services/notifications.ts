import { ApiError, request } from "./plants";


export interface NotificationConfig {
  enabled: boolean;
  public_key: string | null;
}

interface SubscriptionResponse {
  id: number;
  timezone: string;
  reminder_time: string;
  enabled: boolean;
}

export function getNotificationConfig(): Promise<NotificationConfig> {
  return request<NotificationConfig>("/notifications/config");
}

export function savePushSubscription(
  subscription: PushSubscription,
  timezone: string,
  reminderTime: string,
): Promise<SubscriptionResponse> {
  const serialized = subscription.toJSON();
  if (!serialized.endpoint || !serialized.keys?.p256dh || !serialized.keys.auth) {
    throw new ApiError("The browser returned an incomplete push subscription.", 0);
  }

  return request<SubscriptionResponse>("/notifications/subscriptions", {
    method: "POST",
    body: JSON.stringify({
      endpoint: serialized.endpoint,
      keys: serialized.keys,
      timezone,
      reminder_time: reminderTime,
    }),
  });
}

export function removePushSubscription(endpoint: string): Promise<void> {
  return request<void>("/notifications/subscriptions", {
    method: "DELETE",
    body: JSON.stringify({ endpoint }),
  });
}

export function sendTestNotification(endpoint: string): Promise<void> {
  return request<void>("/notifications/test", {
    method: "POST",
    body: JSON.stringify({ endpoint }),
  });
}
