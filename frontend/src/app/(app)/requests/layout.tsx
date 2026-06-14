import { redirectIfHrAdmin } from "@/lib/auth-guards";

export default async function RequestsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  await redirectIfHrAdmin();
  return <>{children}</>;
}
