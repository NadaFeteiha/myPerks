"use client";

import { useAuth } from "@/contexts/auth-context";
import { MOCK_USER_PROFILE } from "@/data/mock/dashboard.mock";

export function HeroBanner() {
  const { user } = useAuth();

  return (
    <div className="mb-5 rounded-xl bg-gradient-to-br from-brand-purple-800 to-brand-purple-600 px-5 py-5">
      <p className="text-[18px] font-semibold tracking-tight text-white">
        Hello, {user?.name?.split(" ")[0] ?? "there"}
      </p>
      <p className="mt-0.5 text-[12px] text-white/65">
        {user?.role} · Joined {MOCK_USER_PROFILE.joinedDate} · Benefits year resets{" "}
        {MOCK_USER_PROFILE.benefitsYearReset}
      </p>
    </div>
  );
}
