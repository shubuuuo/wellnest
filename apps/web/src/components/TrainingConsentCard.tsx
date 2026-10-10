"use client";

import { useState } from "react";
import Card from "./Card";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { User } from "@/lib/types";

export default function TrainingConsentCard() {
  const { user, updateUser } = useAuth();
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  if (!user) return null;

  async function change(granted: boolean) {
    setBusy(true);
    setProblem(null);
    try {
      updateUser(await api.put<User>("/me/training-consent", { granted }));
    } catch (e) {
      setProblem(
        e instanceof ApiError ? e.userMessage : "Could not save your choice",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Help improve the models (optional)">
      <label className="flex items-start gap-2 text-sm">
        <input
          type="checkbox"
          className="mt-1"
          checked={user.training_consent}
          disabled={busy}
          onChange={(e) => change(e.target.checked)}
        />
        <span>
          If an administrator confirms my real result, allow my answers and that
          result to be added to an anonymous learning pool (no name, no
          account).
        </span>
      </label>
      <p className="mt-2 text-xs text-muted">
        Turning this off stops future use, but data already used to update a
        model cannot be taken back out. Online learning is enabled for course
        demonstration. It is not recommended for real clinical deployment.
      </p>
      {problem && (
        <p role="alert" className="mt-2 text-sm text-brand">
          {problem}
        </p>
      )}
    </Card>
  );
}
