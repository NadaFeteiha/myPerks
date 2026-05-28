"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useApi } from "@/lib/api.client";

export default function OnboardingPage() {
  const router = useRouter();
  const api = useApi();
  const [name, setName] = useState("");
  const [department, setDepartment] = useState("");
  const [error, setError] = useState<null | string>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await api.onboard({
        department: department || undefined,
        name,
      });
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-md space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Welcome to MyPerks</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Tell us a bit about yourself to get started.
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="name">
              Full name
            </label>
            <input
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              id="name"
              onChange={(e) => setName(e.target.value)}
              placeholder="Alice Johnson"
              required
              type="text"
              value={name}
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="department">
              Department
              <span className="ml-1 text-muted-foreground">(optional)</span>
            </label>
            <input
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              id="department"
              onChange={(e) => setDepartment(e.target.value)}
              placeholder="Engineering"
              type="text"
              value={department}
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <button
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            disabled={loading}
            type="submit"
          >
            {loading ? "Setting up your account..." : "Get started"}
          </button>
        </form>
      </div>
    </div>
  );
}
