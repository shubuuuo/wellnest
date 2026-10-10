"use client";

import { useEffect, useMemo, useState } from "react";
import Card from "./Card";
import DownloadButton from "./DownloadButton";
import Pager from "./Pager";
import PredictionTable from "./PredictionTable";
import UserDetail from "./UserDetail";
import { useApi } from "@/lib/useApi";
import { useLoad } from "@/lib/useLoad";
import type { AnyPrediction, DatasetInfo, Page } from "@/lib/types";

const PAGE_SIZE = 20;
const field = "rounded-md border border-line bg-surface px-2 py-1 text-sm";

export default function AdminPredictionsTab() {
  const { data: datasets } = useApi<DatasetInfo[]>("/dataset");
  const [f, setF] = useState({
    search: "",
    dataset: "",
    band: "",
    from: "",
    to: "",
  });
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [viewing, setViewing] = useState<{
    id: string;
    name: string;
    email: string;
  } | null>(null);

  // wait until typing pauses before querying
  useEffect(() => {
    const t = setTimeout(() => setSearch(f.search.trim()), 300);
    return () => clearTimeout(t);
  }, [f.search]);

  const filterQuery = useMemo(() => {
    const p = new URLSearchParams();
    if (search) p.set("search", search);
    if (f.dataset) p.set("dataset", f.dataset);
    if (f.band) p.set("band", f.band);
    if (f.from) p.set("date_from", f.from);
    if (f.to) p.set("date_to", f.to);
    return p.toString();
  }, [search, f.dataset, f.band, f.from, f.to]);

  const listQuery = `${filterQuery}${filterQuery ? "&" : ""}page=${page}&page_size=${PAGE_SIZE}`;
  const { data, error } = useLoad<Page<AnyPrediction>>(
    `/admin/predictions?${listQuery}`,
  );

  function change(patch: Partial<typeof f>) {
    setF({ ...f, ...patch });
    setPage(1);
  }

  if (viewing) {
    return (
      <UserDetail
        userId={viewing.id}
        name={viewing.name}
        email={viewing.email}
        onBack={() => setViewing(null)}
      />
    );
  }

  return (
    <Card title="All predictions">
      <div className="mb-3 flex flex-wrap items-end gap-3">
        <input
          className={field}
          placeholder="Search user name or email"
          value={f.search}
          onChange={(e) => change({ search: e.target.value })}
        />
        <select
          className={field}
          value={f.dataset}
          onChange={(e) => change({ dataset: e.target.value })}
        >
          <option value="">All datasets</option>
          {datasets?.map((d) => (
            <option key={d.id} value={d.id}>
              {d.label}
            </option>
          ))}
        </select>
        <select
          className={field}
          value={f.band}
          onChange={(e) => change({ band: e.target.value })}
        >
          <option value="">All risk bands</option>
          <option value="low">Lower</option>
          <option value="moderate">Moderate</option>
          <option value="high">Higher</option>
        </select>
        <label className="text-xs text-muted">
          From{" "}
          <input
            type="date"
            className={field}
            value={f.from}
            onChange={(e) => change({ from: e.target.value })}
          />
        </label>
        <label className="text-xs text-muted">
          To{" "}
          <input
            type="date"
            className={field}
            value={f.to}
            onChange={(e) => change({ to: e.target.value })}
          />
        </label>
        <div className="ml-auto">
          <DownloadButton
            path={`/admin/predictions/export.csv${filterQuery ? `?${filterQuery}` : ""}`}
            filename="wellnest-predictions.csv"
            label="Export CSV (current filters)"
          />
        </div>
      </div>

      {error && <p className="text-sm text-brand">{error}</p>}
      {!data && !error && <p className="text-sm text-muted">Loading…</p>}
      {data && data.total === 0 && (
        <p className="text-sm text-muted">
          No predictions match these filters.
        </p>
      )}
      {data && data.total > 0 && (
        <>
          <PredictionTable
            items={data.items}
            showUser
            reportPath={(id) => `/admin/predictions/${id}/report.pdf`}
            onOpenUser={(id, name, email) => setViewing({ id, name, email })}
          />
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
