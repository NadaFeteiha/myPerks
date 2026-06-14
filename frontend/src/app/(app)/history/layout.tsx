import { redirectIfHrAdmin } from "@/lib/auth-guards";

export default async function HistoryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  await redirectIfHrAdmin();
  return <>{children}</>;
}
