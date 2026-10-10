"use client";

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Card from "./Card";
import { useLoad } from "@/lib/useLoad";
import type { Analytics } from "@/lib/types";

const RANGES = [7, 30, 90];
const AXIS = { fontSize: 12, fill: "#636369" };
const BRAND = "#991b1b";

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
      <p className="text-2xl font-semibold">{value}</p>
      {hint && <p className="text-xs text-muted">{hint}</p>}
    </div>
  );
}

function Chart({ children }: { children: React.ReactElement }) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  );
}

export default function AnalyticsTab() {
  const [days, setDays] = useState(30);
  const { data, error } = useLoad<Analytics>(`/admin/analytics?days=${days}`);

  if (error) return <p className="text-sm text-brand">{error}</p>;
  if (!data) return <p className="text-sm text-muted">Loading…</p>;

  const t = data.totals;
  const series = data.series.map((s) => ({ ...s, label: s.date.slice(5) }));
  const bands = [
    { name: "Lower", count: data.by_band.low },
    { name: "Moderate", count: data.by_band.moderate },
    { name: "Higher", count: data.by_band.high },
  ];
  const stars = [1, 2, 3, 4, 5].map((n) => ({
    name: `${n}★`,
    count: data.ratings.distribution[String(n)] ?? 0,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted">Period:</span>
        {RANGES.map((r) => (
          <button
            key={r}
            onClick={() => setDays(r)}
            aria-pressed={days === r}
            className={`rounded-md border px-3 py-1 ${days === r ? "border-brand text-brand" : "border-line"}`}
          >
            {r} days
          </button>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Registered users" value={t.users} />
        <Stat label="Users who ran a check" value={t.users_with_checks} />
        <Stat
          label="Returning users"
          value={t.returning_users}
          hint="2 or more checks"
        />
        <Stat
          label="Active users"
          value={t.active_users_period}
          hint={`last ${data.days} days`}
        />
        <Stat label="Risk checks, all time" value={t.predictions} />
        <Stat label="Risk checks in period" value={t.predictions_period} />
        <Stat label="Reviews" value={data.ratings.count} />
        <Stat
          label="Average rating"
          value={data.ratings.average ? `${data.ratings.average} / 5` : "—"}
        />
      </div>

      <Card title="Activity per day">
        <Chart>
          <LineChart
            data={series}
            margin={{ top: 8, right: 12, bottom: 0, left: -12 }}
          >
            <CartesianGrid stroke="#e4e4e7" strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={AXIS} interval="preserveStartEnd" />
            <YAxis allowDecimals={false} tick={AXIS} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="predictions"
              name="Risk checks"
              stroke={BRAND}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="active_users"
              name="Active users"
              stroke="#0f766e"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="new_users"
              name="New sign-ups"
              stroke="#475569"
              strokeWidth={2}
              strokeDasharray="5 3"
              dot={false}
            />
          </LineChart>
        </Chart>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Checks by dataset">
          <Chart>
            <BarChart
              data={data.by_dataset}
              margin={{ top: 8, right: 8, bottom: 0, left: -16 }}
            >
              <CartesianGrid stroke="#e4e4e7" strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={AXIS} />
              <YAxis allowDecimals={false} tick={AXIS} />
              <Tooltip />
              <Bar dataKey="count" name="Risk checks" fill={BRAND} />
            </BarChart>
          </Chart>
        </Card>
        <Card title="Results by risk band">
          <Chart>
            <BarChart
              data={bands}
              margin={{ top: 8, right: 8, bottom: 0, left: -16 }}
            >
              <CartesianGrid stroke="#e4e4e7" strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={AXIS} />
              <YAxis allowDecimals={false} tick={AXIS} />
              <Tooltip />
              <Bar dataKey="count" name="Results" fill={BRAND} />
            </BarChart>
          </Chart>
        </Card>
        <Card title="Ratings">
          <Chart>
            <BarChart
              data={stars}
              margin={{ top: 8, right: 8, bottom: 0, left: -16 }}
            >
              <CartesianGrid stroke="#e4e4e7" strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={AXIS} />
              <YAxis allowDecimals={false} tick={AXIS} />
              <Tooltip />
              <Bar dataKey="count" name="Reviews" fill={BRAND} />
            </BarChart>
          </Chart>
        </Card>
      </div>

      <p className="text-xs text-muted">
        These figures count real accounts and real checks only. Share the app
        with classmates to build genuine usage.
      </p>
    </div>
  );
}
