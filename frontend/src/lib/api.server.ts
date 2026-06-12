import { auth } from "@clerk/nextjs/server";

export interface AdminBalanceSnapshot {
  leave_type: string;
  remaining_days: number;
  total_days: number;
  used_days: number;
}

export interface AdminEmployeeDetail {
  balances: AdminBalanceSnapshot[];
  benefits_year_reset: string;
  department: string;
  email: string;
  id: number;
  joined_date: string;
  linked: boolean;
  name: string;
  request_history: AdminRequestHistorySnapshot[];
  role: string;
}

export interface AdminEmployeeListItem {
  department: string;
  email: string;
  id: number;
  joined_date: string;
  linked: boolean;
  name: string;
  role: string;
}

export interface AdminRequestHistorySnapshot {
  body: null | string;
  created_at: string;
  id: number;
  status: string;
  type: string;
}

export interface AdminRequestListItem {
  body: null | string;
  created_at: string;
  employee_id: number;
  employee_name: string;
  id: number;
  status: string;
  type: string;
}

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
  role: "employee" | "hr_admin";
}

export interface PaginatedAdminEmployees {
  items: AdminEmployeeListItem[];
  page: number;
  pages: number;
  size: number;
  total: number;
}

export interface PaginatedAdminRequests {
  items: AdminRequestListItem[];
  page: number;
  pages: number;
  size: number;
  total: number;
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

  const response = await fetch(`${getBackendPrefix()}${path}`, {
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
  const token = await getToken();
  if (!token) throw new Error("Not authenticated");
  return { Authorization: `Bearer ${token}` };
}

function getBackendPrefix(): string {
  if (typeof window !== "undefined") return "/api/backend";
  // Server components: call Render directly — avoids routing through the
  // Vercel proxy which re-runs Clerk middleware and drops the auth header.
  const directUrl = process.env.BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL;
  return directUrl ?? "http://localhost:8000";
}

export const api = {
  getAdminEmployeeDetail: (id: number) =>
    apiFetch<AdminEmployeeDetail>(`/admin/employees/${id}`),
  getAdminEmployees: (page = 1, size = 10, q?: string) => {
    const params = new URLSearchParams({
      page: String(page),
      size: String(size),
    });
    if (q) params.set("q", q);
    return apiFetch<PaginatedAdminEmployees>(`/admin/employees?${params}`);
  },
  getAdminRequests: (page = 1, size = 10, status = "pending") => {
    const params = new URLSearchParams({
      page: String(page),
      size: String(size),
      status_filter: status,
    });
    return apiFetch<PaginatedAdminRequests>(`/admin/requests?${params}`);
  },
  getBenefitsSummary: () =>
    apiFetch<BenefitsSummaryResponse>("/me/benefits-summary"),
  getMe: () => apiFetch<OnboardResponse>("/employees/me"),
  getRequestHistory: (page = 1, pageSize = 10) =>
    apiFetch<RequestHistoryResponse>(
      `/me/requests?page=${page}&page_size=${pageSize}`,
    ),
  getVacationBalance: () => apiFetch<VacationBalanceResponse>("/me/vacation"),
};
