"use client";

import { useState, type ComponentType } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useApi } from "@/lib/useApi";
import { useAuth } from "@/lib/auth";
import type { DatasetInfo } from "@/lib/types";

export type WorkspaceTab = {
  id: string;
  label: string;
  View: ComponentType<{ dataset: string }>;
  needsDataset: boolean;
};

export default function Workspace({
  title,
  tabs,
}: {
  title: string;
  tabs: WorkspaceTab[];
}) {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [active, setActive] = useState(tabs[0].id);
  const [chosen, setChosen] = useState<string | null>(null);
  const { data: datasets, error } = useApi<DatasetInfo[]>("/dataset");

  const dataset = chosen ?? datasets?.[0]?.id ?? "";
  const inAdmin = title === "Admin panel";

  async function signOut() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <div>
            <h1 className="text-xl font-semibold text-brand">WellNest</h1>
            <p className="text-sm text-muted">{title}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            {datasets && datasets.length > 0 && (
              <label>
                Dataset{" "}
                <select
                  className="rounded-md border border-line bg-surface px-2 py-1"
                  value={dataset}
                  onChange={(e) => setChosen(e.target.value)}
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {user?.role === "admin" && (
              <Link
                href={inAdmin ? "/app" : "/admin"}
                className="text-brand underline"
              >
                {inAdmin ? "User view" : "Admin panel"}
              </Link>
            )}
            <span className="text-muted">
              {user?.name} ({user?.role})
            </span>
            <button
              onClick={signOut}
              className="rounded-md border border-line px-3 py-1 hover:border-brand"
            >
              Log out
            </button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setActive(t.id)}
              className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium ${
                active === t.id
                  ? "border-brand text-brand"
                  : "border-transparent text-muted hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {error && <p className="mb-4 text-sm text-brand">{error}</p>}
        {/* {tabs.map(({ id, View, needsDataset }) => (
          <div
            key={`${needsDataset ? dataset : "-"}-${id}`}
            className={active === id ? "" : "hidden"}
          >
            {needsDataset && !dataset ? (
              <p className="text-sm text-muted">
                No trained dataset yet. Run: python ml/train.py lung
              </p>
            ) : (
              <View dataset={dataset} />
            )}
          </div>
        ))} */}
        {tabs.map(({ id, View, needsDataset }) =>
          active === id ? (
            <div key={`${needsDataset ? dataset : "-"}-${id}`}>
              {needsDataset && !dataset ? (
                <p className="text-sm text-muted">
                  No trained dataset yet. Run: python ml/train.py lung
                </p>
              ) : (
                <View dataset={dataset} />
              )}
            </div>
          ) : null,
        )}
      </main>
    </div>
  );
}
