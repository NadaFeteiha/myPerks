"use client";

import { useUser } from "@clerk/nextjs";
import { createContext, useContext, useEffect, useState } from "react";

import { useApi } from "@/lib/api.client";

type AuthContextType = {
  isAuthenticated: boolean;
  user: null | User;
};

type User = {
  department: string;
  email: string;
  initials: string;
  name: string;
};

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { isSignedIn } = useUser();
  const api = useApi();
  const [user, setUser] = useState<null | User>(null);

  useEffect(() => {
    if (!isSignedIn) {
      void Promise.resolve().then(() => setUser(null));
      return;
    }

    api
      .getMe()
      .then((data) => {
        const name = data.name ?? "User";
        setUser({
          department: data.department ?? "",
          email: data.email ?? "",
          initials: getInitials(name),
          name,
        });
      })
      .catch((err: unknown) => {
        console.error("[MyPerks] Failed to load user profile:", err);
      });
  }, [isSignedIn]);

  return (
    <AuthContext.Provider value={{ isAuthenticated: !!isSignedIn, user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}
