"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { DashboardSkeleton, EmptyGarden, LoadError, NoResults } from "@/components/dashboard/dashboard-states";
import { FilterToolbar } from "@/components/dashboard/filter-toolbar";
import { SummaryGrid } from "@/components/dashboard/summary-grid";
import { SeasonBanner } from "@/components/season/season-banner";
import { SeasonSimulator } from "@/components/season/season-simulator";
import { NotificationSettings } from "@/components/notifications/notification-settings";
import { AccountAvatar } from "@/components/streak/account-avatar";
import { CareHistoryDialog } from "@/components/plants/care-history-dialog";
import { DeleteDialog } from "@/components/plants/delete-dialog";
import { PlantCard } from "@/components/plants/plant-card";
import { PlantFormDialog } from "@/components/plants/plant-form-dialog";
import { ProfileDialog } from "@/components/profile/profile-dialog";
import { VacationDialog } from "@/components/vacation/vacation-dialog";
import { ToastMessage, ToastViewport } from "@/components/ui/toast";
import { getRooms, queryPlants } from "@/lib/plant-query";
import {
  ApiError,
  createPlant,
  deletePlant,
  getPlants,
  updatePlant,
  waterPlant,
} from "@/services/plants";
import { getCurrentUser, updateProfile } from "@/services/auth";
import type { PetSafetyFilter, Plant, PlantPayload, PlantSort, SeasonOverride } from "@/types/plant";
import type { CareEvent } from "@/types/care";
import type { ProfilePayload, UserProfile } from "@/types/user";


type LoadState = "loading" | "ready" | "error";

interface PlantDashboardProps {
  user: UserProfile;
  onUserChange: (user: UserProfile) => void;
  onLogout: () => Promise<void>;
}

