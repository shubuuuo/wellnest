"use client";

import Card from "./Card";
import DownloadButton from "./DownloadButton";
import RiskBadge from "./RiskBadge";
import TimelineChart from "./TimelineChart";
import { fmtDate, pct } from "@/lib/format";
import { useLoad } from "@/lib/useLoad";
import type { DatasetProfile, HealthSummary } from "@/lib/types";

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
    </div>
  );
}

function trendText(d: DatasetProfile) {
  if (d.trend === "first" || d.change === null)
    return "First check. Repeat it later to see a trend.";
  const points = Math.abs(d.change * 100).toFixed(1);
  if (d.trend === "up") return `▲ Up ${points} points since the previous check`;
  if (d.trend === "down")
    return `▼ Down ${points} points since the previous check`;
  return "● No meaningful change since the previous check";
}

export default function ProfileView({
  basePath,
  reportName,
}: {
  basePath: string;
  reportName: string;
}) {
  const { data, error } = useLoad<HealthSummary>(`${basePath}/summary`);

  if (error) return <p className="text-sm text-brand">{error}</p>;
  if (!data) return <p className="text-sm text-muted">Loading…</p>;
  if (data.total_checks === 0) {
    return (
      <Card title="Health profile">
        <p className="text-sm text-muted">
          No saved checks yet. A profile appears after the first risk check.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Stat label="Total checks" value={data.total_checks} />
        <Stat label="First check" value={fmtDate(data.first_check_at)} />
        <Stat label="Latest check" value={fmtDate(data.last_check_at)} />
        <Stat label="Lower risk results" value={data.band_counts.low} />
        <Stat
          label="Moderate / higher"
          value={`${data.band_counts.moderate} / ${data.band_counts.high}`}
        />
      </div>

      <div className="flex justify-end">
        <DownloadButton
          solid
          path={`${basePath}/report.pdf`}
          filename={reportName}
          label="Download full health report (PDF)"
        />
      </div>

      {data.datasets.map((d) => (
        <Card key={d.dataset} title={d.label}>
          <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
            <span className="text-2xl font-semibold">
              {pct(d.latest.probability)}
            </span>
            <RiskBadge band={d.latest.risk_band} />
            <span className="text-muted">
              Latest of {d.checks} check{d.checks > 1 ? "s" : ""},{" "}
              {fmtDate(d.latest.created_at)}
            </span>
          </div>
          <p className="mb-3 text-sm">{trendText(d)}</p>
          <TimelineChart points={d.points} label={d.label} />
        </Card>
      ))}

      <p className="text-xs text-muted">
        These are estimates for education only, not a diagnosis. A change
        between checks can come from different answers, not from a change in
        health.
      </p>
    </div>
  );
}
