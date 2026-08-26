import type { PlantMood } from "@/types/plant";

interface PlantAvatarProps {
  stage: 1 | 2 | 3 | 4 | 5;
  mood: PlantMood;
  size?: number;
}

const stageNames = ["Seed companion", "Sprout companion", "Seedling companion", "Flowering companion", "Thriving companion"];

export function PlantAvatar({ stage, mood, size = 72 }: PlantAvatarProps) {
  const stemTop = [54, 45, 34, 24, 16][stage - 1];
  const leafCount = [0, 2, 4, 6, 8][stage - 1];
  const face = mood === "happy" ? "happy" : mood === "sad" ? "sad" : "doubtful";

  return (
    <svg viewBox="0 0 100 112" width={size} height={Math.round(size * 1.12)} className={`plant-avatar plant-avatar--${mood} shrink-0`} role="img" aria-label={`${stageNames[stage - 1]}, ${mood}`}>
      <ellipse cx="50" cy="103" rx="27" ry="5" fill="var(--text-soft)" opacity="0.2" />
      <g className="plant-avatar__growth">
        {stage === 1 ? (
          <g className="plant-avatar__seed-character">
            <ellipse cx="50" cy="57" rx="12" ry="9" fill="var(--healthy)" />
            <path d="M44 51 Q49 44 55 50" fill="none" stroke="var(--healthy)" strokeWidth="3" strokeLinecap="round" />
          </g>
        ) : (
          <>
            <path d={`M50 66 Q48 48 50 ${stemTop}`} fill="none" stroke="var(--healthy)" strokeWidth="5" strokeLinecap="round" />
            {Array.from({ length: leafCount }, (_, index) => {
              const y = 54 - index * 5.7;
              const left = index % 2 === 0;
              return (
                <g key={`${stage}-${index}`} className="plant-avatar__leaf">
                  <path d={left ? `M50 ${y} C38 ${y - 10} 25 ${y - 3} 47 ${y + 6}` : `M51 ${y} C62 ${y - 10} 75 ${y - 3} 53 ${y + 6}`} fill="var(--healthy)" />
                  <path d={left ? `M46 ${y + 3} Q37 ${y - 1} 31 ${y - 2}` : `M54 ${y + 3} Q63 ${y - 1} 69 ${y - 2}`} fill="none" stroke="var(--healthy-soft)" strokeWidth="1.2" opacity="0.8" />
                </g>
              );
            })}
            {stage >= 4 && <path d="M50 31 Q40 25 34 20 M50 38 Q61 32 68 27" fill="none" stroke="var(--healthy)" strokeWidth="3" strokeLinecap="round" />}
            {stage === 4 && <Bud x={50} y={stemTop} />}
            {stage === 5 && <><Flower x={50} y={stemTop} /><Flower x={31} y={22} small /><Flower x={69} y={28} small /></>}
          </>
        )}
      </g>
      <g className="plant-avatar__pot">
        <path d="M23 70 H77 L70 99 Q50 108 30 99 Z" fill="var(--accent)" />
        <path d="M27 83 H73" stroke="var(--healthy-soft)" strokeWidth="2" opacity="0.75" />
        <ellipse cx="50" cy="70" rx="28" ry="8" fill="var(--healthy)" />
        <ellipse cx="50" cy="69" rx="22" ry="4.5" fill="var(--soon)" opacity="0.72" />
        <ellipse cx="36" cy="101" rx="7" ry="3" fill="var(--accent)" />
        <ellipse cx="64" cy="101" rx="7" ry="3" fill="var(--accent)" />
        <PotFace mood={face} />
      </g>
    </svg>
  );
}

function PotFace({ mood }: { mood: "happy" | "doubtful" | "sad" }) {
  return (
    <g className="plant-avatar__pot-face">
      <ellipse cx="41" cy="84" rx="3" ry="4" fill="var(--text)" />
      <ellipse cx="59" cy="84" rx="3" ry="4" fill="var(--text)" />
      <circle cx="33" cy="89" r="3" fill="var(--risk-soft)" opacity="0.85" />
      <circle cx="67" cy="89" r="3" fill="var(--risk-soft)" opacity="0.85" />
      <path d={mood === "happy" ? "M42 91 Q50 98 58 91" : mood === "sad" ? "M42 97 Q50 90 58 97" : "M44 94 Q50 91 56 94"} fill="none" stroke="var(--text)" strokeWidth="2" strokeLinecap="round" />
      {mood === "doubtful" && <path d="M37 78 L44 80 M56 80 L63 78" stroke="var(--text)" strokeWidth="1.6" strokeLinecap="round" />}
    </g>
  );
}

function Bud({ x, y }: { x: number; y: number }) {
  return <path d={`M${x} ${y} q6 -7 0 -12 q-6 5 0 12`} fill="var(--soon)" />;
}

function Flower({ x, y, small = false }: { x: number; y: number; small?: boolean }) {
  const radius = small ? 4 : 6;
  return (
    <g className="plant-avatar__flower" transform={`translate(${x} ${y})`}>
      <circle cy={-radius} r={radius} fill="var(--healthy-soft)" />
      <circle cy={radius} r={radius} fill="var(--healthy-soft)" />
      <circle cx={-radius} r={radius} fill="var(--healthy-soft)" />
      <circle cx={radius} r={radius} fill="var(--healthy-soft)" />
      <circle r={radius * 0.65} fill="var(--soon)" />
    </g>
  );
}
