import { fmtDate, fmtDateTime, pct } from "@/lib/format";
import type { SummaryPoint } from "@/lib/types";

const W = 640,
  H = 220,
  L = 44,
  R = 16,
  T = 12,
  B = 28;

export default function TimelineChart({
  points,
  label,
}: {
  points: SummaryPoint[];
  label: string;
}) {
  const n = points.length;
  if (n === 0) return null;
  const x = (i: number) =>
    n === 1 ? (L + W - R) / 2 : L + (i * (W - L - R)) / (n - 1);
  const y = (p: number) => T + (1 - p) * (H - T - B);
  const path = points
    .map(
      (p, i) =>
        `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.probability).toFixed(1)}`,
    )
    .join(" ");
  const first = points[0];
  const last = points[n - 1];

  return (
    <figure>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`${label}: ${n} checks, from ${pct(first.probability)} to ${pct(last.probability)}`}
        className="h-auto w-full"
      >
        {[0, 0.3, 0.7, 1].map((t) => (
          <g key={t}>
            <line
              x1={L}
              x2={W - R}
              y1={y(t)}
              y2={y(t)}
              stroke="var(--line)"
              strokeDasharray={t === 0.3 || t === 0.7 ? "4 4" : undefined}
            />
            <text
              x={L - 6}
              y={y(t) + 4}
              textAnchor="end"
              fontSize="11"
              fill="var(--muted)"
            >
              {Math.round(t * 100)}%
            </text>
          </g>
        ))}
        {n > 1 && (
          <path d={path} fill="none" stroke="var(--brand)" strokeWidth="2" />
        )}
        {points.map((p, i) => (
          <circle
            key={p.id}
            cx={x(i)}
            cy={y(p.probability)}
            r="4"
            fill="var(--brand)"
          >
            <title>{`${fmtDateTime(p.created_at)}: ${pct(p.probability)} (${p.risk_band})`}</title>
          </circle>
        ))}
        <text x={L} y={H - 8} fontSize="11" fill="var(--muted)">
          {fmtDate(first.created_at)}
        </text>
        <text
          x={W - R}
          y={H - 8}
          textAnchor="end"
          fontSize="11"
          fill="var(--muted)"
        >
          {fmtDate(last.created_at)}
        </text>
      </svg>
      <figcaption className="mt-1 text-xs text-muted">
        Dashed lines mark the 30% and 70% risk-band limits. Checks are spaced
        evenly, not by date.
      </figcaption>
    </figure>
  );
}
