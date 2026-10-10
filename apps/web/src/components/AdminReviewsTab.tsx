"use client";

import { useState } from "react";
import Card from "./Card";
import Pager from "./Pager";
import { api, ApiError } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { useLoad } from "@/lib/useLoad";
import type { ReviewPage } from "@/lib/types";

const PAGE_SIZE = 20;

export default function AdminReviewsTab() {
  const [rating, setRating] = useState("");
  const [page, setPage] = useState(1);
  const [problem, setProblem] = useState<string | null>(null);

  const params = new URLSearchParams({
    page: String(page),
    page_size: String(PAGE_SIZE),
  });
  if (rating) params.set("rating", rating);
  const { data, error, reload } = useLoad<ReviewPage>(
    `/admin/reviews?${params}`,
  );

  async function remove(id: string) {
    if (!window.confirm("Remove this review permanently?")) return;
    try {
      await api.delete(`/admin/reviews/${id}`);
      setProblem(null);
      reload();
    } catch (e) {
      setProblem(
        e instanceof ApiError ? e.userMessage : "Could not remove the review",
      );
    }
  }

  if (error) return <p className="text-sm text-brand">{error}</p>;
  if (!data) return <p className="text-sm text-muted">Loading…</p>;
  const s = data.summary;
  const max = Math.max(1, ...Object.values(s.distribution));

  return (
    <div className="space-y-6">
      <Card title="Rating summary">
        <div className="grid gap-6 sm:grid-cols-[10rem_1fr]">
          <div>
            <p className="text-3xl font-semibold">
              {s.average ? s.average.toFixed(1) : "—"}
            </p>
            <p className="text-sm text-muted">
              {s.count} review{s.count === 1 ? "" : "s"}
            </p>
          </div>
          <div className="space-y-1">
            {[5, 4, 3, 2, 1].map((n) => (
              <div key={n} className="flex items-center gap-2 text-sm">
                <span className="w-8">{n}★</span>
                <div className="h-2 flex-1 rounded bg-line">
                  <div
                    className="h-2 rounded bg-brand"
                    style={{
                      width: `${((s.distribution[String(n)] ?? 0) / max) * 100}%`,
                    }}
                  />
                </div>
                <span className="w-6 text-right text-muted">
                  {s.distribution[String(n)] ?? 0}
                </span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card title="All reviews">
        <label className="mb-3 block text-sm">
          Show{" "}
          <select
            className="rounded-md border border-line bg-surface px-2 py-1"
            value={rating}
            onChange={(e) => {
              setRating(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All ratings</option>
            {[5, 4, 3, 2, 1].map((n) => (
              <option key={n} value={n}>
                {n} stars
              </option>
            ))}
          </select>
        </label>
        {problem && (
          <p role="alert" className="mb-3 text-sm text-brand">
            {problem}
          </p>
        )}
        {data.total === 0 && (
          <p className="text-sm text-muted">No reviews yet.</p>
        )}
        <ul className="space-y-3">
          {data.items.map((r) => (
            <li key={r.id} className="rounded-md border border-line p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm">
                  <span
                    className="font-medium text-brand"
                    aria-label={`${r.rating} out of 5`}
                  >
                    {"★".repeat(r.rating)}
                    {"☆".repeat(5 - r.rating)}
                  </span>{" "}
                  <span className="font-medium">{r.user_name}</span>{" "}
                  <span className="text-muted">
                    ({r.user_email}), {fmtDate(r.updated_at)}
                  </span>
                </p>
                <button
                  onClick={() => remove(r.id)}
                  className="rounded border border-line px-2 py-0.5 text-xs hover:border-brand"
                >
                  Remove
                </button>
              </div>
              {r.comment && <p className="mt-2 text-sm">{r.comment}</p>}
            </li>
          ))}
        </ul>
        {data.total > 0 && (
          <Pager
            page={page}
            pageSize={PAGE_SIZE}
            total={data.total}
            onChange={setPage}
          />
        )}
      </Card>
    </div>
  );
}
