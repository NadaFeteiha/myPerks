import { redirectIfHrAdmin } from "@/lib/auth-guards";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  await redirectIfHrAdmin();
  return <>{children}</>;
}
