import { Clock, Leaf, Plane } from "lucide-react";

type ChipProps = {
  icon: React.ReactNode;
  label: string;
};

function Chip({ icon, label }: ChipProps) {
  return (
    <span className="flex items-center gap-1 rounded-full border border-white/20 bg-white/[0.12] px-2.5 py-1 text-[11px] font-medium text-white/90">
      {icon}
      {label}
    </span>
  );
}

export function HeroBanner() {
  return (
    <div
      className="mb-5 rounded-xl px-5 py-5"
      style={{ background: "linear-gradient(110deg, #3C3489 0%, #534AB7 100%)" }}
    >
      <p className="text-[18px] font-semibold tracking-tight text-white">
        Hello, Sarah
      </p>
      <p className="mt-0.5 text-[12px] text-white/65">
        Engineering · Joined Jan 2023 · Benefits year resets Jan 1
      </p>
    </div>
  );
}
