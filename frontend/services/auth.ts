import { request } from "./plants";
import type {
  LoginPayload,
  GoogleAuthPayload,
  ProfilePayload,
  SignupPayload,
  UserProfile,
} from "../types/user";


export function getCurrentUser(): Promise<UserProfile> {
  return request<UserProfile>("/auth/me");
}

export function signup(payload: SignupPayload): Promise<UserProfile> {
  return request<UserProfile>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function login(payload: LoginPayload): Promise<UserProfile> {
  return request<UserProfile>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function googleAuth(payload: GoogleAuthPayload): Promise<UserProfile> {
  return request<UserProfile>("/auth/google", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logout(): Promise<void> {
  return request<void>("/auth/logout", { method: "POST" });
}

export function updateProfile(payload: ProfilePayload): Promise<UserProfile> {
  return request<UserProfile>("/profile", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
