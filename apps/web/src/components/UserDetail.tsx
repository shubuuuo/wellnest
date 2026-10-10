"use client";

import Card from "./Card";
import PredictionList from "./PredictionList";
import ProfileView from "./ProfileView";

export default function UserDetail({
  userId,
  name,
  email,
  onBack,
}: {
  userId: string;
  name: string;
  email: string;
  onBack: () => void;
}) {
  const base = `/admin/users/${userId}`;
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={onBack}
          className="rounded-md border border-line px-3 py-1.5 text-sm hover:border-brand"
        >
          ← Back
        </button>
        <div>
          <h2 className="text-lg font-semibold">{name}</h2>
          <p className="text-sm text-muted">{email}</p>
        </div>
      </div>
      <ProfileView
        basePath={base}
        reportName={`wellnest-health-report-${userId.slice(0, 8)}.pdf`}
      />
      <Card title="All checks">
        <PredictionList
          basePath={base}
          reportPath={(id) => `/admin/predictions/${id}/report.pdf`}
        />
      </Card>
    </div>
  );
}
