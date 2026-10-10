"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api";
import { downloadFile } from "@/lib/download";

export default function DownloadButton({
  path,
  filename,
  label,
  solid = false,
}: {
  path: string;
  filename: string;
  label: string;
  solid?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  async function go() {
    setBusy(true);
    setProblem(null);
    try {
      await downloadFile(path, filename);
    } catch (e) {
      setProblem(e instanceof ApiError ? e.userMessage : "Download failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={go}
        disabled={busy}
        className={`rounded-md px-3 py-1.5 text-sm font-medium disabled:opacity-50 ${
          solid
            ? "bg-brand text-white"
            : "border border-line hover:border-brand"
        }`}
      >
        {busy ? "Preparing…" : label}
      </button>
      {problem && (
        <span role="alert" className="text-xs text-brand">
          {problem}
        </span>
      )}
    </span>
  );
}
