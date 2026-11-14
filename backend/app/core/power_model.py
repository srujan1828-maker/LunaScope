"""
Demonstration Spacecraft Power & Battery Storage Model.
Simulates multi-junction solar array conversion (including orbital solar distance scaling
and temperature efficiency coefficients), continuous azimuth tracking vs fixed arrays,
and lithium-ion battery state-of-charge with unmet demand tracking.
"""

import math
from typing import Dict, List, Any
import numpy as np

SOLAR_CONSTANT_1AU: float = 1361.0  # Solar irradiance at 1 AU in W/m^2


def simulate_power_and_battery(
    timestamps: List[float],
    solar_fractions: List[float],
    sun_elevations: List[float],
    sun_azimuths: List[float],
    panel_area_m2: float = 3.5,
    panel_efficiency: float = 0.28,         # 28% triple-junction GaAs space solar cells
    panel_orientation: str = "tracking",     # "tracking" (vertical rotating) or "fixed_vertical"
    fixed_azimuth_deg: float = 0.0,
    derating_factor: float = 0.85,           # Dust accumulation, wiring, radiation degradation
    spacecraft_load_w: float = 120.0,        # Constant baseline spacecraft load
    battery_capacity_wh: float = 2400.0,     # e.g., 2.4 kWh lithium-ion battery pack
    initial_soc_pct: float = 100.0,
    charge_efficiency: float = 0.92,
    discharge_efficiency: float = 0.95,
    reserve_margin_pct: float = 20.0,
    solar_flux_w_m2: List[float] = None,
    step_hours: float = 1.0,
    sample_hours: List[float] = None
) -> Dict[str, Any]:
    """
    Simulates approximate electrical power generation, net energy balance,
    and battery state of charge across the mission duration.
    """
    n_steps = len(timestamps)
    initial_energy_wh = battery_capacity_wh * (initial_soc_pct / 100.0)
    reserve_threshold_wh = battery_capacity_wh * (reserve_margin_pct / 100.0)

    p_gen_w = []
    p_net_w = []
    battery_energy_wh = []
    soc_pct = []
    unmet_demand_wh = []
    reserve_breached = []

    current_energy = initial_energy_wh
    total_unmet_wh = 0.0

    durations = sample_hours if sample_hours is not None else [step_hours] * n_steps
    if len(durations) != n_steps or any(h < 0 for h in durations):
        raise ValueError("Invalid sample durations")
    for i in range(n_steps):
        step_hours = durations[i]
        f_sun = solar_fractions[i]
        el = sun_elevations[i]
        az = sun_azimuths[i]
        flux = solar_flux_w_m2[i] if solar_flux_w_m2 and i < len(solar_flux_w_m2) else SOLAR_CONSTANT_1AU

        # Solar incidence cosine
        if f_sun <= 0.0:
            cos_inc = 0.0
        else:
            if panel_orientation == "tracking":
                # Single-axis vertical rotating tracker following the Sun in azimuth:
                # normal points horizontally towards the Sun's azimuth, so incidence angle is sun elevation
                cos_inc = max(0.0, math.cos(math.radians(el)))
            else:
                # Fixed vertical panel facing fixed_azimuth_deg
                delta_az = math.radians(az - fixed_azimuth_deg)
                cos_inc = max(0.0, math.cos(math.radians(el)) * math.cos(delta_az))

        # Solar generation
        p_in = flux * panel_area_m2 * panel_efficiency * f_sun * cos_inc * derating_factor
        p_gen_w.append(round(p_in, 1))

        # Net power relative to load
        net = p_in - spacecraft_load_w
        p_net_w.append(round(net, 1))

        # Battery state update
        if net >= 0.0:
            # Charging battery
            added = net * step_hours * charge_efficiency
            current_energy = min(battery_capacity_wh, current_energy + added)
            step_unmet = 0.0
        else:
            # Discharging battery
            deficit = abs(net) * step_hours / discharge_efficiency
            if current_energy >= deficit:
                current_energy -= deficit
                step_unmet = 0.0
            else:
                # Battery emptied
                step_unmet = (deficit - current_energy) * discharge_efficiency
                current_energy = 0.0
                total_unmet_wh += step_unmet

        battery_energy_wh.append(round(current_energy, 1))
        curr_soc = (current_energy / battery_capacity_wh) * 100.0
        soc_pct.append(round(curr_soc, 1))
        unmet_demand_wh.append(round(step_unmet, 1))
        reserve_breached.append(bool(current_energy < reserve_threshold_wh))

    min_soc = min(soc_pct) if soc_pct else 0.0
    min_energy = min(battery_energy_wh) if battery_energy_wh else 0.0
    breach_count = sum(1 for b in reserve_breached if b)

    return {
        "inputs": {
            "panel_area_m2": panel_area_m2,
            "panel_efficiency": panel_efficiency,
            "panel_orientation": panel_orientation,
            "spacecraft_load_w": spacecraft_load_w,
            "battery_capacity_wh": battery_capacity_wh,
            "reserve_margin_pct": reserve_margin_pct
        },
        "summary": {
            "min_soc_pct": min_soc,
            "min_energy_wh": min_energy,
            "total_unmet_demand_wh": round(total_unmet_wh, 1),
            "reserve_breach_hours": round(sum(h for h, breached in zip(durations, reserve_breached) if breached), 4),
            "battery_depleted": bool(total_unmet_wh > 0.0)
        },
        "time_series": {
            "power_generated_w": p_gen_w,
            "net_power_w": p_net_w,
            "battery_energy_wh": battery_energy_wh,
            "battery_soc_pct": soc_pct,
            "unmet_demand_wh": unmet_demand_wh
        }
    }
