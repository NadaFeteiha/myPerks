import { redirect } from "next/navigation";

import { api } from "@/lib/api.server";

/**
 * HR admins manage employees from /admin/* — redirect them away from the
 * employee-facing dashboard/assistant/history/requests pages.
 */
export async function redirectIfHrAdmin(): Promise<void> {
  let role: "employee" | "hr_admin" | undefined;
  try {
    role = (await api.getMe()).role;
  } catch {
    return;
  }

  if (role === "hr_admin") redirect("/admin");
}
