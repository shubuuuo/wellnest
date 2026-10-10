"use client";

import { useState } from "react";
import Card from "./Card";
import Pager from "./Pager";
import { api, ApiError } from "@/lib/api";
import { fmtDateTime } from "@/lib/format";
import { useLoad } from "@/lib/useLoad";
import type { LoopEvent, LoopStatus, Page } from "@/lib/types";

const NOTICE =
  "Online learning is enabled for course demonstration. It is not recommended for real clinical deployment, " +
  "because one wrong or malicious label can quietly damage a model. That is why every update is checked against a " +
  "frozen test set and can be rolled back.";
const KIND: Record<string, string> = {
  online_update: "Online update",
  batch_retrain: "Batch retrain",
  rollback: "Rollback",
  reset: "Reset",
};
const f3 = (n?: number | null) => (typeof n === "number" ? n.toFixed(3) : "—");

function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
      {hint && <p className="text-xs text-muted">{hint}</p>}
    </div>
  );
}

function EventRow({ e }: { e: LoopEvent }) {
  const [open, setOpen] = useState(false);
  const d = e.details;
  const accepted = d.models?.filter((m) => m.accepted).length ?? 0;
  const summary =
    e.kind === "online_update"
      ? `${accepted} of ${d.models?.length ?? 0} models accepted the update (${e.n_records} record${e.n_records === 1 ? "" : "s"})`
      : e.kind === "batch_retrain"
        ? `${d.model}: F1 ${f3(d.before?.f1)} → ${f3(d.after?.f1)} using ${e.n_records} pool records (not deployed)`
        : e.kind === "rollback"
          ? `Reverted ${d.reverted?.length ?? 0} model(s) to their previous version`
          : (d.reason ?? "");
  return (
    <li className="rounded-md border border-line p-3 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p>
          <span className="font-medium">{KIND[e.kind] ?? e.kind}</span>
          {e.status === "rolled_back" && (
            <span className="ml-2 rounded bg-line px-2 py-0.5 text-xs">
              rolled back
            </span>
          )}
          <span className="ml-2 text-muted">
            {fmtDateTime(e.created_at)}
            {e.actor_name ? ` · ${e.actor_name}` : ""}
          </span>
        </p>
        <button
          className="text-xs underline"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
        >
          {open ? "Hide details" : "Details"}
        </button>
      </div>
      <p className="mt-1">{summary}</p>
      {open && (
        <div className="mt-2 space-y-1 border-t border-line pt-2">
          {d.models?.map((m) => (
            <p key={m.model}>
              <span className="font-medium">{m.model}:</span>{" "}
              {m.accepted
                ? `accepted, now v${m.version} (F1 ${f3(m.before?.f1)} → ${f3(m.after?.f1)}, recall ${f3(m.before?.recall)} → ${f3(m.after?.recall)})`
                : (m.reason ?? "not accepted")}
            </p>
          ))}
          {d.reverted?.map((m) => (
            <p key={m.model}>
              <span className="font-medium">{m.model}:</span> v{m.from_version}{" "}
              → v{m.to_version}
            </p>
          ))}
          {d.note && <p className="text-muted">{d.note}</p>}
          {d.fit_seconds !== undefined && (
            <p className="text-muted">Training took {d.fit_seconds}s.</p>
          )}
          {d.fingerprint && (
            <p className="text-xs text-muted">
              Frozen test set fingerprint: {d.fingerprint}
            </p>
          )}
        </div>
      )}
    </li>
  );
}

