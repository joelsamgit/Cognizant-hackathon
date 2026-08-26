import { CaretDown, MagnifyingGlass, SlidersHorizontal } from "@phosphor-icons/react/dist/ssr";

import type { PetSafetyFilter, PlantSort } from "@/types/plant";


interface FilterToolbarProps {
  rooms: string[];
  selectedRoom: string;
  onRoomChange: (room: string) => void;
  search: string;
  onSearchChange: (search: string) => void;
  sort: PlantSort;
  onSortChange: (sort: PlantSort) => void;
  petSafety: PetSafetyFilter;
  onPetSafetyChange: (filter: PetSafetyFilter) => void;
}

export function FilterToolbar({
  rooms,
  selectedRoom,
  onRoomChange,
  search,
  onSearchChange,
  sort,
  onSortChange,
  petSafety,
  onPetSafetyChange,
}: FilterToolbarProps) {
  return (
    <section aria-label="Plant filters" className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row">
        <label className="relative min-w-0 flex-1">
          <span className="sr-only">Search by nickname or species</span>
          <MagnifyingGlass
            size={18}
            className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-soft)]"
            aria-hidden="true"
          />
          <input
            type="search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search nickname or species"
            className="min-h-12 w-full rounded-full border border-[var(--line)] bg-[var(--surface-raised)] py-2 pl-11 pr-4 text-sm text-[var(--text)] shadow-[0_8px_24px_rgba(31,96,61,0.04)] transition-colors placeholder:text-[var(--text-soft)] hover:border-[var(--line-strong)] focus:border-[var(--accent)] focus:outline-none"
          />
        </label>

        <label className="relative md:w-52">
          <span className="sr-only">Sort plants</span>
          <SlidersHorizontal
            size={17}
            className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-soft)]"
            aria-hidden="true"
          />
          <select
            value={sort}
            onChange={(event) => onSortChange(event.target.value as PlantSort)}
            className="min-h-12 w-full appearance-none rounded-full border border-[var(--line)] bg-[var(--surface-raised)] py-2 pl-11 pr-9 text-sm font-semibold text-[var(--text)] shadow-[0_8px_24px_rgba(31,96,61,0.04)] transition-colors hover:border-[var(--line-strong)] focus:border-[var(--accent)] focus:outline-none"
          >
            <option value="risk-desc">Highest risk</option>
            <option value="risk-asc">Lowest risk</option>
            <option value="recent">Recently watered</option>
            <option value="name">Name</option>
          </select>
          <CaretDown
            size={14}
            weight="bold"
            className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[var(--text-soft)]"
            aria-hidden="true"
          />
        </label>
        <label className="relative md:w-44">
          <span className="sr-only">Filter by pet safety</span>
          <select
            value={petSafety}
            onChange={(event) => onPetSafetyChange(event.target.value as PetSafetyFilter)}
            className="min-h-12 w-full appearance-none rounded-full border border-[var(--line)] bg-[var(--surface-raised)] py-2 pl-4 pr-9 text-sm font-semibold text-[var(--text)] shadow-[0_8px_24px_rgba(31,96,61,0.04)] transition-colors hover:border-[var(--line-strong)] focus:border-[var(--accent)] focus:outline-none"
          >
            <option value="all">All pet safety</option>
            <option value="safe">Safe only</option>
            <option value="hide-toxic">Hide toxic</option>
          </select>
          <CaretDown
            size={14}
            weight="bold"
            className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[var(--text-soft)]"
            aria-hidden="true"
          />
        </label>
      </div>

      <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1" aria-label="Filter plants by room">
        {["All", ...rooms].map((room) => {
          const active = room === selectedRoom;
          return (
            <button
              key={room}
              type="button"
              onClick={() => onRoomChange(room)}
              aria-pressed={active}
              className={`min-h-9 shrink-0 rounded-full border px-4 text-sm font-semibold transition-colors active:translate-y-px ${
                active
                  ? "border-[var(--accent)] bg-[var(--accent)] text-[var(--text)]"
                  : "border-[var(--line)] bg-[var(--surface)] text-[var(--text-muted)] hover:border-[var(--line-strong)] hover:text-[var(--text)]"
              }`}
            >
              {room}
            </button>
          );
        })}
      </div>
    </section>
  );
}
