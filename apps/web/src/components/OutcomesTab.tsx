"use client";

import { useState } from "react";
import Card from "./Card";
import Pager from "./Pager";
import RiskBadge from "./RiskBadge";
import { api, ApiError } from "@/lib/api";
import { fmtDateTime, pct } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { useLoad } from "@/lib/useLoad";
import type { DatasetInfo, OutcomeResult, OutcomeRow, Page } from "@/lib/types";

const PAGE_SIZE = 15;
const field = "rounded-md border border-line bg-surface px-2 py-1 text-sm";

export default function OutcomesTab() {
  const { data: datasets } = useApi<DatasetInfo[]>("/dataset");
  const [state, setState] = useState("pending");
  const [dataset, setDataset] = useState("");
  const [page, setPage] = useState(1);
  const [message, setMessage] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const params = new URLSearchParams({
    state,
    page: String(page),
    page_size: String(PAGE_SIZE),
  });
  if (dataset) params.set("dataset", dataset);
  const { data, error, reload } = useLoad<Page<OutcomeRow>>(
    `/admin/outcomes?${params}`,
  );

  async function confirm(row: OutcomeRow, cancer: boolean) {
    const text =
      `Confirm "${cancer ? "cancer present" : "no cancer"}" for ${row.user_name}'s ${row.dataset_label} check?\n\n` +
      "This cannot be changed afterwards.\n" +
      (row.training_consent
        ? "The user agreed, so it will join the learning pool and may update the models."
        : "The user did not agree to learning, so it will NOT be used to train anything.");
    if (!window.confirm(text)) return;
    setBusy(row.id);
    setProblem(null);
    setMessage(null);
    try {
      const r = await api.post<OutcomeResult>(
        `/admin/predictions/${row.id}/outcome`,
        { confirmed_cancer: cancer },
      );
      setMessage(
        "Outcome saved. " +
          (r.entered_pool
            ? "Added to the learning pool. "
            : "Not added to the pool (no consent). ") +
          (r.update
            ? `Models updated: ${r.update.accepted} of ${r.update.total} accepted the update. `
            : "") +
          (r.update_skipped ? `Update skipped: ${r.update_skipped}` : ""),
      );
      reload();
    } catch (e) {
      setProblem(
        e instanceof ApiError ? e.userMessage : "Could not save the outcome",
      );
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card title="Confirm real outcomes (simulated doctor verification)">
      <p className="mb-3 text-sm text-muted">
        A check only becomes training data after you confirm what the real
        result was and the user has agreed to learning. In a real product this
        step would be a doctor, not an administrator.
      </p>
      <div className="mb-3 flex flex-wrap gap-2">
        <select
          className={field}
          value={state}
          onChange={(e) => {
            setState(e.target.value);
            setPage(1);
          }}
        >
          <option value="pending">Waiting for an outcome</option>
          <option value="confirmed">Already confirmed</option>
          <option value="all">All</option>
        </select>
        <select
          className={field}
          value={dataset}
          onChange={(e) => {
            setDataset(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All datasets</option>
          {datasets?.map((d) => (
            <option key={d.id} value={d.id}>
              {d.label}
            </option>
          ))}
        </select>
      </div>
      {message && (
        <p role="status" className="mb-3 text-sm">
          {message}
        </p>
      )}
      {problem && (
        <p role="alert" className="mb-3 text-sm text-brand">
          {problem}
        </p>
      )}
      {error && <p className="text-sm text-brand">{error}</p>}
      {!data && !error && <p className="text-sm text-muted">Loading…</p>}
      {data && data.total === 0 && (
        <p className="text-sm text-muted">Nothing here.</p>
      )}
      {data && data.total > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-muted">
                <tr>
                  {[
                    "Date",
                    "User",
                    "Dataset",
                    "Model result",
                    "Real outcome",
                  ].map((h) => (
                    <th key={h} className="py-2 pr-4 font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((r) => (
                  <tr key={r.id} className="border-t border-line align-top">
                    <td className="whitespace-nowrap py-2 pr-4">
                      {fmtDateTime(r.created_at)}
                    </td>
                    <td className="py-2 pr-4">
                      {r.user_name}
                      <div className="text-xs text-muted">
                        {r.user_email} ·{" "}
                        {r.training_consent
                          ? "agreed to learning"
                          : "no learning consent"}
                      </div>
                    </td>
                    <td className="py-2 pr-4">{r.dataset_label}</td>
                    <td className="whitespace-nowrap py-2 pr-4">
                      <span className="mr-2 font-medium">
                        {pct(r.probability)}
                      </span>
                      <RiskBadge band={r.risk_band} />
                    </td>
                    <td className="py-2 pr-4">
                      {r.outcome ? (
                        <span>
                          {r.outcome.confirmed_cancer
                            ? "Cancer confirmed"
                            : "No cancer"}
                          <span className="block text-xs text-muted">
                            {r.outcome.entered_pool
                              ? "Added to learning pool"
                              : "Not used for learning"}
                          </span>
                        </span>
                      ) : (
                        <span className="flex flex-wrap gap-2">
                          <button
                            disabled={busy === r.id}
                            onClick={() => confirm(r, true)}
                            className="rounded border border-line px-2 py-1 text-xs hover:border-brand disabled:opacity-50"
                          >
                            Cancer confirmed
                          </button>
                          <button
                            disabled={busy === r.id}
                            onClick={() => confirm(r, false)}
                            className="rounded border border-line px-2 py-1 text-xs hover:border-brand disabled:opacity-50"
                          >
                            No cancer
                          </button>
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager
            page={page}
            pageSize={PAGE_SIZE}
            total={data.total}
            onChange={setPage}
          />
        </>
      )}
    </Card>
  );
}
