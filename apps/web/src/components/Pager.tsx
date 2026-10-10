export default function Pager({
  page,
  pageSize,
  total,
  onChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="mt-3 flex items-center gap-3 text-sm">
      <button
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        className="rounded border border-line px-3 py-1 disabled:opacity-50"
      >
        Previous
      </button>
      <span className="text-muted">
        Page {page} of {pages} ({total} total)
      </span>
      <button
        disabled={page >= pages}
        onClick={() => onChange(page + 1)}
        className="rounded border border-line px-3 py-1 disabled:opacity-50"
      >
        Next
      </button>
    </div>
  );
}
