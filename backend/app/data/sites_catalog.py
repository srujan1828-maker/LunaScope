"""
Catalog of Artemis candidate landing sites and lunar South Pole exploration zones.
Illustrative hard-coded metrics, inspired by lunar research; not verified source data.
"""

from typing import Dict, List, Any

# Demonstration sites and assumed multi-year metrics (2025-2032).
SITES_CATALOG: List[Dict[str, Any]] = [
    {
        "site_id": "shackleton-connecting-ridge",
        "name": "Shackleton Connecting Ridge",
        "region": "Connecting Ridge",
        "lat_deg": -89.44,
        "lon_deg": 222.70,
        "elevation_m": 1920.0,
        "description": "High ridge linking Shackleton crater with de Gerlache crater rim. Outstanding elevation above local craters offering prolonged sunlight.",
        "psr_distance_km": 1.2,
        "scientific_significance": "Direct access to deep PSR cold traps while retaining periodic direct-to-Earth line of sight.",
        "annual_data": {
            "2025": {"max_consec_sun_days": 14.8, "max_consec_joint_days": 11.2, "annual_illum_fraction": 0.68},
            "2026": {"max_consec_sun_days": 13.5, "max_consec_joint_days": 10.1, "annual_illum_fraction": 0.65},
            "2027": {"max_consec_sun_days": 15.2, "max_consec_joint_days": 11.8, "annual_illum_fraction": 0.71},
            "2028": {"max_consec_sun_days": 14.0, "max_consec_joint_days": 9.8, "annual_illum_fraction": 0.66},
            "2029": {"max_consec_sun_days": 16.1, "max_consec_joint_days": 12.4, "annual_illum_fraction": 0.74},
            "2030": {"max_consec_sun_days": 15.0, "max_consec_joint_days": 11.0, "annual_illum_fraction": 0.69},
            "2031": {"max_consec_sun_days": 13.9, "max_consec_joint_days": 9.5, "annual_illum_fraction": 0.64},
            "2032": {"max_consec_sun_days": 14.7, "max_consec_joint_days": 10.8, "annual_illum_fraction": 0.67},
        }
    },
    {
        "site_id": "peak-near-shackleton",
        "name": "Peak Near Shackleton",
        "region": "Shackleton Crater",
        "lat_deg": -89.70,
        "lon_deg": 128.00,
        "elevation_m": 1450.0,
        "description": "Isolated topographic high 10 km from the South Pole on the rim of Shackleton.",
        "psr_distance_km": 0.8,
        "scientific_significance": "Extremely close to the geometric pole; experiences near-horizontal grazing solar illumination.",
        "annual_data": {
            "2025": {"max_consec_sun_days": 11.2, "max_consec_joint_days": 8.0, "annual_illum_fraction": 0.58},
            "2026": {"max_consec_sun_days": 10.4, "max_consec_joint_days": 7.2, "annual_illum_fraction": 0.55},
            "2027": {"max_consec_sun_days": 12.1, "max_consec_joint_days": 8.7, "annual_illum_fraction": 0.61},
            "2028": {"max_consec_sun_days": 10.9, "max_consec_joint_days": 7.4, "annual_illum_fraction": 0.56},
            "2029": {"max_consec_sun_days": 12.8, "max_consec_joint_days": 9.1, "annual_illum_fraction": 0.63},
            "2030": {"max_consec_sun_days": 11.5, "max_consec_joint_days": 8.2, "annual_illum_fraction": 0.59},
            "2031": {"max_consec_sun_days": 10.2, "max_consec_joint_days": 6.9, "annual_illum_fraction": 0.53},
            "2032": {"max_consec_sun_days": 11.0, "max_consec_joint_days": 7.8, "annual_illum_fraction": 0.57},
        }
    },
    {
        "site_id": "malapert-mountain",
        "name": "Malapert Mountain Massif",
        "region": "Malapert Mountain",
        "lat_deg": -85.99,
        "lon_deg": 0.05,
        "elevation_m": 5050.0,
        "description": "Enormous massif rising over 5 km above the surrounding terrain. Known for continuous Earth line-of-sight.",
        "psr_distance_km": 14.5,
        "scientific_significance": "Premier candidate for early comms relay / lunar base due to near 100% Earth visibility and high solar exposure.",
        "annual_data": {
            "2025": {"max_consec_sun_days": 21.5, "max_consec_joint_days": 20.8, "annual_illum_fraction": 0.88},
            "2026": {"max_consec_sun_days": 20.2, "max_consec_joint_days": 19.5, "annual_illum_fraction": 0.85},
            "2027": {"max_consec_sun_days": 22.8, "max_consec_joint_days": 22.1, "annual_illum_fraction": 0.91},
            "2028": {"max_consec_sun_days": 21.0, "max_consec_joint_days": 20.1, "annual_illum_fraction": 0.87},
            "2029": {"max_consec_sun_days": 23.4, "max_consec_joint_days": 22.9, "annual_illum_fraction": 0.93},
            "2030": {"max_consec_sun_days": 22.0, "max_consec_joint_days": 21.3, "annual_illum_fraction": 0.89},
            "2031": {"max_consec_sun_days": 19.8, "max_consec_joint_days": 18.9, "annual_illum_fraction": 0.83},
            "2032": {"max_consec_sun_days": 21.2, "max_consec_joint_days": 20.4, "annual_illum_fraction": 0.86},
        }
    },
    {
        "site_id": "haworth-crater-rim",
        "name": "Haworth Crater Rim",
        "region": "Haworth",
        "lat_deg": -87.87,
        "lon_deg": 354.71,
        "elevation_m": -320.0,
        "description": "Depressed rim section on northern edge of Haworth crater with adjacent volatile-rich permanent shadows.",
        "psr_distance_km": 0.5,
        "scientific_significance": "Direct science target for volatile prospecting, but susceptible to deep crater wall shadow occultations.",
        "annual_data": {
            "2025": {"max_consec_sun_days": 5.8, "max_consec_joint_days": 4.1, "annual_illum_fraction": 0.36},
            "2026": {"max_consec_sun_days": 4.9, "max_consec_joint_days": 3.4, "annual_illum_fraction": 0.32},
            "2027": {"max_consec_sun_days": 6.4, "max_consec_joint_days": 4.8, "annual_illum_fraction": 0.40},
            "2028": {"max_consec_sun_days": 5.2, "max_consec_joint_days": 3.7, "annual_illum_fraction": 0.34},
            "2029": {"max_consec_sun_days": 7.0, "max_consec_joint_days": 5.3, "annual_illum_fraction": 0.43},
            "2030": {"max_consec_sun_days": 6.1, "max_consec_joint_days": 4.5, "annual_illum_fraction": 0.38},
            "2031": {"max_consec_sun_days": 4.5, "max_consec_joint_days": 3.0, "annual_illum_fraction": 0.30},
            "2032": {"max_consec_sun_days": 5.4, "max_consec_joint_days": 3.9, "annual_illum_fraction": 0.35},
        }
    },
    {
        "site_id": "faustini-rim",
        "name": "Faustini Crater Rim A",
        "region": "Faustini",
        "lat_deg": -87.18,
        "lon_deg": 84.34,
        "elevation_m": 1240.0,
        "description": "Eastern elevated flank of Faustini Crater overlooking deep interior ice deposits.",
        "psr_distance_km": 2.1,
        "scientific_significance": "Balanced site for surface power and proximity to high volatile probability zones.",
        "annual_data": {
            "2025": {"max_consec_sun_days": 9.4, "max_consec_joint_days": 7.0, "annual_illum_fraction": 0.51},
            "2026": {"max_consec_sun_days": 8.5, "max_consec_joint_days": 6.2, "annual_illum_fraction": 0.48},
            "2027": {"max_consec_sun_days": 10.2, "max_consec_joint_days": 7.8, "annual_illum_fraction": 0.54},
            "2028": {"max_consec_sun_days": 9.0, "max_consec_joint_days": 6.6, "annual_illum_fraction": 0.49},
            "2029": {"max_consec_sun_days": 11.0, "max_consec_joint_days": 8.4, "annual_illum_fraction": 0.57},
            "2030": {"max_consec_sun_days": 9.8, "max_consec_joint_days": 7.3, "annual_illum_fraction": 0.52},
            "2031": {"max_consec_sun_days": 8.0, "max_consec_joint_days": 5.8, "annual_illum_fraction": 0.45},
            "2032": {"max_consec_sun_days": 9.1, "max_consec_joint_days": 6.8, "annual_illum_fraction": 0.50},
        }
    },
    {
        "site_id": "nobile-rim-1",
        "name": "Nobile Crater Rim 1",
        "region": "Nobile",
        "lat_deg": -85.25,
        "lon_deg": 35.80,
        "elevation_m": 3700.0,
        "description": "Prominent massif on the western rim of Nobile crater. VIPER rover primary region of interest.",
        "psr_distance_km": 3.4,
        "scientific_significance": "High terrain with extensive rover trafficability and reliable DTE links.",
        "annual_data": {
            "2025": {"max_consec_sun_days": 18.2, "max_consec_joint_days": 16.5, "annual_illum_fraction": 0.79},
            "2026": {"max_consec_sun_days": 17.0, "max_consec_joint_days": 15.2, "annual_illum_fraction": 0.75},
            "2027": {"max_consec_sun_days": 19.4, "max_consec_joint_days": 17.8, "annual_illum_fraction": 0.83},
            "2028": {"max_consec_sun_days": 17.8, "max_consec_joint_days": 16.0, "annual_illum_fraction": 0.77},
            "2029": {"max_consec_sun_days": 20.3, "max_consec_joint_days": 18.7, "annual_illum_fraction": 0.86},
            "2030": {"max_consec_sun_days": 18.8, "max_consec_joint_days": 17.1, "annual_illum_fraction": 0.81},
            "2031": {"max_consec_sun_days": 16.5, "max_consec_joint_days": 14.8, "annual_illum_fraction": 0.73},
            "2032": {"max_consec_sun_days": 17.9, "max_consec_joint_days": 16.2, "annual_illum_fraction": 0.78},
        }
    },
    {
        "site_id": "de-gerlache-rim-1",
        "name": "de Gerlache Crater Rim 1",
        "region": "de Gerlache",
        "lat_deg": -88.71,
        "lon_deg": 291.62,
        "elevation_m": 680.0,
        "description": "Narrow crest along the northeastern rim of de Gerlache crater.",
        "psr_distance_km": 1.8,
        "scientific_significance": "Adjacent to extensive cold traps; subject to periodic occultation by Shackleton massif.",
        "annual_data": {
            "2025": {"max_consec_sun_days": 8.7, "max_consec_joint_days": 6.5, "annual_illum_fraction": 0.49},
            "2026": {"max_consec_sun_days": 7.9, "max_consec_joint_days": 5.8, "annual_illum_fraction": 0.46},
            "2027": {"max_consec_sun_days": 9.5, "max_consec_joint_days": 7.2, "annual_illum_fraction": 0.52},
            "2028": {"max_consec_sun_days": 8.3, "max_consec_joint_days": 6.1, "annual_illum_fraction": 0.47},
            "2029": {"max_consec_sun_days": 10.1, "max_consec_joint_days": 7.8, "annual_illum_fraction": 0.55},
            "2030": {"max_consec_sun_days": 9.0, "max_consec_joint_days": 6.8, "annual_illum_fraction": 0.50},
            "2031": {"max_consec_sun_days": 7.5, "max_consec_joint_days": 5.3, "annual_illum_fraction": 0.43},
            "2032": {"max_consec_sun_days": 8.4, "max_consec_joint_days": 6.3, "annual_illum_fraction": 0.48},
        }
    },
    {
        "site_id": "leibnitz-beta-plateau",
        "name": "Leibnitz Beta Plateau",
        "region": "Leibnitz Beta",
        "lat_deg": -85.80,
        "lon_deg": 330.50,
        "elevation_m": 4400.0,
        "description": "Spacious elevated plateau at the edge of the South Pole-Aitken basin.",
        "psr_distance_km": 8.0,
        "scientific_significance": "Wide flat landing areas with sustained high elevation and strong Earth link continuity.",
        "annual_data": {
            "2025": {"max_consec_sun_days": 17.5, "max_consec_joint_days": 15.8, "annual_illum_fraction": 0.77},
            "2026": {"max_consec_sun_days": 16.3, "max_consec_joint_days": 14.6, "annual_illum_fraction": 0.73},
            "2027": {"max_consec_sun_days": 18.6, "max_consec_joint_days": 17.0, "annual_illum_fraction": 0.81},
            "2028": {"max_consec_sun_days": 17.0, "max_consec_joint_days": 15.2, "annual_illum_fraction": 0.75},
            "2029": {"max_consec_sun_days": 19.5, "max_consec_joint_days": 18.0, "annual_illum_fraction": 0.84},
            "2030": {"max_consec_sun_days": 18.0, "max_consec_joint_days": 16.4, "annual_illum_fraction": 0.79},
            "2031": {"max_consec_sun_days": 15.8, "max_consec_joint_days": 14.0, "annual_illum_fraction": 0.71},
            "2032": {"max_consec_sun_days": 17.1, "max_consec_joint_days": 15.5, "annual_illum_fraction": 0.76},
        }
    },
    {
        "site_id": "amundsen-rim",
        "name": "Amundsen Crater Rim",
        "region": "Amundsen",
        "lat_deg": -84.50,
        "lon_deg": 85.00,
        "elevation_m": 2100.0,
        "description": "Northern rim of Amundsen crater featuring ancient impact melt sheets and central peak complexes.",
        "psr_distance_km": 5.6,
        "scientific_significance": "Exposes deep lunar crustal material with high scientific sample return value.",
        "annual_data": {
            "2025": {"max_consec_sun_days": 14.1, "max_consec_joint_days": 12.3, "annual_illum_fraction": 0.65},
            "2026": {"max_consec_sun_days": 13.0, "max_consec_joint_days": 11.2, "annual_illum_fraction": 0.62},
            "2027": {"max_consec_sun_days": 15.0, "max_consec_joint_days": 13.2, "annual_illum_fraction": 0.69},
            "2028": {"max_consec_sun_days": 13.6, "max_consec_joint_days": 11.8, "annual_illum_fraction": 0.64},
            "2029": {"max_consec_sun_days": 16.0, "max_consec_joint_days": 14.2, "annual_illum_fraction": 0.72},
            "2030": {"max_consec_sun_days": 14.5, "max_consec_joint_days": 12.7, "annual_illum_fraction": 0.67},
            "2031": {"max_consec_sun_days": 12.5, "max_consec_joint_days": 10.6, "annual_illum_fraction": 0.59},
            "2032": {"max_consec_sun_days": 13.8, "max_consec_joint_days": 12.0, "annual_illum_fraction": 0.64},
        }
    },
    {
        "site_id": "slater-plain",
        "name": "Slater Basin Floor",
        "region": "Slater",
        "lat_deg": -88.10,
        "lon_deg": 115.00,
        "elevation_m": -1100.0,
        "description": "Low-elevation floor region south of Faustini, surrounded by high crater rims.",
        "psr_distance_km": 0.2,
        "scientific_significance": "Rich in shadowed cryo-traps, but suffers severe terrain occultation for both Sun and Earth.",
        "annual_data": {
            "2025": {"max_consec_sun_days": 3.2, "max_consec_joint_days": 1.5, "annual_illum_fraction": 0.22},
            "2026": {"max_consec_sun_days": 2.6, "max_consec_joint_days": 1.1, "annual_illum_fraction": 0.19},
            "2027": {"max_consec_sun_days": 3.8, "max_consec_joint_days": 2.0, "annual_illum_fraction": 0.26},
            "2028": {"max_consec_sun_days": 3.0, "max_consec_joint_days": 1.3, "annual_illum_fraction": 0.21},
            "2029": {"max_consec_sun_days": 4.5, "max_consec_joint_days": 2.6, "annual_illum_fraction": 0.30},
            "2030": {"max_consec_sun_days": 3.5, "max_consec_joint_days": 1.8, "annual_illum_fraction": 0.24},
            "2031": {"max_consec_sun_days": 2.2, "max_consec_joint_days": 0.8, "annual_illum_fraction": 0.17},
            "2032": {"max_consec_sun_days": 3.1, "max_consec_joint_days": 1.4, "annual_illum_fraction": 0.21},
        }
    }
]


def get_sites_catalog() -> List[Dict[str, Any]]:
    """Return the complete list of candidate sites."""
    from copy import deepcopy
    return deepcopy(SITES_CATALOG)


def get_site_by_id(site_id: str) -> Dict[str, Any] | None:
    """Retrieve site metadata by site_id."""
    for site in SITES_CATALOG:
        if site["site_id"] == site_id:
            from copy import deepcopy
            return deepcopy(site)
    return None

for _site in SITES_CATALOG:
    _site['provenance'] = 'Assumed / demonstration catalog; unverified coordinates and annual metrics'
    _site['terrain_safety'] = 'unknown'
