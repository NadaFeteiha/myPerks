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
