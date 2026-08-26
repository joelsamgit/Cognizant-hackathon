"use client";

import { useEffect, useState } from "react";
import { Leaf, SpinnerGap } from "@phosphor-icons/react";

import { AuthScreen } from "@/components/auth/auth-screen";
import { PlantDashboard } from "@/components/dashboard/plant-dashboard";
import { getCurrentUser, logout } from "@/services/auth";
import { ApiError } from "@/services/plants";
import type { UserProfile } from "@/types/user";


type AccountState = "loading" | "signed-out" | "signed-in";

export function AccountGate() {
  const [state, setState] = useState<AccountState>("loading");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [initialError, setInitialError] = useState("");

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then((profile) => {
        if (!active) return;
        setUser(profile);
        setState("signed-in");
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (!(error instanceof ApiError) || error.status !== 401) {
          setInitialError(
            error instanceof ApiError
              ? error.message
              : "Plant Guardian could not check your session.",
          );
        }
        setState("signed-out");
      });
    return () => {
      active = false;
    };
  }, []);

  if (state === "loading") {
    return (
      <main className="grid min-h-[100dvh] place-items-center px-4" aria-busy="true">
        <div className="grid justify-items-center gap-4 text-[var(--text-muted)]">
          <div className="relative flex size-16 items-center justify-center rounded-3xl bg-[var(--accent-soft)] text-[var(--accent)]">
            <Leaf size={28} weight="fill" aria-hidden="true" />
            <SpinnerGap className="absolute -right-2 -top-2 animate-spin" size={22} aria-hidden="true" />
          </div>
          <p className="text-sm font-semibold">Opening your garden</p>
        </div>
      </main>
    );
  }

  if (state === "signed-out" || !user) {
    return (
      <AuthScreen
        initialError={initialError}
        onAuthenticated={(profile) => {
          setUser(profile);
          setInitialError("");
          setState("signed-in");
        }}
      />
    );
  }

  return (
    <PlantDashboard
      user={user}
      onUserChange={setUser}
      onLogout={async () => {
        await logout();
        setUser(null);
        setState("signed-out");
      }}
    />
  );
}
