"use client";

import { Briefcase, Mail, User } from "lucide-react";

import { useAuth } from "@/contexts/auth-context";

export default function ProfilePage() {
  const { user } = useAuth();

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
            <Mail className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">Email</p>
              <p className="text-sm text-muted-foreground">{user.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-lg border border-border bg-background px-4 py-3">
            <Briefcase className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium text-foreground">Role</p>
              <p className="text-sm text-muted-foreground">{user.role}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
