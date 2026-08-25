"use client";

import { useEffect, useRef } from "react";
import { SpinnerGap, Trash } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import type { Plant } from "@/types/plant";


interface DeleteDialogProps {
  plant: Plant;
  deleting: boolean;
  error: string | null;
  onConfirm: () => void;
  onClose: () => void;
}

export function DeleteDialog({ plant, deleting, error, onConfirm, onClose }: DeleteDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    dialog.showModal();
    return () => dialog.close();
  }, []);

  return (
    <dialog
      ref={dialogRef}
      onCancel={(event) => {
        if (deleting) event.preventDefault();
        else onClose();
      }}
      onClose={onClose}
      className="m-auto w-[min(28rem,calc(100vw-2rem))] rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-0 text-[var(--text)] shadow-[var(--shadow)]"
      aria-labelledby="delete-title"
    >
      <div className="p-6">
        <div className="flex size-11 items-center justify-center rounded-2xl bg-[var(--risk-soft)] text-[var(--risk)]">
          <Trash size={21} weight="duotone" aria-hidden="true" />
        </div>
        <h2 id="delete-title" className="mt-5 text-xl font-bold tracking-[-0.025em]">
          Delete {plant.nickname}?
        </h2>
        <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
          This removes the plant and its care history from your collection. This action cannot be undone.
        </p>
        {error && (
          <p role="alert" className="mt-4 rounded-xl bg-[var(--risk-soft)] px-4 py-3 text-sm font-medium text-[var(--risk)]">
            {error}
          </p>
        )}
      </div>
      <div className="flex flex-col-reverse gap-2 border-t border-[var(--line)] bg-[var(--surface-raised)] p-4 sm:flex-row sm:justify-end">
        <Button variant="secondary" onClick={onClose} disabled={deleting}>
          Keep plant
        </Button>
        <Button variant="danger" onClick={onConfirm} disabled={deleting}>
          {deleting && <SpinnerGap size={18} className="animate-spin" aria-hidden="true" />}
          {deleting ? "Deleting" : "Delete plant"}
        </Button>
      </div>
    </dialog>
  );
}