function messageFrom(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

export function PlantDashboard({ user, onUserChange, onLogout }: PlantDashboardProps) {
  const [plants, setPlants] = useState<Plant[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState("");
  const [search, setSearch] = useState("");
  const [room, setRoom] = useState("All");
  const [sort, setSort] = useState<PlantSort>("risk-desc");
  const [petSafety, setPetSafety] = useState<PetSafetyFilter>("all");
  const [seasonOverride, setSeasonOverride] = useState<SeasonOverride | undefined>();
  const [formPlant, setFormPlant] = useState<Plant | "new" | null>(null);
  const [formSaving, setFormSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Plant | null>(null);
  const [historyPlant, setHistoryPlant] = useState<Plant | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [wateringIds, setWateringIds] = useState<Set<number>>(() => new Set());
  const [xpGains, setXpGains] = useState<Record<number, { amount: number; key: number }>>({});
  const [vacationOpen, setVacationOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const nextToastId = useRef(1);
  const toastTimers = useRef(new Map<number, ReturnType<typeof setTimeout>>());
  const xpTimer = useRef(1);

  const dismissToast = useCallback((id: number) => {
    const timer = toastTimers.current.get(id);
    if (timer) clearTimeout(timer);
    toastTimers.current.delete(id);
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const pushToast = useCallback(
    (message: string, tone: ToastMessage["tone"] = "success") => {
      const id = nextToastId.current++;
      setToasts((current) => [...current, { id, message, tone }]);
      toastTimers.current.set(id, setTimeout(() => dismissToast(id), 4200));
    },
    [dismissToast],
  );

  useEffect(() => {
    const timers = toastTimers.current;
    return () => timers.forEach((timer) => clearTimeout(timer));
  }, []);

  const loadPlants = useCallback(async () => {
    try {
      const records = await getPlants(undefined, seasonOverride);
      setPlants(records);
      setLoadState("ready");
    } catch (error) {
      setLoadError(messageFrom(error));
      setLoadState("error");
    }
  }, [seasonOverride]);

  useEffect(() => {
    let active = true;

    getPlants(undefined, seasonOverride)
      .then((records) => {
        if (!active) return;
        setPlants(records);
        setLoadState("ready");
      })
      .catch((error: unknown) => {
        if (!active) return;
        setLoadError(messageFrom(error));
        setLoadState("error");
      });

    return () => {
      active = false;
    };
  }, [seasonOverride]);

  const rooms = useMemo(() => getRooms(plants), [plants]);
  const activeRoom = room === "All" || rooms.includes(room) ? room : "All";
  const visiblePlants = useMemo(
    () => queryPlants(plants, { room: activeRoom, search, sort, petSafety }),
    [activeRoom, petSafety, plants, search, sort],
  );

  async function handleSave(payload: PlantPayload) {
    setFormSaving(true);
    setFormError(null);
    try {
      if (formPlant === "new") {
        const created = await createPlant(payload, seasonOverride);
        setPlants((current) => [created, ...current]);
        setFormPlant(null);
        pushToast("Plant added successfully");
      } else if (formPlant) {
        const updated = await updatePlant(formPlant.id, payload, seasonOverride);
        setPlants((current) => current.map((plant) => (plant.id === updated.id ? updated : plant)));
        setFormPlant(null);
        pushToast(`${updated.nickname} was updated`);
      }
    } catch (error) {
      setFormError(messageFrom(error));
    } finally {
      setFormSaving(false);
    }
  }

  async function handleWater(plant: Plant) {
    setWateringIds((current) => new Set(current).add(plant.id));
    try {
      const updated = await waterPlant(plant.id, seasonOverride);
      const gain = Math.max(0, updated.xp - plant.xp);
      setPlants((current) => current.map((record) => (record.id === updated.id ? updated : record)));
      getCurrentUser().then(onUserChange).catch(() => undefined);
      const gainKey = xpTimer.current++;
      setXpGains((current) => ({ ...current, [plant.id]: { amount: gain, key: gainKey } }));
      setTimeout(() => {
        setXpGains((current) => {
          const next = { ...current };
          delete next[plant.id];
          return next;
        });
      }, 1400);
      pushToast(`${plant.nickname} was watered`);
    } catch (error) {
      pushToast(messageFrom(error), "error");
    } finally {
      setWateringIds((current) => {
        const next = new Set(current);
        next.delete(plant.id);
        return next;
      });
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await deletePlant(deleteTarget.id);
      setPlants((current) => current.filter((plant) => plant.id !== deleteTarget.id));
      setDeleteTarget(null);
      pushToast("Plant deleted");
    } catch (error) {
      setDeleteError(messageFrom(error));
    } finally {
      setDeleting(false);
    }
  }

  function clearFilters() {
    setSearch("");
    setRoom("All");
    setSort("risk-desc");
    setPetSafety("all");
  }

  async function handleProfileSave(payload: ProfilePayload) {
    setProfileSaving(true);
    setProfileError(null);
    try {
      const updated = await updateProfile(payload);
      onUserChange(updated);
      setProfileOpen(false);
      pushToast("Profile updated");
    } catch (error) {
      setProfileError(messageFrom(error));
    } finally {
      setProfileSaving(false);
    }
  }

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await onLogout();
    } catch (error) {
      pushToast(messageFrom(error), "error");
      setLoggingOut(false);
    }
  }

  return (
    <main className="mx-auto min-h-[100dvh] w-full max-w-[1440px] px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
      <DashboardHeader
        user={user}
        loggingOut={loggingOut}
        onProfile={() => {
          setProfileError(null);
          setProfileOpen(true);
        }}
        onLogout={() => void handleLogout()}
        onAdd={() => {
          setFormError(null);
          setFormPlant("new");
        }}
        onVacation={() => setVacationOpen(true)}
      />

      <div className="mt-8">
        {loadState === "loading" && <DashboardSkeleton />}
        {loadState === "error" && (
          <LoadError
            message={loadError}
            onRetry={() => {
              setLoadState("loading");
              setLoadError("");
              void loadPlants();
            }}
          />
        )}

        {loadState === "ready" && (
          <div className="space-y-8">
            {plants[0] && <SeasonBanner key={plants[0].season} season={plants[0].season} />}
            <SummaryGrid plants={plants} user={user} />
            <p className="-mt-6 text-xs text-[var(--text-soft)]">
              Pet info from ASPCA toxic-plant lists — not veterinary advice.
            </p>
            <NotificationSettings onNotify={pushToast} />

            {plants.length === 0 ? (
              <EmptyGarden onAdd={() => setFormPlant("new")} />
            ) : (
              <>
                <FilterToolbar
                  rooms={rooms}
                  selectedRoom={activeRoom}
                  onRoomChange={setRoom}
                  search={search}
                  onSearchChange={setSearch}
                  sort={sort}
                  onSortChange={setSort}
                  petSafety={petSafety}
                  onPetSafetyChange={setPetSafety}
                />

                {visiblePlants.length ? (
                  <section aria-label="Plant collection" className="grid items-stretch gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {visiblePlants.map((plant) => (
                      <PlantCard
                        key={plant.id}
                        plant={plant}
                        userPets={user.pets}
                        watering={wateringIds.has(plant.id)}
                        xpGain={xpGains[plant.id]}
                        onWater={(target) => void handleWater(target)}
                        onEdit={(target) => {
                          setFormError(null);
                          setFormPlant(target);
                        }}
                        onHistory={setHistoryPlant}
                        onDelete={(target) => {
                          setDeleteError(null);
                          setDeleteTarget(target);
                        }}
                      />
                    ))}
                  </section>
                ) : (
                  <NoResults onClear={clearFilters} />
                )}
              </>
            )}
          </div>
        )}
      </div>

      {formPlant && (
        <PlantFormDialog
          key={formPlant === "new" ? "new" : formPlant.id}
          plant={formPlant === "new" ? undefined : formPlant}
          saving={formSaving}
          error={formError}
          onSubmit={handleSave}
          onClose={() => {
            if (!formSaving) setFormPlant(null);
          }}
        />
      )}

      {deleteTarget && (
        <DeleteDialog
          key={deleteTarget.id}
          plant={deleteTarget}
          deleting={deleting}
          error={deleteError}
          onConfirm={() => void handleDelete()}
          onClose={() => {
            if (!deleting) setDeleteTarget(null);
          }}
        />
      )}

      {historyPlant && (
        <CareHistoryDialog
          key={historyPlant.id}
          plant={historyPlant}
          onClose={() => setHistoryPlant(null)}
          onRecorded={(event: CareEvent) => {
            if (event.action === "water") void loadPlants();
          }}
          onNotify={pushToast}
        />
      )}

      {vacationOpen && loadState === "ready" && (
        <VacationDialog
          key="vacation"
          plants={plants}
          onClose={() => setVacationOpen(false)}
          onNotify={pushToast}
        />
      )}

      {profileOpen && (
        <ProfileDialog
          user={user}
          saving={profileSaving}
          error={profileError}
          onSubmit={handleProfileSave}
          onClose={() => {
            if (!profileSaving) setProfileOpen(false);
          }}
        />
      )}

      <ToastViewport toasts={toasts} onDismiss={dismissToast} />
      <AccountAvatar user={user} />
      <SeasonSimulator
        value={seasonOverride}
        onChange={(season) => {
          setLoadState("loading");
          setSeasonOverride(season);
        }}
      />
    </main>
  );
}
