export const fmtDate = (v: string | null | undefined) =>
  v ? new Date(v).toLocaleDateString() : "—";
export const fmtDateTime = (v: string | null | undefined) =>
  v ? new Date(v).toLocaleString() : "—";
export const pct = (p: number, digits = 1) => `${(p * 100).toFixed(digits)}%`;
