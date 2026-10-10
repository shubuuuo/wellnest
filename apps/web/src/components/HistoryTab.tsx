"use client";

import { useState } from "react";
import Card from "./Card";
import DownloadButton from "./DownloadButton";
import PredictionList from "./PredictionList";
import { useApi } from "@/lib/useApi";
import type { DatasetInfo } from "@/lib/types";

export default function HistoryTab() {
  const [dataset, setDataset] = useState("");
  const { data: datasets } = useApi<DatasetInfo[]>("/dataset");

  return (
    <Card title="My checks">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <label className="text-sm">
          Show{" "}
          <select
            className="rounded-md border border-line bg-surface px-2 py-1"
            value={dataset}
            onChange={(e) => setDataset(e.target.value)}
          >
            <option value="">All datasets</option>
            {datasets?.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
        </label>
        <DownloadButton
          path="/me/report.pdf"
          filename="wellnest-health-report.pdf"
          label="Download full report (PDF)"
        />
      </div>
      <PredictionList
        key={dataset}
        basePath="/me"
        dataset={dataset}
        reportPath={(id) => `/me/predictions/${id}/report.pdf`}
      />
    </Card>
  );
}
