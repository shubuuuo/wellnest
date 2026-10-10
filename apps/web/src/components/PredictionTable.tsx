"use client";

import { Fragment, useState } from "react";
import DownloadButton from "./DownloadButton";
import RiskBadge from "./RiskBadge";
import { fmtDateTime, pct } from "@/lib/format";
import type { AnyPrediction } from "@/lib/types";

export default function PredictionTable({
  items,
  reportPath,
  showUser = false,
  onOpenUser,
}: {
  items: AnyPrediction[];
  reportPath: (id: string) => string;
  showUser?: boolean;
  onOpenUser?: (userId: string, name: string, email: string) => void;
}) {
  const [open, setOpen] = useState<string | null>(null);
  const cols = showUser ? 6 : 5;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-muted">
          <tr>
            {[
              "Date",
              ...(showUser ? ["User"] : []),
              "Dataset",
              "Result",
              "Model",
              "",
            ].map((h, i) => (
              <th key={i} className="py-2 pr-4 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((p) => (
            <Fragment key={p.id}>
              <tr className="border-t border-line align-top">
                <td className="whitespace-nowrap py-2 pr-4">
                  {fmtDateTime(p.created_at)}
                </td>
                {showUser && (
                  <td className="py-2 pr-4">
                    {onOpenUser && p.user_id ? (
                      <button
                        className="text-left text-brand underline"
                        onClick={() =>
                          onOpenUser(
                            p.user_id!,
                            p.user_name ?? "",
                            p.user_email ?? "",
                          )
                        }
                      >
                        {p.user_name}
                      </button>
                    ) : (
                      p.user_name
                    )}
                    <div className="text-xs text-muted">{p.user_email}</div>
                  </td>
                )}
                <td className="py-2 pr-4">{p.dataset_label}</td>
                <td className="whitespace-nowrap py-2 pr-4">
                  <span className="mr-2 font-medium">{pct(p.probability)}</span>
                  <RiskBadge band={p.risk_band} />
                </td>
                <td className="py-2 pr-4 text-muted">{p.model_name}</td>
                <td className="whitespace-nowrap py-2">
                  <div className="flex flex-wrap items-start gap-2">
                    <button
                      className="rounded-md border border-line px-3 py-1.5 text-sm hover:border-brand"
                      aria-expanded={open === p.id}
                      onClick={() => setOpen(open === p.id ? null : p.id)}
                    >
                      {open === p.id ? "Hide answers" : "Answers"}
                    </button>
                    <DownloadButton
                      path={reportPath(p.id)}
                      filename={`wellnest-risk-report-${p.id.slice(0, 8)}.pdf`}
                      label="PDF"
                    />
                  </div>
                </td>
              </tr>
              {open === p.id && (
                <tr className="bg-bg">
                  <td colSpan={cols} className="px-3 py-3">
                    <dl className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2 lg:grid-cols-3">
                      {Object.entries(p.inputs).map(([k, v]) => (
                        <div
                          key={k}
                          className="flex justify-between gap-3 border-b border-line py-1"
                        >
                          <dt className="text-muted">{k}</dt>
                          <dd className="font-medium">{String(v)}</dd>
                        </div>
                      ))}
                    </dl>
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
