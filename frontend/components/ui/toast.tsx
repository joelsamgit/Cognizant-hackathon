"use client";

import { CheckCircle, Warning, X } from "@phosphor-icons/react";


export interface ToastMessage {
  id: number;
  message: string;
  tone: "success" | "error";
}

interface ToastViewportProps {
  toasts: ToastMessage[];
  onDismiss: (id: number) => void;
}

export function ToastViewport({ toasts, onDismiss }: ToastViewportProps) {
  return (
    <div
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2"
      aria-live="polite"
      aria-atomic="false"
    >
      {toasts.map((toast) => {
        const Icon = toast.tone === "success" ? CheckCircle : Warning;
        return (
          <div
            key={toast.id}
            role="status"
            className="pointer-events-auto flex items-start gap-3 rounded-2xl border border-[var(--line)] bg-[var(--surface-raised)] p-4 shadow-[var(--shadow)]"
          >
            <Icon
              size={20}
              weight="fill"
              className={toast.tone === "success" ? "text-[var(--healthy)]" : "text-[var(--risk)]"}
              aria-hidden="true"
            />
            <p className="min-w-0 flex-1 text-sm font-medium leading-5 text-[var(--text)]">
              {toast.message}
            </p>
            <button
              type="button"
              onClick={() => onDismiss(toast.id)}
              className="rounded-full p-1 text-[var(--text-muted)] transition-colors hover:bg-[var(--page-muted)] hover:text-[var(--text)]"
              aria-label="Dismiss notification"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        );
      })}
    </div>
  );
}

