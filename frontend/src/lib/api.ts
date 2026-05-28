// frontend/src/lib/api.ts

import { auth } from "@clerk/nextjs/server";

export interface BenefitsSummaryResponse {
  summary: BenefitSummaryItem[];
  year: number;
}

export interface BenefitSummaryItem {
  leave_type: string;
  percent_used: number;
  remaining_days: number;
  total_days: number;
  used_days: number;
}

export interface LeaveBalance {
  leave_type: string;
  remaining_days: number;
  total_days: number;
  used_days: number;
}

export interface RequestHistoryItem {
  body: null | string;
  created_at: string;
  id: number;
  status: string;
  type: string;
}

export interface RequestHistoryResponse {
  items: RequestHistoryItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface VacationBalanceResponse {
  balances: LeaveBalance[];
  year: number;
}

export const api = {
  getBenefitsSummary: () =>
    apiFetch<BenefitsSummaryResponse>("/me/benefits-summary"),

  getRequestHistory: (page = 1, pageSize = 10) =>
    apiFetch<RequestHistoryResponse>(
      `/me/requests?page=${page}&page_size=${pageSize}`,
    ),

  getVacationBalance: () => apiFetch<VacationBalanceResponse>("/me/vacation"),
};

async function apiFetch<T>(path: string): Promise<T> {
  const headers = await getAuthHeader();

  const response = await fetch(`${getBackendPrefix()}${path}`, {
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

async function getAuthHeader(): Promise<{ Authorization: string }> {
  const { getToken } = await auth();
  const token = await getToken();
  return { Authorization: `Bearer ${token}` };
}

function getBackendPrefix(): string {
  if (typeof window !== "undefined") return "/api/backend";
  // Server components: call Render directly — avoids routing through the
  // Vercel proxy which re-runs Clerk middleware and drops the auth header.
  const directUrl =
    process.env.BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL;
  return directUrl ?? "http://localhost:8000";
}
