import type { Band } from "@/lib/types";

const STYLE: Record<Band, { text: string; cls: string }> = {
  low: {
    text: "✓ Lower",
    cls: "bg-emerald-50 text-emerald-800 border-emerald-200",
  },
  moderate: {
    text: "! Moderate",
    cls: "bg-amber-50 text-amber-900 border-amber-200",
  },
  high: { text: "▲ Higher", cls: "bg-brand-soft text-brand border-brand/30" },
};

export default function RiskBadge({ band }: { band: Band }) {
  const s = STYLE[band];
  return (
    <span
      className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${s.cls}`}
    >
      {s.text}
    </span>
  );
}
