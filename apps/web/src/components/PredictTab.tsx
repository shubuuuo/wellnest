"use client";

import { useState } from "react";
import Card from "./Card";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import DownloadButton from "./DownloadButton";
import { notifyPredictionsChanged } from "@/lib/useLoad";
import type { PredictResponse, SchemaField } from "@/lib/types";

const input =
  "w-full rounded-md border border-line bg-surface px-3 py-2 text-sm";
const BAND = {
  low: "✓ Lower estimated risk",
  moderate: "! Moderate estimated risk",
  high: "▲ Higher estimated risk",
};

export default function PredictTab({ dataset }: { dataset: string }) {
  const { data: schema, error } = useApi<SchemaField[]>(
    "/predict/schema?dataset=" + dataset,
  );
  // const [values, setValues] = useState<Record<string, string>>({});
  const [edits, setEdits] = useState<Record<string, string>>({});
  const values: Record<string, string> = {
    ...Object.fromEntries(
      (schema ?? []).map((f) => [f.name, String(f.default)]),
    ),
    ...edits,
  };
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  // useEffect(() => {
  //   if (schema)
  //     setValues(
  //       Object.fromEntries(schema.map((f) => [f.name, String(f.default)])),
  //     );
  // }, [schema]);

  async function submit() {
    setBusy(true);
    setProblem(null);
    try {
      // setResult(
      //   await api.post<PredictResponse>("/predict?dataset=" + dataset, {
      //     values,
      //   }),
      // );
      const saved = await api.post<PredictResponse>(
        "/predict?dataset=" + dataset,
        {
          values,
        },
      );
      setResult(saved);
      notifyPredictionsChanged();
    } catch (e) {
      setProblem(
        e instanceof ApiError ? e.userMessage : "Something went wrong",
      );
    } finally {
      setBusy(false);
    }
  }

  if (error) return <p className="text-sm text-brand">{error}</p>;
  if (!schema) return <p className="text-sm text-muted">Loading…</p>;

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <Card title="Patient details">
          <div className="grid gap-4 sm:grid-cols-2">
            {schema.map((f) => (
              <label key={f.name} className="block text-sm">
                <span className="mb-1 block text-muted">
                  {f.name}
                  {f.kind === "number" && ` (${f.min} to ${f.max})`}
                </span>
                {f.kind === "number" ? (
                  <input
                    className={input}
                    type="number"
                    step="any"
                    min={f.min}
                    max={f.max}
                    value={values[f.name] ?? ""}
                    onChange={(e) =>
                      setEdits({ ...edits, [f.name]: e.target.value })
                    }
                  />
                ) : (
                  <select
                    className={input}
                    value={values[f.name] ?? ""}
                    onChange={(e) =>
                      setEdits({ ...edits, [f.name]: e.target.value })
                    }
                  >
                    {f.options.map((o) => (
                      <option key={o} value={o}>
                        {o}
                      </option>
                    ))}
                  </select>
                )}
              </label>
            ))}
          </div>
          <button
            onClick={submit}
            disabled={busy}
            className="mt-4 rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy ? "Calculating…" : "Estimate risk"}
          </button>
          {problem && <p className="mt-3 text-sm text-brand">{problem}</p>}
        </Card>
      </div>

      <Card title="Result">
        {!result ? (
          <p className="text-sm text-muted">
            Fill in the form and press &quot;Estimate risk&quot;.
          </p>
        ) : (
          <div className="space-y-3">
            <p className="text-3xl font-semibold">
              {(result.probability * 100).toFixed(1)}%
            </p>
            <DownloadButton
              path={`/me/predictions/${result.id}/report.pdf`}
              filename={`wellnest-risk-report-${result.id.slice(0, 8)}.pdf`}
              label="Download this report (PDF)"
              solid
            />
            <div className="h-2 rounded bg-line">
              <div
                className="h-2 rounded bg-brand"
                style={{ width: `${result.probability * 100}%` }}
              />
            </div>
            <p className="text-sm font-medium">{BAND[result.risk_band]}</p>
            <p className="text-xs text-muted">Model: {result.model}</p>
            <p className="text-xs text-muted">{result.disclaimer}</p>
          </div>
        )}
      </Card>
    </div>
  );
}
