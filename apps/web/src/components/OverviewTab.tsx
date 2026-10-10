"use client";

import { useApi } from "@/lib/useApi";
import type { AdminStats } from "@/lib/types";

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className="text-2xl font-semibold">{value}</p>
    </div>
  );
}

export default function OverviewTab() {
  const { data, error } = useApi<AdminStats>("/admin/stats");
  if (error) return <p className="text-sm text-brand">{error}</p>;
  if (!data) return <p className="text-sm text-muted">Loading…</p>;
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <Stat label="Total users" value={data.total_users} />
      <Stat label="Active accounts" value={data.active_accounts} />
      <Stat label="Admins" value={data.admins} />
      <Stat label="New in 7 days" value={data.new_last_7_days} />
      <Stat label="Logged in within 7 days" value={data.active_last_7_days} />
    </div>
  );
}
