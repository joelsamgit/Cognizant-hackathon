import {
  BookOpenText,
  CalendarBlank,
  ClockCounterClockwise,
  Drop,
  Lightbulb,
  MapPin,
  Note,
  PawPrint,
  PencilSimple,
  Quotes,
  Sparkle,
  SpinnerGap,
  Sun,
  Trash,
  WarningCircle,
} from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import { formatLastWatered, formatNextWatering } from "@/lib/dates";
import { buildPetSafetyMessage } from "@/lib/pet-safety";
import type { Plant, PlantStatus } from "@/types/plant";
import type { PetType } from "@/types/user";


interface SummaryFaceProps {
  plant: Plant;
  userPets: PetType[];
  watering: boolean;
  onWater: (plant: Plant) => void;
  onEdit: (plant: Plant) => void;
  onHistory: (plant: Plant) => void;
  onDelete: (plant: Plant) => void;
  xpGain?: { amount: number; key: number };
}

const statusStyles: Record<PlantStatus, { bar: string; score: string }> = {
  Healthy: {
    bar: "bg-[var(--healthy)]",
    score: "text-[var(--healthy)]",
  },
  "Needs Water Soon": {
    bar: "bg-[var(--soon)]",
    score: "text-[var(--soon)]",
  },
  "Overdue / High Risk": {
    bar: "bg-[var(--risk)]",
    score: "text-[var(--risk)]",
  },
};

export function CareSummaryFace({
  plant,
  userPets,
  watering,
  onWater,
  onEdit,
  onHistory,
  onDelete,
  xpGain,
}: SummaryFaceProps) {
  const styles = statusStyles[plant.status];

  return (
    <div className="flex min-h-[38rem] flex-col p-5 sm:p-6">
      <header>
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="min-w-0">
          <p className="mb-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--text-soft)]">
            Care status
          </p>
          <h2 className="truncate text-xl font-bold tracking-[-0.025em] text-[var(--text)]">
            {plant.nickname}
          </h2>
          <p className="mt-1 truncate text-sm font-medium text-[var(--text-muted)]">{plant.species}</p>
            </div>
          </div>
          <PetSafetyBadge plant={plant} userPets={userPets} />
        </div>
      </header>

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
        <Metric icon={<CalendarBlank size={15} aria-hidden="true" />} label="Last watered">
          {formatLastWatered(plant.days_since_watered)}
        </Metric>
        <Metric icon={<Drop size={15} aria-hidden="true" />} label="Water every">
          {plant.base_watering_frequency} days
          {plant.effective_watering_frequency !== plant.base_watering_frequency
            ? ` · ${plant.effective_watering_frequency} in ${plant.season.toLowerCase()}`
            : ""}
        </Metric>
        <Metric icon={<MapPin size={15} aria-hidden="true" />} label="Room">
          {plant.room}
        </Metric>
        <Metric icon={<Sun size={15} aria-hidden="true" />} label="Light">
          {plant.sunlight}
        </Metric>
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

      <div className="mt-auto pt-5">
        <div className="relative">
          {xpGain && (
            <span
              key={xpGain.key}
              aria-hidden="true"
              className="xp-chip pointer-events-none absolute -top-2 left-1/2 z-10 -translate-x-1/2 rounded-full bg-[var(--surface-strong)] px-3 py-1 text-xs font-bold text-[var(--page)] shadow-lg"
            >
              +{xpGain.amount} XP
            </span>
          )}
        <Button
          onClick={() => onWater(plant)}
          disabled={watering || Boolean(plant.watering_locked)}
          className="w-full"
          aria-label={`Record watering for ${plant.nickname}`}
        >
          {watering ? (
            <SpinnerGap size={18} className="animate-spin" aria-hidden="true" />
          ) : (
            <Drop size={18} weight="fill" aria-hidden="true" />
          )}
          {watering
            ? "Recording"
            : plant.watering_locked
              ? `Ready in ${plant.next_watering_in_days ?? 0} day${plant.next_watering_in_days === 1 ? "" : "s"}`
              : "Just Watered"}
        </Button>
        </div>

        <div className="mt-2 flex rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] p-1">
          <Button variant="ghost" size="sm" className="flex-1" onClick={() => onEdit(plant)}>
            <PencilSimple size={16} aria-hidden="true" />
            Edit
          </Button>
          <Button variant="ghost" size="sm" className="flex-1" onClick={() => onHistory(plant)}>
            <ClockCounterClockwise size={16} aria-hidden="true" />
            History
          </Button>
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
      </div>
    </div>
  );
}

