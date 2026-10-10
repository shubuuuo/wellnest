"use client";

import { useEffect, useRef, useState } from "react";
import {
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
import { API_URL } from "@/lib/api";
import type { Metrics, StepMetrics } from "@/lib/types";

type Point = { rows: number; models: Record<string, StepMetrics> };
type BatchInfo = Record<string, { warm: Metrics; final: Metrics }>;
type Metric = "f1" | "recall" | "accuracy";

const COLORS = ["#991b1b", "#27272a", "#f87171", "#71717a"];
const select = "rounded-md border border-line bg-surface px-2 py-1 text-sm";

export default function OnlineTab({ dataset }: { dataset: string }) {
  const [points, setPoints] = useState<Point[]>([]);
  const [batch, setBatch] = useState<BatchInfo>({});
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState<"idle" | "running" | "done" | "error">(
    "idle",
  );
  const [metric, setMetric] = useState<Metric>("f1");
  const [chunk, setChunk] = useState(250);
  const [delay, setDelay] = useState(0.4);
  const source = useRef<EventSource | null>(null);

  useEffect(() => () => source.current?.close(), []);

  function start() {
    source.current?.close();
    setPoints([]);
    setBatch({});
    setStatus("running");
    const es = new EventSource(
      `${API_URL}/learning/stream?dataset=${dataset}&chunk=${chunk}&delay=${delay}`,
      { withCredentials: true },
    );
    source.current = es;
    es.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "start") {
        setBatch(msg.batch);
        setTotal(msg.total_rows);
      } else if (msg.type === "step") {
        setPoints((prev) => [
          ...prev,
          { rows: msg.rows_seen, models: msg.models },
        ]);
      } else if (msg.type === "done") {
        setStatus("done");
        es.close();
      }
    };
    es.onerror = () => {
      es.close();
      setStatus((s) => (s === "done" ? s : "error"));
    };
  }

  function stop() {
    source.current?.close();
    setStatus("idle");
  }

  const names = points[0] ? Object.keys(points[0].models) : [];
  const chartData = points.map((p) => ({
    rows: p.rows,
    ...Object.fromEntries(names.map((n) => [n, p.models[n][metric]])),
  }));
  const seen = points.length ? points[points.length - 1].rows : 0;

  return (
    <div className="space-y-6">
      <Card title="Online learning demo">
        <p className="mb-4 text-sm text-muted">
          The models start trained on a small slice of the data. Press Start:
          new patient rows arrive in chunks, and each online model updates
          itself after every chunk. The lines show the test score after each
          update.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={start}
            disabled={status === "running"}
            className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            Start stream
          </button>
          <button
            onClick={stop}
            disabled={status !== "running"}
            className="rounded-md border border-line px-4 py-2 text-sm disabled:opacity-50"
          >
            Stop
          </button>
          <label className="text-sm">
            Metric{" "}
            <select
              className={select}
              value={metric}
              onChange={(e) => setMetric(e.target.value as Metric)}
            >
              <option value="f1">F1</option>
              <option value="recall">Recall</option>
              <option value="accuracy">Accuracy</option>
            </select>
          </label>
          <label className="text-sm">
            Chunk{" "}
            <select
              className={select}
              value={chunk}
              onChange={(e) => setChunk(Number(e.target.value))}
            >
              <option value={100}>100 rows</option>
              <option value={250}>250 rows</option>
              <option value={500}>500 rows</option>
            </select>
          </label>
          <label className="text-sm">
            Speed{" "}
            <select
              className={select}
              value={delay}
              onChange={(e) => setDelay(Number(e.target.value))}
            >
              <option value={0.8}>Slow</option>
              <option value={0.4}>Normal</option>
              <option value={0.1}>Fast</option>
            </select>
          </label>
          <span className="text-sm text-muted">
            {status === "running" &&
              `Streaming… ${seen.toLocaleString()} / ${total.toLocaleString()} rows`}
            {status === "done" &&
              `Finished: ${seen.toLocaleString()} rows learned`}
            {status === "error" &&
              "Could not reach the server (is the API running?)"}
          </span>
        </div>
      </Card>

      <Card title="Live test score of the online models">
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="rows"
                type="number"
                domain={[0, total > 0 ? total : "auto"]}
                fontSize={11}
              />
              <YAxis
                domain={[
                  (min: number) => Math.max(0, Math.floor(min * 20) / 20),
                  1,
                ]}
                fontSize={11}
              />
              <Tooltip />
              <Legend />
              {names.map((n, i) => (
                <Line
                  key={n}
                  type="monotone"
                  dataKey={n}
                  stroke={COLORS[i % COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card title="Batch-only models cannot learn online">
        <p className="mb-3 text-sm text-muted">
          Random Forest and kernel SVM have no way to update from a few new
          rows. They must be retrained from scratch on all data. Scores below:
          trained on the small start vs fully retrained on everything.
        </p>
        <table className="w-full text-left text-sm">
          <thead className="text-muted">
            <tr>
              <th className="py-2 pr-4 font-medium">Model</th>
              <th className="py-2 pr-4 font-medium">Online update</th>
              <th className="py-2 pr-4 font-medium">Small start</th>
              <th className="py-2 pr-4 font-medium">After batch retrain</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(batch).map(([name, b]) => (
              <tr key={name} className="border-t border-line">
                <td className="py-2 pr-4 font-medium">{name}</td>
                <td className="py-2 pr-4">Not possible</td>
                <td className="py-2 pr-4">{b.warm[metric].toFixed(3)}</td>
                <td className="py-2 pr-4">
                  {status === "done" ? b.final[metric].toFixed(3) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
