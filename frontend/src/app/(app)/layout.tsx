import { LeftNav } from "@/components/layout/left-nav";
import { TopBar } from "@/components/layout/top-bar";

type AppLayoutProps = {
  children: React.ReactNode;
};

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex h-screen flex-col bg-white">
      <TopBar />
      <div className="flex min-h-0 flex-1">
        <LeftNav />
        <main className="flex min-h-0 flex-1 flex-col overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
