/**
 * Parse a YYYY-MM-DD (or ISO datetime) string as a local date and format it.
 * Avoids the UTC-midnight-to-previous-day shift that `new Date(iso)` causes.
 */
export function formatIsoDate(iso: string): string {
  const [year, month, day] = iso.split("T")[0].split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
