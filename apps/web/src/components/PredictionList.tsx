"use client";

import { useState } from "react";
import Pager from "./Pager";
import PredictionTable from "./PredictionTable";
import { useLoad } from "@/lib/useLoad";
import type { AnyPrediction, Page } from "@/lib/types";

const PAGE_SIZE = 10;

export default function PredictionList({
  basePath,
  reportPath,
  dataset,
}: {
  basePath: string; // "/me" or `/admin/users/${id}`
  reportPath: (id: string) => string;
  dataset?: string;
}) {
  const [page, setPage] = useState(1);
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(PAGE_SIZE),
  });
  if (dataset) params.set("dataset", dataset);
  const { data, error } = useLoad<Page<AnyPrediction>>(
    `${basePath}/predictions?${params}`,
  );

  if (error) return <p className="text-sm text-brand">{error}</p>;
  if (!data) return <p className="text-sm text-muted">Loading…</p>;
  if (data.total === 0)
    return <p className="text-sm text-muted">No saved checks yet.</p>;

  return (
    <>
      <PredictionTable items={data.items} reportPath={reportPath} />
      <Pager
        page={page}
        pageSize={PAGE_SIZE}
        total={data.total}
        onChange={setPage}
      />
    </>
  );
}