function PetSafetyBadge({ plant, userPets }: { plant: Plant; userPets: PetType[] }) {
  if (!plant.pet_safety) return null;
  const label =
    plant.pet_safety === "safe" ? "Pet-safe" : plant.pet_safety === "mild" ? "Mild" : "Toxic";
  const color =
    plant.pet_safety === "safe"
      ? "text-[var(--healthy)] bg-[var(--healthy-soft)]"
      : plant.pet_safety === "mild"
        ? "text-[var(--soon)] bg-[var(--soon-soft)]"
        : "text-[var(--risk)] bg-[var(--risk-soft)]";
  const Icon = plant.pet_safety === "mild" ? WarningCircle : PawPrint;
  const petMessage = buildPetSafetyMessage(plant, userPets);
  return (
    <span
      title={petMessage}
      aria-label={`${label}. ${petMessage ?? ""}`.trim()}
      className={`flex shrink-0 items-center gap-1 rounded-full px-2 py-1 text-[10px] font-bold ${color}`}
    >
      <Icon size={12} weight="fill" aria-hidden="true" />
      {label}
    </span>
  );
}

export function PlantProfileFace({ plant }: { plant: Plant }) {
  const details = plant.details;

  return (
    <div className="flex min-h-[38rem] flex-col p-5 sm:p-6">
      <FaceHeader eyebrow="Plant profile" title={plant.nickname} subtitle={details?.scientific_name ?? plant.species} />

      {details ? (
        <>
          <div className="mt-5 flex flex-wrap gap-2">
            <Pill>{details.category}</Pill>
            <Pill>{details.difficulty}</Pill>
          </div>

          <p className="mt-5 text-lg font-semibold leading-7 tracking-[-0.02em] text-[var(--text)]">
            “{details.tagline}”
          </p>

          <dl className="mt-5 grid grid-cols-2 gap-3">
            <InfoTile label="Also known as">{details.indian_name}</InfoTile>
            <InfoTile label="Personality">{details.vibe}</InfoTile>
          </dl>

          <section className="mt-4 rounded-2xl border border-[color-mix(in_srgb,var(--accent)_24%,var(--line))] bg-[var(--accent-soft)] p-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.12em] text-[var(--accent)]">
              <Sparkle size={16} weight="fill" aria-hidden="true" />
              Did you know?
            </div>
            <p className="mt-2 text-sm leading-6 text-[var(--text)]">{details.fun_fact}</p>
          </section>

          <div className="mt-4 rounded-xl bg-[var(--page-muted)] p-3.5">
            <p className="flex items-center gap-2 text-xs font-bold text-[var(--text-muted)]">
              <MapPin size={16} aria-hidden="true" />
              Ideal spot
            </p>
            <p className="mt-1.5 text-sm leading-6 text-[var(--text)]">{details.ideal_spot}</p>
          </div>

          <details className="mt-4 rounded-xl border border-[var(--line)] px-3.5 py-3">
            <summary className="flex list-none items-center gap-2 text-xs font-bold text-[var(--text-muted)] marker:content-none">
              <Quotes size={16} aria-hidden="true" />
              Story, origin & symbolism
            </summary>
            <div className="mt-3 space-y-3 text-sm leading-6 text-[var(--text-muted)]">
              <p>{details.name_origin}</p>
              <p>{details.cultural_context}</p>
              <p className="font-semibold text-[var(--text)]">{details.symbolism}</p>
            </div>
          </details>
        </>
      ) : (
        <FallbackPanel
          title="A personal profile is waiting"
          body={plant.notes ?? `${plant.nickname} is a ${plant.species} kept in the ${plant.room}.`}
        />
      )}
    </div>
  );
}

