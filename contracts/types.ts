/**
 * Waga API v1 read surface — TypeScript contract.
 *
 * Mirrors docs/api-contracts-v1.md. Copy this file into the frontend app and import from it.
 * Regenerate the matching fixtures with `python contracts/generate_mock.py`.
 *
 * Breaking changes here must be announced; additive changes are fine.
 */

// ---------------------------------------------------------------------------
// Frozen vocabularies
// ---------------------------------------------------------------------------

export type MarketCode =
  | "merkato"
  | "shola"
  | "ehil_berenda"
  | "atikilt_tera"
  | "piazza"
  | "saris"
  | "akaki"
  | "asko"
  | "kera"
  | "other";

export type CommodityCode =
  | "teff_mixed"
  | "wheat"
  | "maize"
  | "onion"
  | "cooking_oil";

export type Unit = "kg" | "liter";
export type CityCode = "addis_ababa";
export type BasketCode = "phase1_staple5";

export type CellStatus = "published" | "insufficient_data";

export type InsufficientReason =
  | "below_threshold"
  | "no_submissions"
  | "all_flagged"
  | null;

export type SubmissionSource = "user" | "agent" | "scraped" | "seed";

export type LicenceClass =
  | "commercial_permitted"
  | "internal_only"
  | "display_only";

/** ISO 8601 UTC instant, e.g. "2026-07-25T06:00:00Z". */
export type Timestamp = string;
/** Calendar date, e.g. "2026-07-25". */
export type DateOnly = string;

// ---------------------------------------------------------------------------
// Envelope
// ---------------------------------------------------------------------------

export interface Window {
  start: Timestamp;
  end: Timestamp;
  hours: number;
}

export interface Coverage {
  cells_expected: number;
  cells_published: number;
  cells_insufficient: number;
  coverage_pct: number;
}

export interface Meta {
  generated_at: Timestamp;
  method_version: string;
  city: CityCode;
  currency: "ETB";
  window: Window;
  coverage: Coverage;
  licence_class: LicenceClass;
  snapshot_id: string;
}

/** Every 200 response uses this envelope. */
export interface Envelope<T> {
  meta: Meta;
  data: T;
}

export interface ApiError {
  error: {
    code:
      | "unknown_market"
      | "unknown_commodity"
      | "unknown_basket"
      | "invalid_range"
      | "range_too_large"
      | "unauthorized"
      | "tier_required";
    message: string;
    field?: string;
  };
}

// ---------------------------------------------------------------------------
// The price cell — the atom everything is built from
// ---------------------------------------------------------------------------

export type SourceMix = Partial<Record<SubmissionSource, number>>;

export interface PriceCell {
  market_code: MarketCode;
  market_name_en: string;
  market_name_am: string;
  commodity_code: CommodityCode;
  commodity_name_en: string;
  commodity_name_am: string;
  unit: Unit;
  currency: "ETB";
  status: CellStatus;
  /** null whenever status is "insufficient_data". Never render as 0. */
  value: number | null;
  n_submissions: number;
  n_contributors: number;
  source_mix: SourceMix;
  window_start: Timestamp;
  window_end: Timestamp;
  computed_at: Timestamp;
  method_version: string;
  insufficient_reason: InsufficientReason;
}

// ---------------------------------------------------------------------------
// GET /reference
// ---------------------------------------------------------------------------

export interface MarketRef {
  code: MarketCode;
  name_en: string;
  name_am: string;
  latitude: number | null;
  longitude: number | null;
  is_active: boolean;
}

export interface CommodityRef {
  code: CommodityCode;
  name_en: string;
  name_am: string;
  category: string;
  unit: Unit;
  price_hint_low: number | null;
  price_hint_high: number | null;
}

export interface BasketItemRef {
  commodity_code: CommodityCode;
  quantity: number;
  unit: Unit;
}

export interface BasketRef {
  code: BasketCode;
  name_en: string;
  household_size: number;
  period_days: number;
  items: BasketItemRef[];
}

export interface ReferenceData {
  city: { code: CityCode; name_en: string; name_am: string };
  markets: MarketRef[];
  commodities: CommodityRef[];
  baskets: BasketRef[];
}

export type ReferenceResponse = Envelope<ReferenceData>;

