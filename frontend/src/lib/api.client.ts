"use client";

import { useAuth } from "@clerk/nextjs";

const BACKEND_PREFIX = "/api/backend";

export interface OnboardRequest {
  department?: string;
  email: string;
  name: string;
}

export interface OnboardResponse {
  clerk_user_id: string;
  department: null | string;
  email: null | string;
  id: number;
  name: null | string;
}

export function useApi() {
  const { getToken } = useAuth();

  async function apiPost<T>(path: string, body: unknown): Promise<T> {
    const token = await getToken();
    const response = await fetch(`${BACKEND_PREFIX}${path}`, {
      body: JSON.stringify(body),
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      method: "POST",
    });
    if (!response.ok) {
      const detail = await response
        .json()
        .then((j: { detail?: string }) => j.detail)
        .catch(() => undefined);
      throw new Error(
        `API error: ${response.status}${detail ? ` – ${detail}` : ` ${response.statusText}`}`,
      );
    }
    return response.json() as Promise<T>;
  }

  return {
    onboard: (body: OnboardRequest) =>
      apiPost<OnboardResponse>("/employees/me", body),
  };
}