export function CareGuideFace({ plant }: { plant: Plant }) {
  const guide = plant.care_guide;

  return (
    <div className="flex min-h-[38rem] flex-col p-5 sm:p-6">
      <FaceHeader
        eyebrow="Growing guide"
        title={plant.nickname}
        subtitle="The essentials for steady, healthy growth"
      />

      <dl className="mt-5 grid grid-cols-2 gap-3">
        <GuideStat
          icon={<Drop size={18} weight="fill" aria-hidden="true" />}
          label="Watering rhythm"
          value={`Every ${guide?.watering_frequency_days ?? plant.watering_frequency} days`}
        />
        <GuideStat
          icon={<Drop size={18} aria-hidden="true" />}
          label="Suggested amount"
          value={guide ? `${guide.water_amount_ml} ml` : "Adjust to pot size"}
        />
      </dl>

      <GuideSection icon={<Sun size={18} aria-hidden="true" />} title={guide?.sunlight ?? plant.sunlight}>
        {guide?.sunlight_detail ?? `Keep in ${plant.sunlight.toLowerCase()} and watch for leaf response.`}
      </GuideSection>

      <GuideSection icon={<BookOpenText size={18} aria-hidden="true" />} title="How to water">
        {guide?.watering_method ??
          `Water thoroughly when due, then check that excess water can drain away from the roots.`}
      </GuideSection>

      <section className="mt-4 rounded-2xl bg-[var(--accent-soft)] p-4">
        <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.12em] text-[var(--accent)]">
          <Lightbulb size={17} weight="fill" aria-hidden="true" />
          Grower’s tip
        </p>
        <p className="mt-2 text-sm leading-6 text-[var(--text)]">
          {guide?.pro_tip ?? plant.notes ?? "Observe new growth and adjust light or watering one change at a time."}
        </p>
      </section>

      <section className="mt-4 rounded-2xl border border-[color-mix(in_srgb,var(--risk)_22%,var(--line))] bg-[var(--risk-soft)] p-4">
        <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.12em] text-[var(--risk)]">
          <WarningCircle size={17} weight="fill" aria-hidden="true" />
          Common mistake
        </p>
        <p className="mt-2 text-sm leading-6 text-[var(--text)]">
          {guide?.common_mistake ?? "Avoid watering on autopilot—check the soil and the plant first."}
        </p>
      </section>
    </div>
  );
}

function FaceHeader({ eyebrow, title, subtitle }: { eyebrow: string; title: string; subtitle: string }) {
  return (
    <header>
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--accent)]">{eyebrow}</p>
      <h2 className="mt-1.5 truncate text-xl font-bold tracking-[-0.025em] text-[var(--text)]">{title}</h2>
      <p className="mt-1 truncate text-sm italic text-[var(--text-muted)]">{subtitle}</p>
    </header>
  );
}

function Metric({ icon, label, children }: { icon: React.ReactNode; label: string; children: React.ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-soft)]">
        {icon}
        {label}
      </dt>
      <dd className="mt-1 truncate text-sm font-semibold text-[var(--text)]">{children}</dd>
    </div>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-[var(--line)] bg-[var(--surface-raised)] px-3 py-1 text-[11px] font-bold text-[var(--text-muted)]">
      {children}
    </span>
  );
}

function InfoTile({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl bg-[var(--page-muted)] p-3">
      <dt className="text-[10px] font-bold uppercase tracking-[0.1em] text-[var(--text-soft)]">{label}</dt>
      <dd className="mt-1 text-xs font-semibold leading-5 text-[var(--text)]">{children}</dd>
    </div>
  );
}

function GuideStat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl bg-[var(--page-muted)] p-3.5">
      <dt className="flex items-center gap-2 text-xs font-semibold text-[var(--text-soft)]">
        <span className="text-[var(--accent)]">{icon}</span>
        {label}
      </dt>
      <dd className="mt-2 text-sm font-bold text-[var(--text)]">{value}</dd>
    </div>
  );
}

function GuideSection({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-4 border-b border-[var(--line)] pb-4">
      <h3 className="flex items-center gap-2 text-sm font-bold text-[var(--text)]">
        <span className="text-[var(--accent)]">{icon}</span>
        {title}
      </h3>
      <p className="mt-1.5 text-sm leading-6 text-[var(--text-muted)]">{children}</p>
    </section>
  );
}

function FallbackPanel({ title, body }: { title: string; body: string }) {
  return (
    <div className="mt-6 rounded-2xl border border-dashed border-[var(--line-strong)] bg-[var(--page-muted)] p-5">
      <Sparkle size={22} className="text-[var(--accent)]" aria-hidden="true" />
      <h3 className="mt-4 font-bold text-[var(--text)]">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{body}</p>
    </div>
  );
}