// ---------------------------------------------------------------------------
// GET /prices/current
// ---------------------------------------------------------------------------

export interface MarketExtreme {
  market_code: MarketCode;
  value: number;
}

export interface CityPrice {
  commodity_code: CommodityCode;
  unit: Unit;
  status: CellStatus;
  /** Median across published market cells. */
  value: number | null;
  markets_published: number;
  markets_expected: number;
  min: MarketExtreme | null;
  max: MarketExtreme | null;
  spread_pct: number | null;
}

export interface PricesCurrentData {
  cells: PriceCell[];
  city_prices: CityPrice[];
}

export type PricesCurrentResponse = Envelope<PricesCurrentData>;

// ---------------------------------------------------------------------------
// GET /prices/series
// ---------------------------------------------------------------------------

export type SeriesInterval = "day" | "week" | "month";

export interface SeriesPoint {
  date: DateOnly;
  /** null when status is "insufficient_data". Break the line, do not interpolate. */
  value: number | null;
  status: CellStatus;
  n_submissions: number;
}

export interface Series {
  commodity_code: CommodityCode;
  /** null means the city aggregate. */
  market_code: MarketCode | null;
  unit: Unit;
  points: SeriesPoint[];
}

export interface PricesSeriesData {
  interval: SeriesInterval;
  series: Series[];
}

export type PricesSeriesResponse = Envelope<PricesSeriesData>;

// ---------------------------------------------------------------------------
// GET /coverage
// ---------------------------------------------------------------------------

export interface CoverageCell {
  commodity_code: CommodityCode;
  status: CellStatus;
  n_submissions: number;
  hours_since_last: number | null;
}

export interface CoverageRow {
  market_code: MarketCode;
  cells: CoverageCell[];
}

export interface CoverageData {
  matrix: CoverageRow[];
  worst_covered: Array<{
    market_code: MarketCode;
    commodity_code: CommodityCode;
    hours_since_last: number | null;
  }>;
}

export type CoverageResponse = Envelope<CoverageData>;

// ---------------------------------------------------------------------------
// GET /affordability
// ---------------------------------------------------------------------------

export type AffordabilityBand = "Stable" | "Watch" | "Tightening" | "Severe";

export interface AffordabilityItem {
  commodity_code: CommodityCode;
  quantity: number;
  unit: Unit;
  unit_price_now: number | null;
  unit_price_prior: number | null;
  cost_now: number | null;
  cost_prior: number | null;
  change_pct: number | null;
  /** Share of the total basket movement attributable to this item, in percent. */
  contribution_to_change_pct: number | null;
  status: CellStatus;
}

export interface AffordabilityData {
  basket_code: BasketCode;
  household_size: number;
  period_days: number;
  status: CellStatus;
  cost_now: number | null;
  cost_prior: number | null;
  prior_date: DateOnly;
  change_abs: number | null;
  change_pct: number | null;
  /** 0–100. 100 = no movement, 0 = a 20% rise or worse. */
  score: number | null;
  band: AffordabilityBand | null;
  method_version: string;
  items: AffordabilityItem[];
  /** Non-empty means the basket could not be priced. */
  missing_commodities: CommodityCode[];
}

export type AffordabilityResponse = Envelope<AffordabilityData>;

// ---------------------------------------------------------------------------
// GET /heatmap
// ---------------------------------------------------------------------------

export type HeatMetric = "pct_change_7d" | "pct_change_30d";
export type HeatBand = "cool" | "stable" | "warm" | "hot" | "critical";

export interface HeatCell {
  commodity_code: CommodityCode;
  status: CellStatus;
  value: number | null;
  pct_change: number | null;
  band: HeatBand | null;
}

export interface HeatMarket {
  market_code: MarketCode;
  market_name_en: string;
  latitude: number | null;
  longitude: number | null;
  status: CellStatus;
  heat: number | null;
  band: HeatBand | null;
  cells_published: number;
  cells_expected: number;
  cells: HeatCell[];
}

export interface HeatmapData {
  metric: HeatMetric;
  method_version: string;
  markets: HeatMarket[];
  hottest_cell: {
    market_code: MarketCode;
    commodity_code: CommodityCode;
    pct_change: number;
  } | null;
}

export type HeatmapResponse = Envelope<HeatmapData>;

