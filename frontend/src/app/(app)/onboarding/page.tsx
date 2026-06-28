"use client";

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useApi } from "@/lib/api.client";

type LinkStatus = "error" | "linking" | "not_provisioned";

export default function OnboardingPage() {
  const router = useRouter();
  const api = useApi();
  const { isLoaded, user } = useUser();
  const [status, setStatus] = useState<LinkStatus>("linking");
  const attempted = useRef(false);

  useEffect(() => {
    if (!isLoaded || attempted.current) {
      return;
    }
    const email = user?.primaryEmailAddress?.emailAddress;
    if (!email) {
      return;
    }
    attempted.current = true;

    async function link(address: string) {
      try {
        await api.onboard({ email: address });
        router.replace("/dashboard");
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "";
        setStatus(message.includes("403") ? "not_provisioned" : "error");
      }
    }

    void link(email);
  }, [api, isLoaded, router, user]);

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-md space-y-3 text-center">
        {status === "linking" && (
          <>
            <h1 className="text-2xl font-semibold">Setting up your account</h1>
            <p className="text-sm text-muted-foreground">
              Linking your MyPerks profile, one moment.
            </p>
          </>
        )}
        {status === "not_provisioned" && (
          <>
            <h1 className="text-2xl font-semibold">Account not set up yet</h1>
            <p className="text-sm text-muted-foreground">
              We could not find a MyPerks record for your email. Please contact
              your HR admin to be added, then sign in again.
            </p>
          </>
        )}
        {status === "error" && (
          <>
            <h1 className="text-2xl font-semibold">Something went wrong</h1>
            <p className="text-sm text-muted-foreground">
              We could not link your account. Please try again, or contact your
              HR admin if this keeps happening.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
