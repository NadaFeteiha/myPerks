export function Pagination({
  makeHref,
  page,
  pageSize,
  total,
}: {
  makeHref: (page: number) => string;
  page: number;
  pageSize: number;
  total: number;
}) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  return (
    <div className="mt-4 flex items-center justify-between text-sm">
      <p className="text-muted-foreground">
        Page {page} of {totalPages}
      </p>
      <div className="flex gap-2">
        {page > 1 && (
          <a
            className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted"
            href={makeHref(page - 1)}
          >
            Previous
          </a>
        )}
        {page < totalPages && (
          <a
            className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted"
            href={makeHref(page + 1)}
          >
            Next
          </a>
        )}
      </div>
    </div>
  );
}
