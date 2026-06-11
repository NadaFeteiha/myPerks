"use client";

import { useAuth } from "@clerk/nextjs";
import { useMemo } from "react";

const BACKEND_PREFIX = "/api/backend";

export interface CreateRequestPayload {
  body: Record<string, unknown>;
  type: string;
}

export interface OnboardRequest {
  department?: string;
  email: string;
  name: string;
}

export interface OnboardResponse {
  benefits_year_reset: string;
  clerk_user_id: string;
  department: null | string;
  email: null | string;
  id: number;
  joined_date: string;
  name: null | string;
  role: "employee" | "hr_admin";
}

export interface RequestHistoryItem {
  body: null | string;
  created_at: string;
  id: number;
  status: string;
  type: string;
}

export function useApi() {
  const { getToken } = useAuth();

  return useMemo(() => {
    async function apiGet<T>(path: string): Promise<T> {
      const token = await getToken();
      const response = await fetch(`${BACKEND_PREFIX}${path}`, {
        cache: "no-store",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      return response.json() as Promise<T>;
    }

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
      createRequest: (payload: CreateRequestPayload) =>
        apiPost<RequestHistoryItem>("/me/requests", payload),
      getMe: () => apiGet<OnboardResponse>("/employees/me"),
      onboard: (body: OnboardRequest) =>
        apiPost<OnboardResponse>("/employees/me", body),
    };
  }, [getToken]);
}