export default function LiveLearningTab({ dataset }: { dataset: string }) {
  const [page, setPage] = useState(1);
  const status = useLoad<LoopStatus>(
    `/admin/learning/status?dataset=${dataset}`,
  );
  const events = useLoad<Page<LoopEvent>>(
    `/admin/learning/events?dataset=${dataset}&page=${page}&page_size=8`,
  );
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  async function run(
    key: string,
    call: () => Promise<LoopEvent>,
    done: (e: LoopEvent) => string,
  ) {
    setBusy(key);
    setMessage(null);
    setProblem(null);
    try {
      setMessage(done(await call()));
      status.reload();
      events.reload();
    } catch (e) {
      setProblem(
        e instanceof ApiError ? e.userMessage : "Something went wrong",
      );
    } finally {
      setBusy(null);
    }
  }

  const s = status.data;
  if (status.error) return <p className="text-sm text-brand">{status.error}</p>;
  if (!s) return <p className="text-sm text-muted">Loading…</p>;
  const q = `?dataset=${dataset}`;

  return (
    <div className="space-y-6">
      <div
        role="note"
        className="rounded-lg border border-line bg-brand-soft p-3 text-sm"
      >
        <strong>Course demonstration.</strong> {NOTICE}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Stat
          label="Records waiting"
          value={s.pool.waiting}
          hint={`auto-update at ${s.batch_size}`}
        />
        <Stat
          label="Records in pool"
          value={s.pool.total}
          hint={`${s.pool.positive} cancer · ${s.pool.negative} no cancer`}
        />
        <Stat
          label="Live model"
          value={s.live ? `${s.live.name} v${s.live.version}` : "—"}
        />
        <Stat
          label="Online learning"
          value={s.online_enabled ? "ON" : "OFF"}
          hint={`guard tolerance ${s.tolerance}`}
        />
        <Stat
          label="Test set fingerprint"
          value={s.fingerprint}
          hint="must never change"
        />
      </div>

      <Card title="Actions">
        <div className="flex flex-wrap gap-3">
          <button
            disabled={
              busy !== null || s.pool.waiting === 0 || !s.online_enabled
            }
            onClick={() =>
              run(
                "update",
                () => api.post<LoopEvent>(`/admin/learning/update${q}`),
                (e) =>
                  `Updated with ${e.n_records} record(s): ${e.details.models?.filter((m) => m.accepted).length ?? 0} of ${e.details.models?.length ?? 0} models accepted.`,
              )
            }
            className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy === "update" ? "Updating…" : "Update models now"}
          </button>
          <button
            disabled={busy !== null || !s.can_roll_back}
            onClick={() =>
              run(
                "rollback",
                () => api.post<LoopEvent>(`/admin/learning/rollback${q}`),
                () => "Rolled back the latest update.",
              )
            }
            className="rounded-md border border-line px-4 py-2 text-sm hover:border-brand disabled:opacity-50"
          >
            {busy === "rollback" ? "Rolling back…" : "Roll back last update"}
          </button>
        </div>
        {message && (
          <p role="status" className="mt-3 text-sm">
            {message}
          </p>
        )}
        {problem && (
          <p role="alert" className="mt-3 text-sm text-brand">
            {problem}
          </p>
        )}
      </Card>

      <Card title="Online models (can learn from each new record)">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-muted">
              <tr>
                {["Model", "Version", "F1", "Recall", "Accuracy", ""].map(
                  (h) => (
                    <th key={h} className="py-2 pr-4 font-medium">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {s.online_models.map((m) => (
                <tr key={m.name} className="border-t border-line">
                  <td className="py-2 pr-4 font-medium">{m.name}</td>
                  <td className="py-2 pr-4">v{m.version}</td>
                  <td className="py-2 pr-4">{f3(m.metrics.f1)}</td>
                  <td className="py-2 pr-4">{f3(m.metrics.recall)}</td>
                  <td className="py-2 pr-4">{f3(m.metrics.accuracy)}</td>
                  <td className="py-2 pr-4">
                    {m.is_live && (
                      <span className="rounded bg-brand-soft px-2 py-0.5 text-xs text-brand">
                        answers users
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-muted">
          Scores are on the frozen test set, which no update ever trains on.
        </p>
      </Card>

      <Card title="Batch-only models (cannot update online)">
        <p className="mb-3 text-sm text-muted">
          Random Forest and kernel SVM cannot learn from a few new records. They
          must be retrained from scratch on all data. The result is shown for
          comparison and is not served to users.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-muted">
              <tr>
                {[
                  "Model",
                  "Online update",
                  "Base F1",
                  "After batch retrain (F1 / recall)",
                  "",
                ].map((h) => (
                  <th key={h} className="py-2 pr-4 font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {s.batch_models.map((m) => (
                <tr key={m.name} className="border-t border-line align-top">
                  <td className="py-2 pr-4 font-medium">{m.name}</td>
                  <td className="py-2 pr-4">Not supported</td>
                  <td className="py-2 pr-4">{f3(m.baseline.f1)}</td>
                  <td className="py-2 pr-4">
                    {m.latest?.after
                      ? `${f3(m.latest.after.f1)} / ${f3(m.latest.after.recall)} (${m.latest_records} pool records, ${fmtDateTime(m.latest_at)})`
                      : "not run yet"}
                  </td>
                  <td className="py-2 pr-4">
                    <button
                      disabled={busy !== null || s.pool.total === 0}
                      onClick={() =>
                        run(
                          m.name,
                          () =>
                            api.post<LoopEvent>(
                              `/admin/learning/batch-retrain${q}`,
                              { name: m.name },
                            ),
                          () =>
                            `${m.name} was retrained from scratch. Scores are shown for comparison.`,
                        )
                      }
                      className="rounded border border-line px-2 py-1 text-xs hover:border-brand disabled:opacity-50"
                    >
                      {busy === m.name
                        ? "Retraining…"
                        : "Retrain with pool data"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Learning history">
        {events.error && <p className="text-sm text-brand">{events.error}</p>}
        {events.data && events.data.total === 0 && (
          <p className="text-sm text-muted">
            No learning events yet. Confirm an outcome in the Outcomes tab to
            start.
          </p>
        )}
        <ul className="space-y-2">
          {events.data?.items.map((e) => (
            <EventRow key={e.id} e={e} />
          ))}
        </ul>
        {events.data && events.data.total > 0 && (
          <Pager
            page={page}
            pageSize={8}
            total={events.data.total}
            onChange={setPage}
          />
        )}
      </Card>
    </div>
  );
}
