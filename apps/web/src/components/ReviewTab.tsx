"use client";

import { useState } from "react";
import Card from "./Card";
import { api, ApiError } from "@/lib/api";
import { useLoad } from "@/lib/useLoad";
import type { MyReviewResponse, ReviewData } from "@/lib/types";
import TrainingConsentCard from "./TrainingConsentCard";

function ReviewForm({ initial }: { initial: ReviewData | null }) {
  const [rating, setRating] = useState(initial?.rating ?? 0);
  const [comment, setComment] = useState(initial?.comment ?? "");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  async function save() {
    setMessage(null);
    if (!rating) return setProblem("Please choose a star rating first.");
    setBusy(true);
    setProblem(null);
    try {
      await api.put<MyReviewResponse>("/me/review", { rating, comment });
      setMessage("Thank you! Your feedback was saved.");
    } catch (e) {
      setProblem(
        e instanceof ApiError ? e.userMessage : "Something went wrong",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <p id="rating-label" className="mb-1 text-sm text-muted">
          How useful was WellNest?
        </p>
        <div
          role="radiogroup"
          aria-labelledby="rating-label"
          className="flex gap-1"
        >
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              role="radio"
              aria-checked={rating === n}
              aria-label={`${n} star${n > 1 ? "s" : ""}`}
              onClick={() => setRating(n)}
              className={`text-3xl leading-none ${n <= rating ? "text-brand" : "text-line"}`}
            >
              ★
            </button>
          ))}
        </div>
      </div>
      <label className="block text-sm">
        <span className="mb-1 block text-muted">Comments (optional)</span>
        <textarea
          className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm"
          rows={4}
          maxLength={1000}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </label>
      <button
        onClick={save}
        disabled={busy}
        className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {busy ? "Saving…" : initial ? "Update feedback" : "Send feedback"}
      </button>
      {message && (
        <p role="status" className="text-sm">
          {message}
        </p>
      )}
      {problem && (
        <p role="alert" className="text-sm text-brand">
          {problem}
        </p>
      )}
    </div>
  );
}

// export default function ReviewTab() {
//   const { data, error } = useLoad<MyReviewResponse>("/me/review");
//   return (
//     <div className="max-w-xl">
//       <Card title="Rate your experience">
//         {error && <p className="text-sm text-brand">{error}</p>}
//         {!data && !error && <p className="text-sm text-muted">Loading…</p>}
//         {data && <ReviewForm initial={data.review} />}
//       </Card>
//     </div>
//   );
// }

export default function ReviewTab() {
  const { data, error } = useLoad<MyReviewResponse>("/me/review");
  return (
    <div className="max-w-xl space-y-6">
      <TrainingConsentCard />
      <Card title="Rate your experience">
        {error && <p className="text-sm text-brand">{error}</p>}
        {!data && !error && <p className="text-sm text-muted">Loading…</p>}
        {data && <ReviewForm initial={data.review} />}
      </Card>
    </div>
  );
}
