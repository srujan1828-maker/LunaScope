export interface SiteAnnualData {
  max_consec_sun_days: number;
  max_consec_joint_days: number;
  annual_illum_fraction: number;
}

export interface LandingSite {
  site_id: string;
  name: string;
  region: string;
  lat_deg: number;
  lon_deg: number;
  elevation_m: number;
  description: string;
  psr_distance_km: number;
  scientific_significance: string;
  annual_data: Record<string, SiteAnnualData>;
}

export interface EphemerisData {
  timestamps: number[];
  sun_azimuth: number[];
  sun_elevation: number[];
  earth_azimuth: number[];
  earth_elevation: number[];
}

export interface IntervalMetrics {
  total_duration_hours: number;
  sun_availability_pct: number;
  equivalent_sun_hours: number;
  longest_shadow_gap_hours: number;
  earth_availability_pct: number;
  longest_earth_outage_hours: number;
  joint_availability_pct: number;
  longest_joint_window_hours: number;
  coverage: string;
}

export interface PowerConfig {
  enabled: boolean;
  panel_area_m2: number;
  panel_efficiency: number;
  panel_orientation: string;
  spacecraft_load_w: number;
  battery_capacity_wh: number;
  initial_soc_pct: number;
  reserve_margin_pct: number;
}

export interface PowerSimulationSummary {
  min_soc_pct: number;
  min_energy_wh: number;
  total_unmet_demand_wh: number;
  reserve_breach_hours: number;
  battery_depleted: boolean;
}

export interface PowerSimulationTimeSeries {
  power_generated_w: number[];
  net_power_w: number[];
  battery_energy_wh: number[];
  battery_soc_pct: number[];
  unmet_demand_wh: number[];
}

export interface PowerSimulation {
  inputs: any;
  summary: PowerSimulationSummary;
  time_series: PowerSimulationTimeSeries;
}

export interface EvaluatedSiteData {
  site_info: LandingSite;
  horizon_360: number[];
  timestamps: number[];
  ephemeris: EphemerisData;
  solar_fractions: number[];
  dte_visibility: number[];
  operational_states: number[];
  interval_metrics: IntervalMetrics;
  power_simulation?: PowerSimulation | null;
}

export interface ScenarioEvaluationResult {
  inputs: {
    site_ids: string[];
    start_time_iso: string;
    end_time_iso: string;
    mast_height_m: number;
    antenna_margin_deg: number;
    sun_threshold: number;
    power_config?: any;
  };
  evaluated_sites: Record<string, EvaluatedSiteData>;
  comparative_insights: string[];
  provenance: Record<string, string>;
}

export interface CandidateWindow {
  start_time_iso: string;
  end_time_iso: string;
  start_unix: number;
  duration_days: number;
  all_sites_passed: boolean;
  composite_score: number;
  site_evaluations: Record<string, {
    site_name: string;
    metrics: IntervalMetrics;
    passed: boolean;
    violations: string[];
  }>;
}

export interface WindowSearchResult {
  search_parameters: any;
  total_evaluated_windows: number;
  passing_windows_count: number;
  recommended_windows: CandidateWindow[];
  alternative_windows: CandidateWindow[];
  best_window: CandidateWindow | null;
  explanation: string;
}

export interface ContingencyResult {
  year: number;
  criteria: {
    min_sun_days: number;
    min_joint_days: number;
  };
  primary_site: any;
  primary_passed: boolean;
  recommended_backups: any[];
  failing_candidates: any[];
  provenance: Record<string, string>;
}
