"""
Pydantic Request and Response Schemas for LunaScope REST API.
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import ConfigDict, model_validator
from pydantic import BaseModel, Field


class ValidatedRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    @model_validator(mode='after')
    def validate_inputs(self):
        for start_key, end_key in [('start_time_iso', 'end_time_iso'), ('search_start_iso', 'search_end_iso')]:
            if not hasattr(self, start_key):
                continue
            start = datetime.fromisoformat(getattr(self, start_key).replace('Z', '+00:00'))
            end = datetime.fromisoformat(getattr(self, end_key).replace('Z', '+00:00'))
            if start.tzinfo is None or end.tzinfo is None:
                raise ValueError('Dates must include a UTC offset or Z')
            if not 2025 <= start.year <= 2032 or not 2025 <= end.year <= 2033:
                raise ValueError('Supported mission years: 2025 through 2032')
            if not 0 < (end-start).total_seconds() <= 366*86400:
                raise ValueError('Window must be positive and at most 366 days')
        if hasattr(self, 'site_ids'):
            from app.data.sites_catalog import get_site_by_id
            if len(set(self.site_ids)) != len(self.site_ids) or any(not get_site_by_id(s) for s in self.site_ids):
                raise ValueError('Sites must be unique known catalog IDs')
        if hasattr(self, 'site_id'):
            from app.data.sites_catalog import get_site_by_id
            if not get_site_by_id(self.site_id):
                raise ValueError('Unknown site')
        if hasattr(self, 'mast_heights') and (not 1 <= len(self.mast_heights) <= 20 or any(not 0.5 <= h <= 30 for h in self.mast_heights)):
            raise ValueError('Provide 1 to 20 finite mast heights between 0.5 and 30m')
        return self


class PowerConfig(ValidatedRequest):
    enabled: bool = False
    panel_area_m2: float = Field(3.5, gt=0, le=10000)
    panel_efficiency: float = Field(0.28, gt=0, le=1)
    panel_orientation: Literal["tracking", "fixed_vertical"] = "tracking"
    spacecraft_load_w: float = Field(120.0, ge=0, le=1000000)
    battery_capacity_wh: float = Field(2400.0, gt=0, le=100000000)
    initial_soc_pct: float = Field(100.0, ge=0, le=100)
    reserve_margin_pct: float = Field(20.0, ge=0, le=100)
    fixed_azimuth_deg: float = Field(0,ge=0,le=360)
    derating_factor: float = Field(.85,gt=0,le=1)
    charge_efficiency: float = Field(.92,gt=0,le=1)
    discharge_efficiency: float = Field(.95,gt=0,le=1)


class EvaluateScenarioRequest(ValidatedRequest):
    site_ids: List[str] = Field(..., min_length=1, max_length=3)
    start_time_iso: str = Field(default="2027-01-01T00:00:00Z")
    end_time_iso: str = Field(default="2027-01-14T00:00:00Z")
    mast_height_m: float = Field(default=2.0, ge=0.5, le=30.0)
    antenna_margin_deg: float = Field(default=0.0, ge=0.0, le=10.0)
    sun_threshold: float = Field(default=0.10, ge=0.01, le=1.0)
    power_config: Optional[PowerConfig] = None


class SearchWindowsRequest(ValidatedRequest):
    site_ids: List[str] = Field(..., min_length=1, max_length=3)
    search_start_iso: str = Field(default="2027-01-01T00:00:00Z")
    search_end_iso: str = Field(default="2027-02-15T00:00:00Z")
    mission_duration_days: float = Field(default=7.0, ge=1.0, le=30.0)
    stride_hours: float = Field(default=12.0, ge=1.0, le=48.0)
    min_sun_pct: float = Field(default=60.0, ge=0.0, le=100.0)
    max_shadow_gap_hours: float = Field(default=18.0, ge=0.0, le=200.0)
    min_earth_pct: float = Field(default=50.0, ge=0.0, le=100.0)
    max_earth_outage_hours: float = Field(default=36.0, ge=0.0, le=200.0)
    min_joint_pct: float = Field(default=40.0, ge=0.0, le=100.0)
    priority: Literal["balanced", "favour_sun", "favour_earth", "minimise_interruptions"] = "balanced"
    mast_height_m: float = Field(default=2.0, ge=0.5, le=30.0)


class ContingencyRequest(ValidatedRequest):
    primary_site_id: str
    year: int = Field(default=2027, ge=2025, le=2032)
    min_sun_days: float = Field(default=7.0, ge=0.0, le=30.0)
    min_joint_days: float = Field(default=5.0, ge=0.0, le=30.0)


class SaveScenarioRequest(BaseModel):
    title: str = "LunaScope Scenario"
    notes: Optional[str] = ""
    site_ids: List[str]
    inputs: Dict[str, Any]
    sites_evaluation: Dict[str, Any]
    comparative_insights: List[str]
    provenance: Dict[str, Any]


class DispersionRequest(ValidatedRequest):
    site_id: str
    start_time_iso: str = "2027-01-01T00:00:00Z"
    end_time_iso: str = "2027-01-08T00:00:00Z"
    semi_major_m: float = Field(default=200.0, ge=50.0, le=2000.0)
    semi_minor_m: float = Field(default=100.0, ge=25.0, le=1000.0)
    num_samples: int = Field(default=24, ge=5, le=100)
    mast_height_m: float = Field(default=2.0, ge=0.5, le=30.0)


class MastSensitivityRequest(ValidatedRequest):
    site_id: str
    start_time_iso: str = "2027-01-01T00:00:00Z"
    end_time_iso: str = "2027-01-08T00:00:00Z"
    mast_heights: List[float] = Field(default=[0.5, 1.0, 2.0, 3.5, 5.0, 7.5, 10.0, 15.0])

