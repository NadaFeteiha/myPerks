const STATUS_STYLES = new Map([
  ["approved", "bg-green-100 text-green-800"],
  ["cancelled", "bg-muted text-muted-foreground"],
  ["pending", "bg-yellow-100 text-yellow-800"],
  ["rejected", "bg-red-100 text-red-800"],
]);

export function StatusBadge({ status }: { status: string }) {
  const classes = STATUS_STYLES.get(status) ?? "bg-muted text-muted-foreground";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ${classes}`}
    >
      {status}
    </span>
  );
}
