"""
Unit tests for power and battery SoC simulation.
"""

from app.core.power_model import simulate_power_and_battery


def test_power_and_battery_simulation():
    # 24 hour simulation: 12h sun, 12h shadow
    timestamps = [float(i * 3600) for i in range(24)]
    solar_fractions = [1.0] * 12 + [0.0] * 12
    sun_elevations = [1.5] * 24
    sun_azimuths = [float(i * 15) for i in range(24)]
    
    sim = simulate_power_and_battery(
        timestamps=timestamps,
        solar_fractions=solar_fractions,
        sun_elevations=sun_elevations,
        sun_azimuths=sun_azimuths,
        panel_area_m2=4.0,
        spacecraft_load_w=100.0,
        battery_capacity_wh=2000.0,
        initial_soc_pct=100.0
    )
    
    assert len(sim["time_series"]["power_generated_w"]) == 24
    # First 12h generate power
    assert sim["time_series"]["power_generated_w"][0] > 500.0
    # Last 12h have 0 power generated
    assert sim["time_series"]["power_generated_w"][13] == 0.0
    # Battery discharges during shadow
    assert sim["time_series"]["battery_energy_wh"][-1] < sim["time_series"]["battery_energy_wh"][12]
