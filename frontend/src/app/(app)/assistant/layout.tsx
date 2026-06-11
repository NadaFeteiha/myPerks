import { redirectIfHrAdmin } from "@/lib/auth-guards";

export default async function AssistantLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  await redirectIfHrAdmin();
  return <>{children}</>;
}
