export function formatDepartment(department: string): string {
  if (department.toLowerCase() === "hr") return "HR";
  return department.charAt(0).toUpperCase() + department.slice(1);
}

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

export function formatRequestType(type: string): string {
  if (type.toLowerCase() === "pto") return "PTO";
  return type.charAt(0).toUpperCase() + type.slice(1);
}

/**
 * For leave requests, return "Jun 6 – Jun 12, 2026" using start/end from body.
 * For reimbursements (no start_date), fall back to the submission date.
 */
export function getRequestDate(item: {
  body: null | string;
  created_at: string;
}): string {
  if (item.body) {
    try {
      const parsed = JSON.parse(item.body) as Record<string, unknown>;
      if (typeof parsed.start_date === "string") {
        const start = formatIsoDate(parsed.start_date);
        if (typeof parsed.end_date === "string") {
          const end = formatIsoDate(parsed.end_date);
          return start === end ? start : `${start} – ${end}`;
        }
        return start;
      }
    } catch {
      // fall through
    }
  }
  return formatIsoDate(item.created_at);
}

export function getRequestDescription(body: null | string): string {
  if (!body) return "—";
  try {
    const parsed = JSON.parse(body) as Record<string, unknown>;
    const text = parsed.reason ?? parsed.description;
    return typeof text === "string" ? text : "—";
  } catch {
    return "—";
  }
}
