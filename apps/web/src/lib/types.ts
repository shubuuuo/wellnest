export type Metrics = {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  tn: number;
  fp: number;
  fn: number;
  tp: number;
};
export type DatasetInfo = { id: string; label: string; target: string };
// export type ModelResult = {
//   name: string;
//   mode: "online" | "batch";
//   fit_seconds: number;
//   has_proba: boolean;
//   final: Metrics;
//   warm: Metrics;
// };
// export type Results = {
//   rows_total: number;
//   base_rows: number;
//   stream_rows: number;
//   test_rows: number;
//   baseline_accuracy: number;
//   best_model: string;
//   models: ModelResult[];
// };

export type ParamInfo = {
  name: string;
  label: string;
  value: number;
  default: number;
  min: number;
  max: number;
  int: boolean;
};
export type User = {
  id: string;
  email: string;
  name: string;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
  training_consent: boolean;
};
export type VersionMetrics = {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
};
export type UpdateOutcome = {
  model: string;
  version?: number;
  accepted: boolean;
  reason?: string;
  before: VersionMetrics | null;
  after: VersionMetrics | null;
};
export type EventDetails = {
  models?: UpdateOutcome[];
  reverted?: { model: string; from_version: number; to_version: number }[];
  model?: string;
  before?: VersionMetrics;
  after?: VersionMetrics;
  fit_seconds?: number;
  deployed?: boolean;
  reason?: string;
  note?: string;
  tolerance?: number;
  fingerprint?: string;
};
export type LoopEvent = {
  id: string;
  created_at: string;
  kind: "online_update" | "batch_retrain" | "rollback" | "reset";
  status: "applied" | "rolled_back" | "info";
  n_records: number;
  details: EventDetails;
  actor_name: string | null;
};
export type LoopStatus = {
  dataset: string;
  online_enabled: boolean;
  batch_size: number;
  tolerance: number;
  fingerprint: string;
  pool: { total: number; waiting: number; positive: number; negative: number };
  live: { name: string; version: number } | null;
  online_models: {
    name: string;
    version: number;
    is_live: boolean;
    metrics: VersionMetrics;
    created_at: string;
  }[];
  batch_models: {
    name: string;
    baseline: VersionMetrics;
    latest: EventDetails | null;
    latest_at: string | null;
    latest_records: number | null;
  }[];
  can_roll_back: boolean;
};
export type OutcomeRow = AnyPrediction & {
  training_consent: boolean;
  outcome: {
    confirmed_cancer: boolean;
    entered_pool: boolean;
    at: string;
  } | null;
};
export type OutcomeResult = {
  confirmed_cancer: boolean;
  entered_pool: boolean;
  update?: { event_id: string; accepted: number; total: number };
  update_skipped?: string;
};
export type UserList = {
  items: User[];
  total: number;
  page: number;
  page_size: number;
};
export type AdminStats = {
  total_users: number;
  active_accounts: number;
  admins: number;
  new_last_7_days: number;
  active_last_7_days: number;
};
export type Band = "low" | "moderate" | "high";

export type SavedPrediction = {
  id: string;
  created_at: string;
  dataset: string;
  dataset_label: string;
  model_name: string;
  model_trained_at: string | null;
  probability: number;
  label: 0 | 1;
  risk_band: Band;
  inputs: Record<string, string | number | boolean>;
};
// admin responses add the owner
export type AnyPrediction = SavedPrediction & {
  user_id?: string;
  user_email?: string;
  user_name?: string;
};
export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type SummaryPoint = {
  id: string;
  created_at: string;
  probability: number;
  risk_band: Band;
};
export type DatasetProfile = {
  dataset: string;
  label: string;
  checks: number;
  latest: SavedPrediction;
  change: number | null; // fraction, e.g. 0.04 = 4 points
  trend: "first" | "up" | "down" | "flat";
  points: SummaryPoint[];
};
export type HealthSummary = {
  total_checks: number;
  first_check_at: string | null;
  last_check_at: string | null;
  band_counts: Record<Band, number>;
  datasets: DatasetProfile[];
};
export type ModelResult = {
  name: string;
  mode: "online" | "batch";
  fit_seconds: number;
  has_proba: boolean;
  final: Metrics;
  warm: Metrics;
  roc: { fpr: number[]; tpr: number[] };
  param: ParamInfo;
  previous?: { metrics: Metrics; param_value: number; fit_seconds: number };
};
export type Results = {
  rows_total: number;
  base_rows: number;
  stream_rows: number;
  test_rows: number;
  baseline_accuracy: number;
  best_model: string;
  models: ModelResult[];
};
export type NumericHist = {
  name: string;
  edges: number[];
  no_cancer: number[];
  cancer: number[];
};
export type CategoryHist = {
  name: string;
  categories: string[];
  no_cancer: number[];
  cancer: number[];
};
export type Summary = {
  rows: number;
  columns: number;
  target: string;
  positive_rate: number;
  class_counts: { no_cancer: number; cancer: number };
  numeric: NumericHist[];
  categorical: CategoryHist[];
};
export type SchemaField =
  | { name: string; kind: "number"; min: number; max: number; default: number }
  | { name: string; kind: "category"; options: string[]; default: string };
export type PredictResponse = {
  id: string;
  created_at: string;
  probability: number;
  label: 0 | 1;
  risk_band: "low" | "moderate" | "high";
  model: string;
  disclaimer: string;
};
export type StepMetrics = { accuracy: number; f1: number; recall: number };
export type ReviewData = {
  rating: number;
  comment: string | null;
  created_at: string;
  updated_at: string;
};
export type MyReviewResponse = { review: ReviewData | null };
export type RatingSummary = {
  average: number | null;
  count: number;
  distribution: Record<string, number>;
};
export type Analytics = {
  days: number;
  totals: {
    users: number;
    predictions: number;
    users_with_checks: number;
    returning_users: number;
    active_users_period: number;
    predictions_period: number;
  };
  series: {
    date: string;
    new_users: number;
    predictions: number;
    active_users: number;
  }[];
  by_dataset: { dataset: string; label: string; count: number }[];
  by_band: Record<Band, number>;
  ratings: RatingSummary;
};
export type ActivityItem = {
  id: string;
  created_at: string;
  action: string;
  entity: string | null;
  entity_id: string | null;
  details: Record<string, unknown>;
  actor_id: string | null;
  actor_name: string | null;
  actor_email: string | null;
};
export type ActivityPage = Page<ActivityItem> & { actions: string[] };
export type AdminReview = {
  id: string;
  rating: number;
  comment: string | null;
  created_at: string;
  updated_at: string;
  user_name: string;
  user_email: string;
};
export type ReviewPage = Page<AdminReview> & { summary: RatingSummary };
