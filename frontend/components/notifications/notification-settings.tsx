"use client";

import { useEffect, useRef, useState } from "react";
import { Bell, BellSlash, PaperPlaneTilt, SpinnerGap } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import {
  getNotificationConfig,
  removePushSubscription,
  savePushSubscription,
  sendTestNotification,
  type NotificationConfig,
} from "@/services/notifications";
import { ApiError } from "@/services/plants";


interface NotificationSettingsProps {
  onNotify: (message: string, tone?: "success" | "error") => void;
}

const REMINDER_TIME_KEY = "plant-guardian-reminder-time";

function messageFrom(error: unknown): string {
  return error instanceof ApiError ? error.message : "Notification settings could not be updated.";
}

function base64UrlToBytes(value: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const normalized = (value + padding).replaceAll("-", "+").replaceAll("_", "/");
  const raw = window.atob(normalized);
  const buffer = new ArrayBuffer(raw.length);
  const bytes = new Uint8Array(buffer);
  for (let index = 0; index < raw.length; index += 1) bytes[index] = raw.charCodeAt(index);
  return bytes;
}

export function NotificationSettings({ onNotify }: NotificationSettingsProps) {
  const [config, setConfig] = useState<NotificationConfig | null>(null);
  const [supported, setSupported] = useState(true);
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const [reminderTime, setReminderTime] = useState("09:00");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const registrationRef = useRef<ServiceWorkerRegistration | null>(null);

  useEffect(() => {
    let active = true;

    async function initialize() {
      if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
        if (active) setSupported(false);
        return;
      }

      try {
        const storedTime = window.localStorage.getItem(REMINDER_TIME_KEY);
        if (storedTime) setReminderTime(storedTime);
      } catch {
        // Reminder delivery still works when browser storage is unavailable.
      }

      try {
        const nextConfig = await getNotificationConfig();
        if (!active) return;
        setConfig(nextConfig);
        if (!nextConfig.enabled) return;

        const registration = await navigator.serviceWorker.register("/sw.js");
        registrationRef.current = registration;
        const existing = await registration.pushManager.getSubscription();
        if (active) setSubscription(existing);
      } catch (nextError) {
        if (active) setError(messageFrom(nextError));
      }
    }

    void initialize();
    return () => {
      active = false;
    };
  }, []);

  async function enableReminders() {
    if (!config?.public_key) return;
    setBusy(true);
    setError(null);
    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        throw new ApiError("Notification permission was not granted. You can change it in browser settings.", 0);
      }
      const registration = registrationRef.current ?? (await navigator.serviceWorker.register("/sw.js"));
      registrationRef.current = registration;
      const nextSubscription =
        (await registration.pushManager.getSubscription()) ??
        (await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: base64UrlToBytes(config.public_key),
        }));
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
      await savePushSubscription(nextSubscription, timezone, reminderTime);
      window.localStorage.setItem(REMINDER_TIME_KEY, reminderTime);
      setSubscription(nextSubscription);
      onNotify("Daily plant reminders are enabled");
    } catch (nextError) {
      const message = messageFrom(nextError);
      setError(message);
      onNotify(message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function saveReminderTime() {
    if (!subscription) return;
    setBusy(true);
    setError(null);
    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
      await savePushSubscription(subscription, timezone, reminderTime);
      window.localStorage.setItem(REMINDER_TIME_KEY, reminderTime);
      onNotify(`Reminder time updated to ${reminderTime}`);
    } catch (nextError) {
      const message = messageFrom(nextError);
      setError(message);
      onNotify(message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function disableReminders() {
    if (!subscription) return;
    setBusy(true);
    setError(null);
    try {
      await removePushSubscription(subscription.endpoint);
      await subscription.unsubscribe();
      window.localStorage.removeItem(REMINDER_TIME_KEY);
      setSubscription(null);
      onNotify("Plant reminders are disabled");
    } catch (nextError) {
      const message = messageFrom(nextError);
      setError(message);
      onNotify(message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function sendTest() {
    if (!subscription) return;
    setBusy(true);
    setError(null);
    try {
      await sendTestNotification(subscription.endpoint);
      onNotify("Test notification sent");
    } catch (nextError) {
      const message = messageFrom(nextError);
      setError(message);
      onNotify(message, "error");
    } finally {
      setBusy(false);
    }
  }

  if (!supported) {
    return (
      <section className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-5">
        <p className="text-sm font-semibold text-[var(--text)]">Browser reminders are not supported here.</p>
      </section>
    );
  }

  if (!config && !error) {
    return <div className="skeleton h-24 rounded-2xl" aria-label="Loading reminder settings" />;
  }

  if (config && !config.enabled) {
    return (
      <section className="flex items-start gap-3 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-5">
        <BellSlash size={21} className="mt-0.5 shrink-0 text-[var(--text-soft)]" aria-hidden="true" />
        <div>
          <p className="text-sm font-semibold text-[var(--text)]">Push reminders need server configuration</p>
          <p className="mt-1 text-xs leading-5 text-[var(--text-muted)]">
            Add the VAPID public and private keys to enable notification delivery.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-5 shadow-[0_12px_32px_rgba(31,96,61,0.045)]">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
            <Bell size={20} weight="fill" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-[var(--text)]">Daily care reminders</h2>
            <p className="mt-1 text-xs leading-5 text-[var(--text-muted)]">
              {subscription
                ? "This browser will notify you about plants due for a soil check."
                : "Enable notifications for due and overdue plants, even when the dashboard is closed."}
            </p>
          </div>
        </div>

        {subscription ? (
          <div className="flex flex-wrap items-center gap-2">
            <label className="flex items-center gap-2 text-xs font-semibold text-[var(--text-muted)]">
              At
              <input
                type="time"
                value={reminderTime}
                onChange={(event) => setReminderTime(event.target.value)}
                className="min-h-10 rounded-full border border-[var(--line)] bg-[var(--surface-raised)] px-3 text-sm text-[var(--text)]"
              />
            </label>
            <Button variant="secondary" size="sm" onClick={() => void saveReminderTime()} disabled={busy}>
              Save
            </Button>
            <Button variant="secondary" size="sm" onClick={() => void sendTest()} disabled={busy}>
              <PaperPlaneTilt size={15} aria-hidden="true" />
              Test
            </Button>
            <Button variant="ghost" size="sm" onClick={() => void disableReminders()} disabled={busy}>
              Disable
            </Button>
          </div>
        ) : (
          <Button onClick={() => void enableReminders()} disabled={busy || !config}>
            {busy ? <SpinnerGap size={17} className="animate-spin" aria-hidden="true" /> : <Bell size={17} aria-hidden="true" />}
            {busy ? "Enabling" : "Enable reminders"}
          </Button>
        )}
      </div>
      {error && <p className="mt-3 text-xs font-medium text-[var(--risk)]" role="alert">{error}</p>}
    </section>
  );
}
