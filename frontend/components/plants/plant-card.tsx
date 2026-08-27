"use client";

import { useRef, useState } from "react";
import { flushSync } from "react-dom";
import { useGSAP } from "@gsap/react";
import { ArrowLeft, ArrowsClockwise, BookOpenText, Leaf, Sparkle } from "@phosphor-icons/react";
import gsap from "gsap";

import {
  CareGuideFace,
  CareSummaryFace,
  PlantProfileFace,
} from "@/components/plants/plant-card-faces";
import { Button } from "@/components/ui/button";
import type { Plant, PlantStatus } from "@/types/plant";
import type { PetType } from "@/types/user";


gsap.registerPlugin(useGSAP);

interface PlantCardProps {
  plant: Plant;
  userPets: PetType[];
  watering: boolean;
  onWater: (plant: Plant) => void;
  onEdit: (plant: Plant) => void;
  onHistory: (plant: Plant) => void;
  onDelete: (plant: Plant) => void;
  xpGain?: { amount: number; key: number };
}

type CardFace = 0 | 1 | 2;

const faceLabels = ["Care status", "Plant profile", "Growing guide"] as const;
const nextLabels = ["Plant details", "Care guide", "Care status"] as const;
const cardStatusStyles: Record<
  PlantStatus,
  { label: string; message: string; color: string; soft: string }
> = {
  Healthy: {
    label: "Healthy",
    message: "Care is on track",
    color: "var(--healthy)",
    soft: "var(--healthy-soft)",
  },
  "Needs Water Soon": {
    label: "Needs water soon",
    message: "Plan the next watering",
    color: "var(--soon)",
    soft: "var(--soon-soft)",
  },
  "Overdue / High Risk": {
    label: "Overdue",
    message: "Watering needs attention",
    color: "var(--risk)",
    soft: "var(--risk-soft)",
  },
};
const faceIcons = [
  <Leaf key="care" size={16} weight="fill" aria-hidden="true" />,
  <Sparkle key="profile" size={16} weight="fill" aria-hidden="true" />,
  <BookOpenText key="guide" size={16} weight="fill" aria-hidden="true" />,
] as const;

export function PlantCard(props: PlantCardProps) {
  const { plant } = props;
  const statusStyle = cardStatusStyles[plant.status];
  const cardRef = useRef<HTMLElement>(null);
  const faceRef = useRef<HTMLDivElement>(null);
  const [face, setFace] = useState<CardFace>(0);
  const [animating, setAnimating] = useState(false);
  const animationLocked = useRef(false);

  const { contextSafe } = useGSAP(
    () => {
      gsap.set(faceRef.current, {
        transformPerspective: 1200,
        transformOrigin: "50% 50%",
        transformStyle: "preserve-3d",
      });
    },
    { scope: cardRef },
  );

  function showFace(nextFace: CardFace, direction: 1 | -1) {
    const runAnimation = contextSafe(() => {
      const faceElement = faceRef.current;
      if (!faceElement || animationLocked.current || nextFace === face) return;

      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        setFace(nextFace);
        return;
      }

      animationLocked.current = true;
      setAnimating(true);

      gsap
        .timeline({
          defaults: { overwrite: "auto" },
          onComplete: () => {
            animationLocked.current = false;
            setAnimating(false);
          },
        })
        .to(faceElement, {
          rotationY: direction * -5,
          y: -2,
          duration: 0.08,
          ease: "power1.out",
        })
        .to(faceElement, {
          rotationY: direction * -92,
          autoAlpha: 0.04,
          scale: 0.985,
          duration: 0.2,
          ease: "power2.in",
        })
        .add(() => {
          flushSync(() => setFace(nextFace));
          gsap.set(faceElement, {
            rotationY: direction * 92,
            autoAlpha: 0.04,
            y: 2,
          });
        })
        .to(faceElement, {
          rotationY: 0,
          autoAlpha: 1,
          scale: 1,
          y: 0,
          duration: 0.36,
          ease: "power3.out",
          clearProps: "transform,opacity,visibility",
        });
    });

    runAnimation();
  }

  function showNextFace() {
    showFace(((face + 1) % 3) as CardFace, 1);
  }

  function showPreviousFace() {
    showFace(((face + 2) % 3) as CardFace, -1);
  }

  return (
    <article
      ref={cardRef}
      aria-busy={animating}
      aria-roledescription="three-stage plant card"
      className="group flex min-h-full flex-col overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--surface)] shadow-[0_14px_38px_rgba(31,96,61,0.055)] transition-[border-color,transform,box-shadow] duration-200 hover:-translate-y-0.5 hover:border-[var(--line-strong)] hover:shadow-[var(--shadow)]"
      style={{
        borderColor: `color-mix(in srgb, ${statusStyle.color} 48%, var(--line))`,
        backgroundColor: `color-mix(in srgb, ${statusStyle.soft} 46%, var(--surface))`,
      }}
    >
      <div
        className="flex min-h-10 items-center justify-between gap-3 px-5 py-2 text-xs font-bold sm:px-6"
        style={{ backgroundColor: statusStyle.soft, color: statusStyle.color }}
        role="status"
        aria-label={`${plant.nickname} is ${statusStyle.label}`}
      >
        <span>{statusStyle.label}</span>
        <span className="font-semibold opacity-80">{statusStyle.message}</span>
      </div>
      <div
        ref={faceRef}
        className={`flex-1 [backface-visibility:hidden] ${animating ? "pointer-events-none" : ""}`}
      >
        {face === 0 && <CareSummaryFace {...props} />}
        {face === 1 && <PlantProfileFace plant={plant} />}
        {face === 2 && <CareGuideFace plant={plant} />}
      </div>

      <nav
        aria-label={`Views for ${plant.nickname}`}
        className="relative flex items-center gap-2 border-t border-[var(--line)] bg-[var(--surface-raised)] p-2"
      >
        <button
          type="button"
          onClick={showPreviousFace}
          disabled={animating}
          className="grid size-10 shrink-0 place-items-center rounded-full text-[var(--text-muted)] transition-colors hover:bg-[var(--page-muted)] hover:text-[var(--text)] disabled:opacity-50"
          aria-label={`Show previous view for ${plant.nickname}`}
        >
          <ArrowLeft size={17} aria-hidden="true" />
        </button>

        <div className="min-w-0 flex-1 px-1">
          <div className="flex gap-1" aria-hidden="true">
            {faceLabels.map((label, index) => (
              <span
                key={label}
                className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                  index === face ? "bg-[var(--accent)]" : "bg-[var(--line)]"
                }`}
              />
            ))}
          </div>
          <p className="mt-1.5 flex items-center gap-1.5 truncate text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--text-soft)]">
            <span className="text-[var(--accent)]">{faceIcons[face]}</span>
            {faceLabels[face]} · {face + 1} of 3
          </p>
          <span className="sr-only" aria-live="polite">
            Showing {faceLabels[face]} for {plant.nickname}
          </span>
        </div>

        <Button
          variant="secondary"
          size="sm"
          className="min-w-[8.25rem]"
          onClick={showNextFace}
          disabled={animating}
          aria-label={`Flip ${plant.nickname} to ${nextLabels[face].toLowerCase()}`}
        >
          <ArrowsClockwise
            size={16}
            className={animating ? "animate-spin" : ""}
            aria-hidden="true"
          />
          {nextLabels[face]}
        </Button>
      </nav>
    </article>
  );
}
