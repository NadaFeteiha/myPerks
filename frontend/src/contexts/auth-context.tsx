"use client";

import { useUser } from "@clerk/nextjs";
import { createContext, useContext } from "react";

type AuthContextType = {
  isAuthenticated: boolean;
  user: null | User;
};

type User = {
  email: string;
  initials: string;
  name: string;
  role: string;
};

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { isSignedIn, user: clerkUser } = useUser();

  const user: null | User = clerkUser
    ? {
        email: clerkUser.primaryEmailAddress?.emailAddress ?? "",
        initials: getInitials(
          clerkUser.fullName ?? clerkUser.firstName ?? "U",
        ),
        name: clerkUser.fullName ?? clerkUser.firstName ?? "User",
        role: (clerkUser.publicMetadata?.role as string) ?? "",
      }
    : null;

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
