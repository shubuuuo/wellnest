"use client";

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, ApiError } from "@/lib/api";
import type { ModelResult, Results } from "@/lib/types";

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-bg p-2 text-center">
      <p className="text-[11px] text-muted">{label}</p>
      <p className="text-sm font-semibold">{value}</p>
    </div>
  );
}

type Props = {
  model: ModelResult;
  isBest: boolean;
  dataset: string;
  canRetrain: boolean;
  onUpdated: (results: Results) => void;
};

export default function ModelCard({
  model,
  isBest,
  dataset,
  canRetrain,
  onUpdated,
}: Props) {
  const [value, setValue] = useState(String(model.param.value));
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const f = model.final;
  const roc = model.roc.fpr.map((x, i) => ({ fpr: x, tpr: model.roc.tpr[i] }));
  const learning = [
    {
      metric: "Accuracy",
      "Small start": model.warm.accuracy,
      "All training data": f.accuracy,
    },
    {
      metric: "Recall",
      "Small start": model.warm.recall,
      "All training data": f.recall,
    },
    { metric: "F1", "Small start": model.warm.f1, "All training data": f.f1 },
  ];

  async function retrain() {
    setBusy(true);
    setProblem(null);
    try {
      onUpdated(
        await api.post<Results>(`/models/retrain?dataset=${dataset}`, {
          name: model.name,
          value: Number(value),
        }),
      );
    } catch (e) {
      setProblem(e instanceof ApiError ? e.userMessage : "Retraining failed");
    } finally {
      setBusy(false);
    }
  }

  const change = model.previous ? f.f1 - model.previous.metrics.f1 : null;

  return (
    <section className="space-y-4 rounded-lg border border-line bg-surface p-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-semibold">{model.name}</h3>
        <span
          className={`rounded px-2 py-0.5 text-xs ${model.mode === "online" ? "bg-brand text-white" : "bg-line text-ink"}`}
        >
          {model.mode === "online" ? "Online" : "Batch only"}
        </span>
        {isBest && (
          <span className="rounded bg-brand-soft px-2 py-0.5 text-xs text-brand">
            ★ Used in Predict
          </span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
        <Tile label="Accuracy" value={f.accuracy.toFixed(3)} />
        <Tile label="Precision" value={f.precision.toFixed(3)} />
        <Tile label="Recall" value={f.recall.toFixed(3)} />
        <Tile label="F1" value={f.f1.toFixed(3)} />
        <Tile label="ROC-AUC" value={f.roc_auc.toFixed(3)} />
        <Tile label="Fit time" value={`${model.fit_seconds}s`} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-1 text-xs text-muted">
            ROC curve (closer to the top-left is better)
          </p>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={roc}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="fpr"
                  type="number"
                  domain={[0, 1]}
                  fontSize={10}
                />
                <YAxis domain={[0, 1]} fontSize={10} />
                <Tooltip />
                <ReferenceLine
                  segment={[
                    { x: 0, y: 0 },
                    { x: 1, y: 1 },
                  ]}
                  stroke="#a1a1aa"
                  strokeDasharray="4 4"
                />
                <Line
                  type="monotone"
                  dataKey="tpr"
                  stroke="#991b1b"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div>
          <p className="mb-1 text-xs text-muted">
            Effect of more training data
          </p>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={learning}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="metric" fontSize={10} />
                <YAxis domain={[0, 1]} fontSize={10} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Bar dataKey="Small start" fill="#a1a1aa" />
                <Bar dataKey="All training data" fill="#991b1b" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid max-w-xs grid-cols-2 gap-1 text-center text-xs">
        <div className="rounded bg-line p-2">
          True negatives
          <br />
          <b>{f.tn}</b>
        </div>
        <div className="rounded bg-brand-soft p-2">
          False alarms
          <br />
          <b>{f.fp}</b>
        </div>
        <div className="rounded bg-brand-soft p-2">
          Missed cancers
          <br />
          <b>{f.fn}</b>
        </div>
        <div className="rounded bg-line p-2">
          Cancers found
          <br />
          <b>{f.tp}</b>
        </div>
      </div>

      {canRetrain && (
        <div className="border-t border-line pt-3">
          <div className="flex flex-wrap items-end gap-3">
            <label className="text-sm">
              <span className="mb-1 block text-xs text-muted">
                {model.param.label} ({model.param.min} to {model.param.max})
              </span>
              <input
                type="number"
                step="any"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                className="w-32 rounded-md border border-line bg-surface px-2 py-1 text-sm"
              />
            </label>
            <button
              onClick={retrain}
              disabled={busy}
              className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {busy ? "Retraining…" : "Retrain on all training data"}
            </button>
          </div>
          {busy && model.fit_seconds > 20 && (
            <p className="mt-2 text-xs text-muted">
              Last training took {model.fit_seconds}s, so this may take a
              similar time.
            </p>
          )}
          {change !== null && (
            <p className="mt-2 text-xs text-muted">
              F1 changed from {model.previous!.metrics.f1.toFixed(3)} to{" "}
              {f.f1.toFixed(3)} ({change >= 0 ? "+" : ""}
              {change.toFixed(3)}) after changing {model.param.label} from{" "}
              {model.previous!.param_value} to {model.param.value}.
            </p>
          )}
          {problem && <p className="mt-2 text-sm text-brand">{problem}</p>}
        </div>
      )}
    </section>
  );
}
