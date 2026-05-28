import { auth } from "@clerk/nextjs/server";

const BACKEND_PREFIX =
  typeof window === "undefined"
    ? `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}`
    : "/api/backend";

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

export interface OnboardResponse {
  clerk_user_id: string;
  department: null | string;
  email: null | string;
  id: number;
  name: null | string;
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

async function apiFetch<T>(path: string): Promise<T> {
  const headers = await getAuthHeader();
  const response = await fetch(`${BACKEND_PREFIX}${path}`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...headers },
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

async function getAuthHeader(): Promise<{ Authorization: string }> {
  const { getToken } = await auth();
  const token = await getToken({ template: "myperks-dev" });
  return { Authorization: `Bearer ${token}` };
}

export const api = {
  getBenefitsSummary: () =>
    apiFetch<BenefitsSummaryResponse>("/me/benefits-summary"),
  getMe: () => apiFetch<OnboardResponse>("/employees/me"),
  getRequestHistory: (page = 1, pageSize = 10) =>
    apiFetch<RequestHistoryResponse>(
      `/me/requests?page=${page}&page_size=${pageSize}`,
    ),
  getVacationBalance: () => apiFetch<VacationBalanceResponse>("/me/vacation"),
};
