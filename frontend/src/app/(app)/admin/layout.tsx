import { redirect } from "next/navigation";

import { api } from "@/lib/api.server";

type Role = "employee" | "hr_admin";

/**
 * Server-side authorization guard for every /admin/* route.
 *
 * Role lives in the DB (not Clerk metadata), so this check can't happen in
 * proxy.ts — it runs here as a server component, where we have the auth token
 * and can read the employee's role from /employees/me. A non-admin (or anyone
 * whose record can't be loaded) is redirected before any admin page renders.
 *
 * proxy.ts already forces sign-in for non-public routes, so this adds the
 * authorization (role) layer on top of that authentication layer.
 */
export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  let role: Role | undefined;
  try {
    const me = await api.getMe();
    role = me.role;
  } catch {
    // Not signed in / no employee row — treat as not authorized.
    // (redirect() is called here, outside the try below, to avoid the
    // catch swallowing redirect()'s internal NEXT_REDIRECT signal.)
    redirect("/dashboard");
  }

  if (role !== "hr_admin") {
    redirect("/dashboard");
  }

  return <>{children}</>;
}
