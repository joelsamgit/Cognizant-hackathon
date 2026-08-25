"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { DashboardSkeleton, EmptyGarden, LoadError, NoResults } from "@/components/dashboard/dashboard-states";
import { FilterToolbar } from "@/components/dashboard/filter-toolbar";
import { SummaryGrid } from "@/components/dashboard/summary-grid";
import { DeleteDialog } from "@/components/plants/delete-dialog";
import { PlantCard } from "@/components/plants/plant-card";
import { PlantFormDialog } from "@/components/plants/plant-form-dialog";
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
import type { Plant, PlantPayload, PlantSort } from "@/types/plant";


type LoadState = "loading" | "ready" | "error";

function messageFrom(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

export function PlantDashboard() {
  const [plants, setPlants] = useState<Plant[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState("");
  const [search, setSearch] = useState("");
  const [room, setRoom] = useState("All");
  const [sort, setSort] = useState<PlantSort>("risk-desc");
  const [formPlant, setFormPlant] = useState<Plant | "new" | null>(null);
  const [formSaving, setFormSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Plant | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [wateringIds, setWateringIds] = useState<Set<number>>(() => new Set());
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const nextToastId = useRef(1);
  const toastTimers = useRef(new Map<number, ReturnType<typeof setTimeout>>());

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
      const records = await getPlants();
      setPlants(records);
      setLoadState("ready");
    } catch (error) {
      setLoadError(messageFrom(error));
      setLoadState("error");
    }
  }, []);

  useEffect(() => {
    let active = true;

    getPlants()
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
  }, []);

  const rooms = useMemo(() => getRooms(plants), [plants]);
  const activeRoom = room === "All" || rooms.includes(room) ? room : "All";
  const visiblePlants = useMemo(
    () => queryPlants(plants, { room: activeRoom, search, sort }),
    [activeRoom, plants, search, sort],
  );

  async function handleSave(payload: PlantPayload) {
    setFormSaving(true);
    setFormError(null);
    try {
      if (formPlant === "new") {
        const created = await createPlant(payload);
        setPlants((current) => [created, ...current]);
        setFormPlant(null);
        pushToast("Plant added successfully");
      } else if (formPlant) {
        const updated = await updatePlant(formPlant.id, payload);
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
      const updated = await waterPlant(plant.id);
      setPlants((current) => current.map((record) => (record.id === updated.id ? updated : record)));
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
  }

  return (
    <main className="mx-auto min-h-[100dvh] w-full max-w-[1440px] px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
      <DashboardHeader
        onAdd={() => {
          setFormError(null);
          setFormPlant("new");
        }}
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
            <SummaryGrid plants={plants} />

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
                />

                {visiblePlants.length ? (
                  <section aria-label="Plant collection" className="grid items-stretch gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {visiblePlants.map((plant) => (
                      <PlantCard
                        key={plant.id}
                        plant={plant}
                        watering={wateringIds.has(plant.id)}
                        onWater={(target) => void handleWater(target)}
                        onEdit={(target) => {
                          setFormError(null);
                          setFormPlant(target);
                        }}
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

      <ToastViewport toasts={toasts} onDismiss={dismissToast} />
    </main>
  );
}
