"use client";

import {
  CalendarBlank,
  Drop,
  MapPin,
  Note,
  PencilSimple,
  SpinnerGap,
  Sun,
  Trash,
} from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import { formatLastWatered, formatNextWatering } from "@/lib/dates";
import type { Plant, PlantStatus } from "@/types/plant";


interface PlantCardProps {
  plant: Plant;
  watering: boolean;
  onWater: (plant: Plant) => void;
  onEdit: (plant: Plant) => void;
  onDelete: (plant: Plant) => void;
}

const statusStyles: Record<PlantStatus, { badge: string; bar: string; score: string }> = {
  Healthy: {
    badge: "bg-[var(--healthy-soft)] text-[var(--healthy)]",
    bar: "bg-[var(--healthy)]",
    score: "text-[var(--healthy)]",
  },
  "Needs Water Soon": {
    badge: "bg-[var(--soon-soft)] text-[var(--soon)]",
    bar: "bg-[var(--soon)]",
    score: "text-[var(--soon)]",
  },
  "Overdue / High Risk": {
    badge: "bg-[var(--risk-soft)] text-[var(--risk)]",
    bar: "bg-[var(--risk)]",
    score: "text-[var(--risk)]",
  },
};

export function PlantCard({ plant, watering, onWater, onEdit, onDelete }: PlantCardProps) {
  const styles = statusStyles[plant.status];

  return (
    <article className="group flex min-h-full flex-col overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--surface)] shadow-[0_14px_38px_rgba(30,67,47,0.055)] transition-[border-color,transform,box-shadow] duration-200 hover:-translate-y-0.5 hover:border-[var(--line-strong)] hover:shadow-[var(--shadow)]">
      <div className="flex flex-1 flex-col p-5 sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="truncate text-xl font-bold tracking-[-0.025em] text-[var(--text)]">
              {plant.nickname}
            </h2>
            <p className="mt-1 truncate text-sm font-medium text-[var(--text-muted)]">{plant.species}</p>
          </div>
          <span className={`shrink-0 rounded-full px-3 py-1.5 text-[11px] font-bold ${styles.badge}`}>
            {plant.status}
          </span>
        </div>

        <div className="mt-6 rounded-2xl bg-[var(--page-muted)] p-4">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold text-[var(--text-muted)]">Risk score</p>
              <p className={`mt-1 text-4xl font-bold tracking-[-0.05em] tabular-nums ${styles.score}`}>
                {plant.risk_score}
              </p>
            </div>
            <p className="pb-1 text-right text-xs font-semibold text-[var(--text-muted)]">
              {formatNextWatering(plant.days_until_due)}
            </p>
          </div>
          <div
            className="mt-4 h-1.5 overflow-hidden rounded-full bg-[var(--line)]"
            role="progressbar"
            aria-label={`${plant.nickname} risk score`}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={plant.risk_score}
          >
            <div
              className={`h-full rounded-full transition-[width] duration-500 ${styles.bar}`}
              style={{ width: `${plant.risk_score}%` }}
            />
          </div>
        </div>

        <dl className="mt-5 grid grid-cols-2 gap-x-4 gap-y-4">
          <div>
            <dt className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-soft)]">
              <CalendarBlank size={15} aria-hidden="true" />
              Last watered
            </dt>
            <dd className="mt-1 text-sm font-semibold text-[var(--text)]">
              {formatLastWatered(plant.days_since_watered)}
            </dd>
          </div>
          <div>
            <dt className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-soft)]">
              <Drop size={15} aria-hidden="true" />
              Water every
            </dt>
            <dd className="mt-1 text-sm font-semibold text-[var(--text)]">
              {plant.watering_frequency} {plant.watering_frequency === 1 ? "day" : "days"}
            </dd>
          </div>
          <div>
            <dt className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-soft)]">
              <MapPin size={15} aria-hidden="true" />
              Room
            </dt>
            <dd className="mt-1 truncate text-sm font-semibold text-[var(--text)]">{plant.room}</dd>
          </div>
          <div>
            <dt className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-soft)]">
              <Sun size={15} aria-hidden="true" />
              Light
            </dt>
            <dd className="mt-1 truncate text-sm font-semibold text-[var(--text)]">{plant.sunlight}</dd>
          </div>
        </dl>

        {plant.notes && (
          <details className="mt-5 rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] px-3.5 py-3">
            <summary className="flex list-none items-center gap-2 text-xs font-semibold text-[var(--text-muted)] marker:content-none">
              <Note size={15} aria-hidden="true" />
              View care notes
            </summary>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{plant.notes}</p>
          </details>
        )}

        <Button
          onClick={() => onWater(plant)}
          disabled={watering}
          className="mt-5 w-full"
          aria-label={`Record watering for ${plant.nickname}`}
        >
          {watering ? (
            <SpinnerGap size={18} className="animate-spin" aria-hidden="true" />
          ) : (
            <Drop size={18} weight="fill" aria-hidden="true" />
          )}
          {watering ? "Recording" : "Just Watered"}
        </Button>
      </div>

      <div className="flex border-t border-[var(--line)] bg-[var(--surface-raised)] p-2">
        <Button variant="ghost" size="sm" className="flex-1" onClick={() => onEdit(plant)}>
          <PencilSimple size={16} aria-hidden="true" />
          Edit
        </Button>
        <div className="my-1 w-px bg-[var(--line)]" aria-hidden="true" />
        <Button
          variant="ghost"
          size="sm"
          className="flex-1 hover:text-[var(--danger)]"
          onClick={() => onDelete(plant)}
        >
          <Trash size={16} aria-hidden="true" />
          Delete
        </Button>
      </div>
    </article>
  );
}

