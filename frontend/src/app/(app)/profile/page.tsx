"use client";

import { LogOut, User } from "lucide-react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/contexts/auth-context";

export default function ProfilePage() {
  const router = useRouter();
  const { logout, user } = useAuth();

  const handleLogout = () => {
    logout();
    router.push("/signin");
  };

  if (!user) {
    return null;
  }

  return (
    <div className="flex h-full items-center justify-center bg-background">
      <div className="w-full max-w-md rounded-lg border border-border bg-card p-8 shadow-sm">
        <div className="mb-6 flex flex-col items-center">
          <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full border-2 border-brand-purple-200 bg-brand-purple-50 text-2xl font-semibold text-brand-purple-800 dark:border-brand-purple-700 dark:bg-brand-purple-900/50 dark:text-brand-purple-300">
            {user.initials}
          </div>
          <h1 className="text-2xl font-semibold text-foreground">{user.name}</h1>
          <p className="text-muted-foreground">{user.role}</p>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-3 rounded-lg border border-border bg-background px-4 py-3">
            <User className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">Name</p>
              <p className="text-sm text-muted-foreground">{user.name}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-lg border border-border bg-background px-4 py-3">
            <User className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">Role</p>
              <p className="text-sm text-muted-foreground">{user.role}</p>
            </div>
          </div>

          <button
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-brand-purple-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-purple-700"
            onClick={handleLogout}
            type="button"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