// ---------------------------------------------------------------------------
// GET /alerts
// ---------------------------------------------------------------------------

export type SpikeBand = "normal" | "stress" | "alert" | "crisis";

export interface SpikeAlert {
  market_code: MarketCode;
  commodity_code: CommodityCode;
  /** Detrended residual z-score. */
  spike: number;
  /** The weaker of the z band and the deviation band. */
  band: SpikeBand;
  value: number;
  /** Trend value the price was scored against. */
  expected: number;
  median_30d: number;
  pct_above_expected: number;
  first_detected_at: Timestamp;
  consecutive_days: number;
}

export interface AlertsData {
  method_version: string;
  /** Stays false until 24 monthly observations exist. Never present this as WFP ALPS. */
  alps_comparable: boolean;
  alps_comparable_note: string;
  window_days: number;
  min_deviation_pct: number;
  /** Band cut points for the z-score: [stress, alert, crisis]. */
  z_thresholds: number[];
  /** Band cut points for percent deviation from trend: [stress, alert, crisis]. */
  deviation_thresholds_pct: number[];
  alerts: SpikeAlert[];
}

export type AlertsResponse = Envelope<AlertsData>;

// ---------------------------------------------------------------------------
// GET /meb/food-line
// ---------------------------------------------------------------------------

export interface MebFoodLineData {
  household_size: number;
  waga_food_line_now: number | null;
  waga_food_line_prior: number | null;
  change_pct: number | null;
  coverage_note: string;
  ecwg_reference: {
    source: string;
    national_meb_full_etb: number;
    national_meb_food_etb: number;
    as_of: DateOnly;
    review_cadence_months: number;
    revision_trigger: string;
  };
  consecutive_months_rising: number;
  revision_trigger_met: boolean;
}

export type MebFoodLineResponse = Envelope<MebFoodLineData>;

// ---------------------------------------------------------------------------
// POST /copilot/ask
// ---------------------------------------------------------------------------

export type AnswerMode = "rule_based" | "llm_assisted";
export type Confidence = "low" | "medium" | "high";

export interface Citation {
  label: string;
  value: number;
  unit: string;
  source: string;
  cell_refs: string[];
}

export interface ImpactBlock {
  household_count: number;
  gap_per_household_etb: number;
  monthly_total_etb: number;
  months?: number;
  total_etb?: number;
  note: string;
}

export interface CopilotAskRequest {
  question: string;
  household_count?: number;
  language?: "en" | "am";
}

export interface CopilotData {
  answer: string;
  recommendation: {
    action:
      | "increase_transfer_value"
      | "hold_transfer_value"
      | "decrease_transfer_value"
      | "insufficient_data";
    band_low_pct: number | null;
    band_high_pct: number | null;
    confidence: Confidence;
    confidence_reason: string;
  };
  /** Mandatory and non-empty. An uncited answer is a bug. */
  citations: Citation[];
  impact: ImpactBlock | null;
  mode: AnswerMode;
}

export type CopilotResponse = Envelope<CopilotData>;

// ---------------------------------------------------------------------------
// POST /impact
// ---------------------------------------------------------------------------

export interface ImpactRequest {
  household_count: number;
  gap_per_household_etb: number;
  months?: number;
}

export type ImpactResponse = Envelope<ImpactBlock>;

// ---------------------------------------------------------------------------
// GET /business/cost-index
// ---------------------------------------------------------------------------

export interface CostIndexItem {
  commodity_code: CommodityCode;
  quantity: number;
  unit: Unit;
  unit_price: number | null;
  cost_etb: number | null;
  share_pct: number | null;
  status: CellStatus;
}

export interface CostIndexPoint {
  date: DateOnly;
  value: number | null;
  status: CellStatus;
}

export interface CostIndexData {
  method_version: string;
  base_date: DateOnly;
  base_value: 100;
  current_value: number | null;
  change_pct_30d: number | null;
  monthly_cost_now_etb: number | null;
  monthly_cost_base_etb: number | null;
  /** Coefficient of variation of the daily city series, in percent. */
  volatility_30d_pct: number | null;
  /** Median ± 1.28σ. A band, not a forecast. */
  planning_band: { low_etb: number; high_etb: number; confidence: number } | null;
  items: CostIndexItem[];
  series: CostIndexPoint[];
}

