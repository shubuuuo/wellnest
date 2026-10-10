"use client";

import { useEffect, useState } from "react";
import Card from "./Card";
import Pager from "./Pager";
import { fmtDateTime } from "@/lib/format";
import { useLoad } from "@/lib/useLoad";
import type { ActivityPage } from "@/lib/types";

const PAGE_SIZE = 25;
const field = "rounded-md border border-line bg-surface px-2 py-1 text-sm";

const LABEL: Record<string, string> = {
  register: "Signed up",
  login: "Logged in",
  prediction_created: "Ran a risk check",
  report_downloaded: "Downloaded a report",
  review_created: "Left a review",
  review_updated: "Updated a review",
  review_deleted: "Review removed (admin)",
  role_changed: "Role changed (admin)",
  account_activated: "Account restored (admin)",
  account_deactivated: "Account deactivated (admin)",
  outcome_confirmed: "Outcome confirmed (admin)",
  online_update: "Models updated (admin)",
  online_rollback: "Update rolled back (admin)",
  batch_retrain: "Batch retrain (admin)",
  training_consent_granted: "Allowed learning use",
  training_consent_withdrawn: "Withdrew learning use",
};

export default function ActivityTab() {
  const [typed, setTyped] = useState("");
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const t = setTimeout(() => setSearch(typed.trim()), 300);
    return () => clearTimeout(t);
  }, [typed]);

  const params = new URLSearchParams({
    page: String(page),
    page_size: String(PAGE_SIZE),
  });
  if (search) params.set("search", search);
  if (action) params.set("action", action);
  const { data, error } = useLoad<ActivityPage>(`/admin/activity?${params}`);

  return (
    <Card title="Activity log">
      <div className="mb-3 flex flex-wrap gap-2">
        <input
          className={field}
          placeholder="Search user name or email"
          value={typed}
          onChange={(e) => {
            setTyped(e.target.value);
            setPage(1);
          }}
        />
        <select
          className={field}
          value={action}
          onChange={(e) => {
            setAction(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All actions</option>
          {data?.actions.map((a) => (
            <option key={a} value={a}>
              {LABEL[a] ?? a}
            </option>
          ))}
        </select>
      </div>
      {error && <p className="text-sm text-brand">{error}</p>}
      {!data && !error && <p className="text-sm text-muted">Loading…</p>}
      {data && data.total === 0 && (
        <p className="text-sm text-muted">No activity yet.</p>
      )}
      {data && data.total > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-muted">
                <tr>
                  {["When", "Who", "Action", "Details"].map((h) => (
                    <th key={h} className="py-2 pr-4 font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((a) => (
                  <tr key={a.id} className="border-t border-line align-top">
                    <td className="whitespace-nowrap py-2 pr-4">
                      {fmtDateTime(a.created_at)}
                    </td>
                    <td className="py-2 pr-4">
                      {a.actor_name ?? "Deleted user"}
                      <div className="text-xs text-muted">{a.actor_email}</div>
                    </td>
                    <td className="py-2 pr-4">{LABEL[a.action] ?? a.action}</td>
                    <td className="py-2 pr-4 text-muted">
                      {Object.entries(a.details)
                        .map(([k, v]) => `${k}: ${String(v)}`)
                        .join(", ") || "—"}
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
