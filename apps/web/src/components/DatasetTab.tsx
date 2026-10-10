"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Card from "./Card";
import { useApi } from "@/lib/useApi";
import type { Summary } from "@/lib/types";

const RED = "#991b1b";
const GREY = "#a1a1aa";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className="text-2xl font-semibold">{value}</p>
    </div>
  );
}

function StackedBars({
  data,
}: {
  data: { label: string; "No cancer": number; Cancer: number }[];
}) {
  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" fontSize={11} />
          <YAxis fontSize={11} />
          <Tooltip />
          <Legend />
          <Bar dataKey="No cancer" stackId="a" fill={GREY} />
          <Bar dataKey="Cancer" stackId="a" fill={RED} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function DatasetTab({ dataset }: { dataset: string }) {
  const { data, error } = useApi<Summary>(
    "/dataset/summary?dataset=" + dataset,
  );
  if (error) return <p className="text-sm text-brand">{error}</p>;
  if (!data) return <p className="text-sm text-muted">Loading…</p>;

  const pie = [
    { name: "No cancer", value: data.class_counts.no_cancer },
    { name: "Cancer", value: data.class_counts.cancer },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Rows" value={data.rows.toLocaleString()} />
        <Stat label="Features" value={String(data.columns)} />
        <Stat
          label="Cancer cases"
          value={`${(data.positive_rate * 100).toFixed(1)}%`}
        />
      </div>

      <Card title="Class balance">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pie}
                dataKey="value"
                nameKey="name"
                outerRadius={90}
                label
              >
                {pie.map((_, i) => (
                  <Cell key={i} fill={i === 0 ? GREY : RED} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {data.numeric.map((h) => (
          <Card key={h.name} title={`${h.name} (histogram)`}>
            <StackedBars
              data={h.no_cancer.map((v, i) => ({
                label: ((h.edges[i] + h.edges[i + 1]) / 2).toFixed(1),
                "No cancer": v,
                Cancer: h.cancer[i],
              }))}
            />
          </Card>
        ))}
        {data.categorical.map((h) => (
          <Card key={h.name} title={`${h.name} (counts)`}>
            <StackedBars
              data={h.categories.map((c, i) => ({
                label: c,
                "No cancer": h.no_cancer[i],
                Cancer: h.cancer[i],
              }))}
            />
          </Card>
        ))}
      </div>
    </div>
  );
}