export type CostIndexResponse = Envelope<CostIndexData>;

// ---------------------------------------------------------------------------
// GET /business/sourcing
// ---------------------------------------------------------------------------

export interface SourcingMarket {
  market_code: MarketCode;
  market_name_en: string;
  status: CellStatus;
  value: number | null;
  diff_from_median_pct: number | null;
  n_submissions: number;
}

export interface SourcingCommodity {
  commodity_code: CommodityCode;
  unit: Unit;
  city_median: number | null;
  cheapest: { market_code: MarketCode; value: number; n_submissions: number } | null;
  dearest: { market_code: MarketCode; value: number; n_submissions: number } | null;
  spread_pct: number | null;
  saving_per_unit_etb: number | null;
  volatility_30d_pct: number | null;
  markets: SourcingMarket[];
}

export interface SourcingData {
  commodities: SourcingCommodity[];
}

export type SourcingResponse = Envelope<SourcingData>;

// ---------------------------------------------------------------------------
// POST /business/benchmark
// ---------------------------------------------------------------------------

export type BenchmarkVerdict =
  | "below_market"
  | "at_market"
  | "above_market"
  | "far_above_market";

export interface BenchmarkRequest {
  commodity_code: CommodityCode;
  quoted_price: number;
  unit: Unit;
}

export interface BenchmarkData {
  commodity_code: CommodityCode;
  quoted_price: number;
  city_median: number | null;
  diff_pct: number | null;
  percentile: number | null;
  verdict: BenchmarkVerdict;
  message: string;
  cheapest_alternative: { market_code: MarketCode; value: number } | null;
}

export type BenchmarkResponse = Envelope<BenchmarkData>;

// ---------------------------------------------------------------------------
// POST /business/ask
// ---------------------------------------------------------------------------

export interface BusinessAskRequest {
  question: string;
  language?: "en" | "am";
}

export interface Driver {
  label: string;
  value: number;
  unit: string;
  direction: "up" | "down" | "flat";
}

export interface BusinessAskData {
  answer: string;
  verdict: {
    action:
      | "source_at_alternative_market"
      | "buy_now"
      | "delay_purchase"
      | "avoid_fixed_contract"
      | "lock_fixed_contract"
      | "insufficient_data";
    confidence: Confidence;
    confidence_reason: string;
  };
  drivers: Driver[];
  citations: Citation[];
  mode: AnswerMode;
}

export type BusinessAskResponse = Envelope<BusinessAskData>;

// ---------------------------------------------------------------------------
// GET /research/snapshots
// ---------------------------------------------------------------------------

export interface Snapshot {
  snapshot_id: string;
  created_at: Timestamp;
  method_version: string;
  temporal_coverage: { start: DateOnly; end: DateOnly };
  spatial_coverage: { city: CityCode; markets: number };
  commodities: number;
  row_count: number;
  rows_published: number;
  rows_insufficient: number;
  licence: string;
  checksum_sha256: string;
  citation: string;
  download: { csv: string; parquet: string | null };
  /** Always true. A late submission creates a new snapshot, never mutates this one. */
  immutable: boolean;
}

export interface SnapshotsData {
  snapshots: Snapshot[];
}

export type SnapshotsResponse = Envelope<SnapshotsData>;

// ---------------------------------------------------------------------------
// GET /research/methodology
// ---------------------------------------------------------------------------

export interface MethodologyData {
  method_version: string;
  effective_from: DateOnly;
  window_hours: number;
  publish_threshold_submissions: number;
  aggregation: string;
  source_weights: Record<SubmissionSource, number>;
  recency_weight: string;
  imputation: "none";
  below_threshold_behaviour: string;
  changelog: Array<{ version: string; date: DateOnly; change: string }>;
}

export type MethodologyResponse = Envelope<MethodologyData>;

// ---------------------------------------------------------------------------
// GET /research/codebook
// ---------------------------------------------------------------------------

export interface CodebookColumn {
  name: string;
  type: "string" | "number" | "date" | "datetime" | "enum";
  unit: string | null;
  hxl_tag: string | null;
  description: string;
  allowed_values: string[] | null;
  nullable: boolean;
}

export interface CodebookData {
  dataset: string;
  method_version: string;
  columns: CodebookColumn[];
}

export type CodebookResponse = Envelope<CodebookData>;
