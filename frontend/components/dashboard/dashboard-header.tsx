import {
  AirplaneTakeoff,
  Leaf,
  Plus,
  SignOut,
  UserCircle,
} from "@phosphor-icons/react/dist/ssr";

import { Button } from "@/components/ui/button";
import type { UserProfile } from "@/types/user";


interface DashboardHeaderProps {
  onAdd: () => void;
  onVacation: () => void;
  onProfile: () => void;
  onLogout: () => void;
  user: UserProfile;
  loggingOut: boolean;
}

export function DashboardHeader({
  onAdd,
  onVacation,
  onProfile,
  onLogout,
  user,
  loggingOut,
}: DashboardHeaderProps) {
  return (
    <header className="flex flex-col gap-6 border-b border-[var(--line)] pb-7 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex items-start gap-4">
        <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--surface-strong)] text-[var(--page)] shadow-[var(--shadow)]">
          <Leaf size={25} weight="fill" aria-hidden="true" />
        </div>
        <div>
          <p className="mb-1 text-sm font-semibold text-[var(--accent)]">Your living collection</p>
          <h1 className="text-3xl font-bold tracking-[-0.04em] text-[var(--text)] sm:text-4xl">
            Plant Guardian
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--text-muted)] sm:text-base">
            See what needs care today, before a thirsty plant has to ask.
          </p>
        </div>
      </div>
      <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto sm:justify-end">
        <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onProfile}
          className="mr-auto flex min-h-11 items-center gap-3 rounded-full border border-[var(--line)] bg-[var(--surface-raised)] px-3 pr-4 text-left transition-colors hover:border-[var(--accent)] sm:mr-0"
          aria-label="Open profile settings"
        >
          <span className="flex size-8 items-center justify-center rounded-full bg-[var(--accent-soft)] text-[var(--accent)]">
            <UserCircle size={19} weight="fill" aria-hidden="true" />
          </span>
          <span className="min-w-0">
            <span className="block max-w-28 truncate text-xs font-bold text-[var(--text)]">
              {user.full_name.split(" ")[0]}
            </span>
            <span className="block max-w-28 truncate text-[11px] text-[var(--text-soft)]">
              {user.place}
            </span>
          </span>
        </button>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onLogout}
          disabled={loggingOut}
          aria-label="Log out"
        >
          <SignOut size={18} aria-hidden="true" />
          <span className="hidden xl:inline">{loggingOut ? "Leaving" : "Log out"}</span>
        </Button>
        <Button variant="secondary" onClick={onVacation} className="w-full sm:w-auto">
          <AirplaneTakeoff size={18} weight="fill" aria-hidden="true" />
          Vacation Mode
        </Button>
        <Button onClick={onAdd} className="w-full sm:w-auto">
          <Plus size={18} weight="bold" aria-hidden="true" />
          Add Plant
        </Button>
      </div>
    </header>
  );
}

