# LunaScope

### Lunar south-pole terrain, illumination and surface-operation analysis

LunaScope is an independent NASA International Space Apps Challenge project that combines **official NASA LRO/LOLA topography**, **NASA/JPL SPICE geometry**, an interactive **Three.js terrain explorer**, and explainable mission-window analysis.

Choose a measured terrain location, select a UTC date, explore its elevation surface, follow the calculated Sun and Earth directions, and compare illumination, geometric Earth visibility and configurable electrical-power estimates across locations.

**The production terrain comes from downloaded scientific files. Missing scientific inputs are reported as unavailable; no synthetic terrain dataset is substituted.** The application remains an exploratory analysis and visualization tool. Official source data and passing software tests do not establish flight qualification, landing safety, a communications link, or NASA endorsement.

## Contents

- [Project status and recorded results](#project-status-and-recorded-results)
- [Features and workflow](#features-and-workflow)
- [Data authenticity and provenance](#data-authenticity-and-provenance)
- [Analysis locations and reproducibility](#analysis-locations-and-reproducibility)
- [Scientific methods](#scientific-methods)
- [Power and battery model](#power-and-battery-model)
- [Validation and test results](#validation-and-test-results)
- [Installation and startup on Windows](#installation-and-startup-on-windows)
- [Optional high-resolution terrain](#optional-high-resolution-terrain)
- [API and real-time interfaces](#api-and-real-time-interfaces)
- [Cloud deployment](#cloud-deployment)
- [Architecture and data management](#architecture-and-data-management)
- [Limitations and unsupported claims](#limitations-and-unsupported-claims)
- [Troubleshooting](#troubleshooting)
- [NASA Space Apps context and acknowledgements](#nasa-space-apps-context-and-acknowledgements)

## Project status and recorded results

The following results were recorded on **15 November 2026**. They describe checks that were actually run, with their scope and limitations explained later in this document.

| Check | Recorded result |
|---|---|
| Complete backend suite after the exact-pole correction | **64 passed**, one dependency deprecation warning, **144.01 seconds** |
| Earlier complete backend run | **64 passed** in **59.29 seconds**; execution time varies with local load |
| Source-file integrity | **7/7** installed inputs matched recorded byte counts and SHA-256 hashes; rechecked during this README update |
| Catalog authenticity | All **13** catalog elevations checked against original JP2 raster pixels |
| Independent astronomy comparison | **12** Sun/Earth direction comparisons against JPL Horizons passed the selected **0.02°** tolerance |
| Largest recorded Horizons angular difference | **0.00003258584379173257°** across the checked azimuth/elevation values |
| Frontend production build | Style compilation, strict TypeScript checking and Vite build passed |
| Browser interaction checks | Terrain loading/picking, UTC controls, playback, comparison, power controls, exports and window-finder behavior passed |
| Mobile layout | All **6** routes checked at **390 × 844**, without horizontal page overflow |
| Browser errors in the recorded surface checks | **0** JavaScript page errors; **0** console errors |
| Linux production container | Image build and readiness/frontend/surface smoke tests passed in GitHub Actions |
| Live hosted cloud instance | **Not created**; deployment configuration and a tested container are provided |
| Optional NASA PGDA 5 m terrain | Download attempts timed out; **not installed** in the recorded setup |

The local scientific suite was run with Python 3.14 on Windows. The Linux workflow uses Python 3.12 and Node.js 22. The linked [successful Linux verification run](https://github.com/srujan1828-maker/LunaScope/actions/runs/43688943898) covers implementation commit `074af8f`. The subsequent exact-pole correction was checked by the complete local 64-test suite. This distinction matters when interpreting the CI evidence.

Detailed evidence and implementation history: [VERIFICATION.md](VERIFICATION.md), [UPGRADE_REPORT.md](UPGRADE_REPORT.md), and [SCIENTIFIC_UPGRADE.md](SCIENTIFIC_UPGRADE.md).

## Features and workflow

### Six connected pages

| Page | Purpose |
|---|---|
| Home | Introduces the workspace and opens the planning tools |
| Mission Planner | Sets mission dates, UTC start time, duration, sunlight and Earth-visibility requirements; evaluates, sorts and compares the catalog; selects primary and backup points |
| Horizon Simulator | Hosts the measured 3D terrain explorer, Sun/Earth readings, 360° terrain horizon, UTC playback, site comparison and advanced analysis tools |
| Timeline | Provides editable planning phases, dates, durations and schedule export; this is a planning schedule rather than a trajectory calculation |
| Educator Mode | Explains terrain clearance, sunlight and geometric Earth visibility with explicitly labeled conceptual diagrams |
| Data & Sources | Shows scientific sources, file provenance, saved Horizons comparison results and integration limitations |

### Measured 3D terrain explorer

- Generates terrain vertices from the installed elevation raster, including lunar curvature and a **1:1 vertical scale**.
- Supports orbiting, zooming, panning, an observer view, and camera views toward the calculated Sun or Earth.
- Lets users click a displayed DEM sample to inspect latitude, longitude, elevation and available height uncertainty, then analyze that location.
- Loads a coarse **33 × 33** crop before a **257 × 257** crop. The source pixel spacing and displayed mesh spacing are reported separately.
- Uses calculated Sun direction for local terrain lighting and shadow maps. Sun and Earth sky disks use calculated directions and angular sizes.
- Shows Earth as a phase-lit spherical body, without claiming to display observed weather or a current Earth image.
- Provides elevation colors and an optional **inspection fill light**. This viewing aid does not change calculated illumination or power.
- Preserves missing terrain cells as mesh holes. Missing horizon sectors propagate to Unknown visibility results.

The 3D mesh is a visualization of gridded/interpolated altimetry. Increasing the mesh density or zoom level cannot reveal terrain detail that the source raster does not contain.

### Planning and comparison tools

The mission planner includes reactive matching over WebSockets, with an HTTP fallback, explicit constraint violations, and no passing recommendation when every evaluated location fails. Up to three selected locations share comparison settings. The surface explorer synchronizes sky readings and horizons to one UTC, while period summaries show sunlight, Earth visibility, joint visibility, gaps, exposure and electrical estimates for the configured mission window.

The window finder exposes minimum Sun/Earth/joint availability, maximum shadow and Earth-outage durations, operation duration, allowed start-date range, start stride and ranking priority. Failed alternatives show their actual violations. Applying a window preserves its UTC hour and duration; the planner then evaluates its own configured requirements.

Additional tools include mast-height sensitivity, deterministic landing-position sensitivity, scenario JSON/CSV exports, a mission schedule export, and an optional advanced streamed simulation session. The streamed session is separate from the surface explorer's scene clock and initializes when opened.

## Data authenticity and provenance

### What is real, calculated, assumed or illustrative?

| Category | Used in LunaScope |
|---|---|
| **Published scientific inputs** | Downloaded NASA LRO/LOLA elevation raster and PDS label; NASA/JPL/NAIF ephemeris, lunar orientation, frame, leap-second and constants kernels |
| **Calculated from those inputs** | Terrain crops, elevation mesh, hillshade, analysis-point coordinates, regional slopes, horizon obstructions, Sun/Earth directions and distance-dependent angular sizes |
| **Model approximations** | Sampled terrain rays, angular-plane disk integration, finite temporal sampling, spherical Earth phase and graphical shadow maps |
| **User engineering assumptions** | Solar-panel configuration, efficiency, derating, electrical load, battery parameters and mission constraints |
| **Illustrative visuals** | Educator diagrams and the owner-supplied looping background MP4; neither is an observation dataset |
| **Synthetic test fixtures** | Artificial flat/ridge/crater/NoData landscapes used only in isolated unit tests; they are not the production terrain source |

The former procedural terrain, fabricated annual site table and synthetic Streamlit dataset were removed from the active project. The current annual summaries are computed from scientific inputs, with their hourly temporal approximation disclosed below.

### Installed source files

The NASA LRO/LOLA product is distributed through the LOLA PDS archive hosted at MIT. The other five files come from NASA/JPL's NAIF archive. All original download URLs are recorded rather than replacing the scientific files with copied numbers or a generic lunar texture.

| Original file / download | Bytes | Integrated use |
|---|---:|---|
| [LDEM_80S_80M.JP2](https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/JP2/LDEM_80S_80M.JP2) | 29,837,992 | Regional elevation raster |
| [LDEM_80S_80M_JP2.LBL](https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/JP2/LDEM_80S_80M_JP2.LBL) | 6,354 | Original product scaling, projection and frame metadata |
| [de421.bsp](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp) | 16,790,528 | Planetary ephemeris (SPK) |
| [moon_pa_de421_1900-2050.bpc](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de421_1900-2050.bpc) | 1,770,496 | Binary lunar orientation (PCK) |
| [moon_080317.tf](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf) | 21,437 | Lunar frame definitions (FK) |
| [naif0012.tls](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls) | 5,257 | UTC/leap-second conversion (LSK) |
| [pck00011.tpc](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc) | 131,226 | Planetary constants (text PCK) |

Recorded retrieval time: **2026-11-14 17:59:49.494776 UTC**. The seven original inputs total **48,563,290 bytes**, approximately **46.31 MiB**. The prepared NumPy raster occupies **115,520,128 bytes**, approximately **110.17 MiB**. Additional disk space is needed for dependencies, caches and optional terrain.

### Terrain metadata

| Property | Installed regional product |
|---|---|
| Mission / instrument | Lunar Reconnaissance Orbiter / Lunar Orbiter Laser Altimeter (LRO/LOLA) |
| PDS dataset | `LRO-L-LOLA-4-GDR-V1.0` |
| Product / version | `LDEM_80S_80M`, V2.1 |
| Raster dimensions | `7600 × 7600` |
| Stored sample type | Signed 16-bit integer |
| Height scale | `0.5 m` per stored unit |
| Reference sphere radius | `1,737,400 m` |
| Source pixel scale | `80 m/pixel` |
| Projection | Lunar south-polar stereographic, metres |
| Lunar reference frame | `MOON_ME_DE421` |
| Terrain height uncertainty | **Unknown** for the installed regional grid; no per-cell error product has been integrated for it |
| Effective resolution | **Unknown**; pixel spacing alone is not an effective-resolution measurement |

The original [PDS label](https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/JP2/LDEM_80S_80M_JP2.LBL) is retained and inspected for projection/frame, scaling and offsets. For this product:

```text
elevation above the reference sphere, metres = stored pixel value × 0.5
radius from the lunar center, metres         = 1,737,400 + elevation
```

The map overview is a **400 m/sample hillshade derived from the 80 m raster**. The 3D view reports its separate mesh sampling distance. These display products do not increase the underlying terrain resolution.

### Integrity records and their meaning

[data/nasa_provenance.json](data/nasa_provenance.json) records source URLs, retrieval time, byte counts and SHA-256 hashes. A runtime manifest is written to the scientific-data directory. The original rasters, kernels and decoded raster remain local and are excluded from Git; the source records, derived catalog, derived hillshade and validation fixtures are tracked.

<details>
<summary>Recorded SHA-256 hashes for all seven source files</summary>

| File | SHA-256 |
|---|---|
| `LDEM_80S_80M.JP2` | `c088dd4f510e879375ee7e6f0d320ba84115f535f45fb592dd7f83a7d2e83ae3` |
| `LDEM_80S_80M_JP2.LBL` | `497512747bb56490d50cf3f4945f2cb736bf61cd19b65fa61a826825e2a35d79` |
| `de421.bsp` | `08b20db2ae22488650641c5a9033e5bfda4b1c4b440cfeaf20f621cfa18ecdb3` |
| `moon_pa_de421_1900-2050.bpc` | `656f90616403d75a75f0cd6c8830fc5b44f8cb4facb5ccb8915e752b397520cf` |
| `moon_080317.tf` | `78732477b96f9863e7b0d65bcee3c22b8707ca5ed0db56d1173319cb2e8c7993` |
| `naif0012.tls` | `678e32bdb5a744117a467cd9601cd6b373f0e9bc9bbde1371d5eee39600a039b` |
| `pck00011.tpc` | `3dff7b1dbeceaa01f25467767d3fa25816051c85d162d1edf04acb310ee28bb1` |

</details>

SHA-256 establishes that a local file matches the bytes recorded for this release. It does not, by itself, certify the publisher or the physical correctness of a dataset. Source authenticity also depends on retrieving the published files from the recorded NASA/PDS/NAIF archives and checking their metadata. These records are not presented as NASA-issued digital signatures.

The automated checks verify byte counts and hashes, compare all 13 catalog elevations with pixels read directly from the original JP2, and compare selected SPICE results with independently obtained Horizons responses. Those are different checks with different evidential scope.

### Verify your downloaded files locally

After setup, run this from the project root in PowerShell. It checks each original file against the tracked release manifest and respects `LUNASCOPE_DATA_DIR` if configured:

```powershell
@'
from pathlib import Path
import hashlib, json, os

root = Path.cwd()
raw = Path(os.environ.get('LUNASCOPE_DATA_DIR', str(root / 'data' / 'nasa')))
manifest = json.loads((root / 'data' / 'nasa_provenance.json').read_text(encoding='utf-8'))
for name, record in manifest['sources'].items():
    path = raw / name
    assert path.stat().st_size == record['bytes'], f'Size mismatch: {name}'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], f'Hash mismatch: {name}'
    print('PASS', name)
print('All seven original scientific inputs match the recorded release.')
'@ | .\.venv\Scripts\python.exe -
```

With automatic fetching enabled, cloud startup runs the downloader, which computes source-file hashes, and compares its resulting manifest with the tracked release identities. With fetching disabled, startup relies on the supplied manifest and prepared inputs; use the explicit check above when verifying an offline volume. Readiness checks report required-file availability and are not a substitute for a full integrity audit.

## Analysis locations and reproducibility

The catalog contains **13 LunaScope analysis points derived from real raster cells**. It is not NASA's official candidate-region list, a set of approved landing sites, or a globally optimized site-selection result.

[prepare_nasa_data.py](backend/scripts/prepare_nasa_data.py) selects points reproducibly:

1. Sample candidate rows and columns from `2320` through `5200`, stepping by 80 raster cells, equivalent to a 6.4 km candidate-grid spacing.
2. Retain candidates between 8 km and 120 km from the pole in the polar projection.
3. Derive a regional slope using central differences across the neighboring 80 m pixels; retain slopes no greater than 8°.
4. Sort candidates by descending elevation, with row/column tie-breaks.
5. Select the first 13 candidates satisfying at least 20 km projected separation.

The full coordinates, elevations, source pixels, slope estimates and original source URL are in [nasa_sites.json](backend/app/data/nasa_sites.json). `terrain_safety` remains `unknown`; the regional slope rule does not certify lander-scale slope, rock or touchdown safety. No unverified PSR-distance measurement is supplied.

Example traceable catalog point:

```text
ID:               lola-sp-001
Name:             LOLA South Pole 01
Latitude:         -86.56848542390216 degrees
Longitude:         45.03113900753911 degrees east
Elevation:         2214.0 m above the reference sphere
Original pixel:    row 2880, column 4720 (zero-based indices)
Product:           LDEM_80S_80M
Terrain safety:    Unknown
```

## Scientific methods

### Geometry, frames and time

SpiceyPy calls NAIF SPICE with the installed DE421 planetary ephemeris, matching lunar binary orientation and frame kernels. UTC input is converted to SPICE ephemeris time using the leap-second kernel. Sun/Earth vectors use `LT+S` light-time and stellar-aberration corrections in `MOON_ME_DE421`, then are translated to the local observer and projected into east/north/up coordinates.

The surface explorer and adaptive scenario engine include the sampled ground elevation and observer mast height. Sun/Earth angular sizes vary with calculated distance. The model treats their disks as spherical. Full observer-centered relativistic corrections and atmospheric effects are not modeled; the Moon-centered correction followed by observer translation is an explicit approximation.

The model uses a 695,700 km solar radius and a 6,378.137 km spherical Earth-disk radius. These fixed body-size assumptions are separate from the time-dependent SPICE vectors and distances; the Earth disk is not an ellipsoidal limb model.

Azimuth is clockwise from local north toward east. At the exact south pole, the selected longitude defines the reference north meridian. Great-circle terrain destinations use 3D ENU vectors to avoid the singular longitude formula at the pole. The regression test checks all four cardinal bearings.

### Terrain horizon

The regional horizon samples 360 local compass bearings at 1° spacing, out to 150 km. For the installed grid, radial samples begin at 80 m intervals near the observer and become coarser farther away. Spherical curvature and observer height are included. The maximum terrain elevation angle determines each sampled horizon value; the responsible terrain coordinate, elevation and distance are retained.

Horizon interpolation wraps at 0°/360°. Missing coverage is preserved rather than filled with invented elevations. A finite 1°/radial sampling scheme can miss narrow obstructions, and terrain beyond 150 km is outside this calculation's scope.

### Solar and Earth visibility

A 48-node strip quadrature integrates the apparent circular disk against the horizon as it varies across the disk's angular width. This is an angular-plane, spherical-disk approximation. Earth-center clearance, visible Earth-disk fraction and complete-disk clearance are separate readings.

The default operational Sun threshold is **10% visible solar disk**. The states are:

| State | Meaning |
|---|---|
| 1 | Sun meets threshold; Earth center clears terrain |
| 2 | Sun meets threshold; Earth center is blocked |
| 3 | Sun is below threshold; Earth center clears terrain |
| 4 | Sun is below threshold; Earth center is blocked |
| 0 / Unknown | Required terrain or visibility information is missing |

Earth-center clearance describes geometry, not an established radio link. Likewise, exposed solar-disk fraction is an illumination input, not electrical power by itself.

### Time sampling and metrics

Scenario evaluation and the operation-window finder use a **600-second baseline**, with adaptive bisection to **30-second brackets** around detected state changes and partial solar-disk grazing. Duration-weighted, left-endpoint integration clips the first/last overlapping intervals to the requested window, so fractional durations do not add an extra endpoint interval.

Reported metrics include Sun availability above the selected threshold, equivalent full-Sun exposure hours, longest continuous shadow gap, Earth-center availability, longest Earth outage, joint availability and longest joint window. Equivalent exposure integrates visible fraction; it is distinct from the percentage of time exceeding the Sun threshold.

The baseline can still miss interruptions shorter than 10 minutes if no sampled point reveals them. Adaptive refinement narrows detected-event brackets; it does not prove that every physical event has been detected.

Annual contingency, mast-height sweeps and spatial-dispersion summaries retain **hourly temporal sampling**. They use the scientific terrain/ephemeris inputs but have coarser time resolution than adaptive scenario/window analysis. Landing dispersion uses deterministic concentric elliptical samples and recalculates local terrain/geometry; it is not a Monte Carlo landing-survival probability.

### Window constraints and ranking

Each candidate start is evaluated over the entire requested operation duration. All selected locations must meet their configured hard constraints for the candidate to pass. Missing coverage yields Unknown, not Pass. Passing candidates are ranked first; failed alternatives retain their violations, without silently changing requirements.

Ranking uses the selected preset, averaged across selected locations. Let `S`, `E`, `J` be Sun, Earth and joint availability percentages, and `G`, `O` be longest shadow-gap and Earth-outage hours:

| Priority | Score |
|---|---|
| Balanced | `0.35S + 0.35E + 0.30J − 0.8G − 0.5O` |
| Favour sunlight | `0.60S + 0.30J − 1.5G` |
| Favour Earth | `0.60E + 0.30J − 1.5O` |
| Minimise interruptions | `0.50J − 2G − O` |

These are transparent ranking heuristics, not probabilities of mission success. The separate reactive site matcher uses its own documented coverage weights and selected mission constraints.

## Power and battery model

The optional electrical model accepts panel area and efficiency, vertical-panel azimuth tracking or fixed azimuth, derating, constant electrical load, battery capacity, initial charge, charge/discharge efficiency and reserve requirement.

| Hardware parameter | Default value |
|---|---:|
| Panel area | 3.5 m² |
| Panel efficiency | 0.28 |
| Orientation | Vertical panel tracking solar azimuth |
| Fixed-panel azimuth, when selected | 0° |
| Derating factor | 0.85 |
| Constant load | 120 W |
| Battery capacity | 2,400 Wh |
| Initial charge | 100% |
| Charge / discharge efficiency | 0.92 / 0.95 |
| Reserve requirement | 20% |

These defaults are assumptions, not NASA measurements or a declared spacecraft design. The API electrical model is opt-in; the frontend's initial power settings enable it. Saved browser settings can override initial defaults.

```text
generated power = solar irradiance × panel area × panel efficiency
                  × visible solar fraction × orientation factor × derating

surplus power charges the battery using the configured charge efficiency
power deficit draws from the battery using the configured discharge efficiency
battery energy is bounded between zero and configured capacity
remaining load shortfall is recorded as unmet demand
```

Irradiance uses inverse-square Sun-distance scaling around a **1,361 W/m² at 1 AU** reference. The `tracking` mode follows solar azimuth with a vertical panel; it is not a fully articulated two-axis Sun-normal tracker. A fixed vertical panel includes the difference between Sun azimuth and configured panel azimuth.

Outputs include estimated generation/load energy, instantaneous generation/net power series, battery energy and charge percentage, minimum charge, reserve-breach duration, reserve energy, unmet demand, charging/discharging states and longest duration without generation. These are configurable engineering estimates. They do not include a validated thermal-survival model, detailed spacecraft loads, battery aging, or certified flight performance.

## Validation and test results

### Complete automated suite

The latest recorded full run after the pole fix returned:

```text
python -m pytest backend/tests -q
64 passed, 1 warning in 144.01s (0:02:24)
```

The warning is a third-party Starlette/httpx test-client deprecation warning. Earlier passing timings include 59.29 seconds. These are observed execution times on one machine, not performance guarantees. Parameterized test cases contribute to the total of 64.

| Area | What was exercised |
|---|---|
| Source authenticity | Seven file sizes/hashes, recorded archive URLs, all thirteen catalog elevations against original JP2 pixels |
| Coordinates and frames | Polar projection round trips, distances, ENU basis, exact-pole reference meridian/cardinal bearings, DE421 frame identity |
| Terrain | Horizon ranges, mast sensitivity, isolated flat/ridge/crater cases, responsible obstructions, missing sectors, true mesh elevations and 1:1 scale |
| Visibility | Solar-disk boundaries/complements, changing skyline, azimuth wrap, Earth-center clearance, Unknown propagation and operational states |
| Time and windows | UTC requirements, adaptive event brackets, partial intervals, fractional 1.25-hour candidate stride, 27-hour operation duration, hard constraints and no false recommendation |
| Power | Energy accounting, disabled/enabled configuration, battery/reserve behavior, discharge efficiency and unmet demand |
| API and state | Validation errors, scenario immutability, saves/exports, static frontend assets, missing-data errors and liveness/readiness behavior |
| Real-time paths | REST/WebSocket matching agreement, command errors/recovery, site changes and retained hardware settings |
| Ingestion and failure handling | GeoTIFF metadata/window/NoData handling, incompatible frames and unreadable or incorrectly typed SPICE kernels |

Artificial test landscapes establish expected software behavior for controlled inputs. Passing them does not establish the accuracy of a real lunar terrain product or a spacecraft prediction.

### Independent JPL Horizons comparison

[data/validation/horizons_report.json](data/validation/horizons_report.json) and the four accompanying raw-response files preserve the query URLs, returned observer tables, comparison values and errors.

| Comparison property | Recorded scope |
|---|---|
| Bodies | Sun and Earth |
| Surface locations | `lola-sp-001` and `lola-sp-002` |
| Epochs | 2027-01-01 at 00:00, 01:00 and 02:00 UTC |
| Cases | 12 body/location/epoch cases, comparing azimuth and elevation |
| Application model | DE421 / `MOON_ME_DE421`, observer at raster elevation plus 2 m |
| Independent reference | JPL Horizons DE441 / high-precision `MEAN_ME` |
| Chosen tolerance | 0.02° for each checked direction component |
| Maximum recorded component difference | 0.00003258584379173257°, approximately 0.1173 arcseconds |
| Result | Passed for the recorded cases |

This is cross-ephemeris agreement for selected directions and times. It does not establish global accuracy across every date/location, validate graphical shadows, or validate terrain hazards and electrical/communication models.

### Frontend, browser and deployment checks

- `npm run build` passed styles, TypeScript and production bundling. The lazy-loaded 3D chunk was approximately 145 kB compressed in the recorded build. Vite's large-chunk notice and the Browserslist update notice did not fail the build.
- Installed Chrome was checked headlessly at 1440 × 1100: a 129 × 129 terrain crop, terrain picking, picked-location analysis, UTC input, stepping, playback, three-site horizons, power controls and JSON reading export worked.
- All six routes were checked at 390 × 844. The recorded surface run produced no JavaScript page or console errors.
- Separate window-finder browser checks passed editable constraints, fractional stride, preservation of a 12:00 UTC start and explanations for failing alternatives.
- Terrain images at 00:00 and 12:00 UTC changed as computed lighting changed and were visually inspected. Image differences demonstrate a changing scene, not physical validation of its shadows.
- Compose configuration and the Render blueprint schema passed. Downloading the Railway schema returned HTTP 403; provider-schema validation for Railway is not claimed.
- The linked Linux CI run passed dependency installation, NASA ingestion, scientific/API tests, frontend build, production-image build and container readiness/frontend/surface smoke tests for commit `074af8f`.
- Cloud-style local startup on port 8001 passed data setup, liveness, readiness, health and a surface-frame request. Windows project paths containing spaces were exercised and a launcher issue was corrected.

See [VERIFICATION.md](VERIFICATION.md) for the complete recorded scope. Browser interaction checks were run with local Playwright verification scripts during development; the checked-in CI workflow runs the Python/build/container checks and does not claim to rerun that browser interaction suite.

### Reproduce checks

The scientific files must be installed before running the full backend suite:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
Push-Location frontend
npm ci
npm run build
Pop-Location
```

Refresh the external Horizons comparison explicitly when network access is available:

```powershell
.\.venv\Scripts\python.exe backend/scripts/validate_horizons.py
```

That command makes live JPL requests and rewrites the saved comparison fixtures. The ordinary regression suite uses the retained reference data and does not require a live Horizons call for each test run.

## Installation and startup on Windows

### Requirements

- Python 3.11 or newer; local verification used Python 3.14, while the container/CI uses Python 3.12.
- Node.js for frontend development or rebuilding; the container/CI uses Node.js 22. The committed production frontend can be served without a local Node installation.
- Internet access for initial scientific-file and dependency downloads.
- Sufficient disk space for the approximately 48.6 MB source files, 115.5 MB decoded raster, dependencies and any additional terrain.

Python requirements use version ranges rather than a complete locked environment. Frontend dependencies are recorded in `package-lock.json`. The test results above describe the environments in which they were recorded.

### Install and run

From PowerShell, adapting the project path if necessary:

```powershell
Set-Location 'D:\nasa_space app'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/scripts/fetch_nasa_data.py
.\.venv\Scripts\python.exe backend/scripts/prepare_nasa_data.py
.\.venv\Scripts\python.exe run.py
```

Open [LunaScope](http://127.0.0.1:8000), the [surface explorer](http://127.0.0.1:8000/#/horizon), or the [API documentation](http://127.0.0.1:8000/docs). Direct virtual-environment commands avoid requiring PowerShell activation-script changes. Stop the foreground server with `Ctrl+C`.

`run.py` serves the API and built frontend together. `run_lunascope.py` is a compatibility entry point for the same application. Scientific inputs are downloaded separately rather than bundled into Git. If you change prepared public assets, rebuild the frontend so `frontend/dist` contains those assets.

### Frontend development

Keep the backend running, then use a second terminal:

```powershell
Set-Location 'D:\nasa_space app\frontend'
npm ci
npm run dev
```

Vite uses port 5173 and forwards `/api` REST/WebSocket traffic to the backend on port 8000. The production build is generated with `npm run build`; `npm run preview` previews frontend assets but does not start the scientific backend.

## Optional high-resolution terrain

The recorded installation uses the official 80 m PDS terrain. NASA PGDA product 78's 5 m Connecting Ridge surface and height-error downloads repeatedly timed out from the development machine. No 5 m output has been invented or represented as installed.

Retry the official files:

```powershell
.\.venv\Scripts\python.exe backend/scripts/ingest_terrain.py --pgda-site01
```

Or register manually downloaded files with documented metadata:

```powershell
.\.venv\Scripts\python.exe backend/scripts/ingest_terrain.py --file 'C:\Data\Site01_final_adj_5mpp_surf.tif' --uncertainty 'C:\Data\Site01_final_adj_5mpp_toterr.tif' --id pgda-site01 --source-url 'https://pgda.gsfc.nasa.gov/products/78' --version 'Barker et al. 2021 / PGDA 78' --frame MOON_ME_DE421
```

The ingestion path currently accepts the documented compatible south-polar stereographic lunar grid: `MOON_ME_DE421`, 1,737,400 m sphere, longitude origin 0°, metre units, zero polar origin offsets, an unrotated single elevation band, and normalized scale/offset. An optional uncertainty raster must align in CRS, transform and dimensions. It does not silently reproject an incompatible frame or replace a lunar CRS with an Earth CRS. The declared source/version/frame must come from the product documentation.

Registration records metadata and a terrain-file hash. Registered sources appear after restarting the app. Terrain reads use bounded raster windows. For a selected high-resolution source, the horizon uses that source inside its footprint and the documented regional LOLA context outside; internal high-resolution NoData remains unknown. An error raster, if valid at the selected sample, supplies the displayed height uncertainty.

[NASA PGDA product 90](https://pgda.gsfc.nasa.gov/products/90) and [Zenodo record 17084058](https://zenodo.org/records/17084058) were also inspected as potential sources. Their additional uncertainty, effective-resolution, PSR and publication-specific illumination results have not been integrated into the recorded setup.

## API and real-time interfaces

All paths below use the `/api` prefix. Request schemas and field limits are available through `/docs` and `/openapi.json`.

| Method | Path | Use |
|---|---|---|
| GET | `/api/health` | Application and scientific-file status |
| GET | `/api/live` | Process liveness |
| GET | `/api/ready` | Required-file availability; HTTP 503 when files are missing |
| GET | `/api/data/status` | Data mode, missing files and synthetic-fallback status |
| GET | `/api/data/provenance` | Runtime source manifest and provenance |
| GET | `/api/data/validation` | Saved independent Horizons comparison report |
| GET | `/api/sites` | Dataset-derived analysis catalog |
| GET | `/api/terrain/sources` | Installed terrain-source metadata |
| GET | `/api/terrain/crop` | Bounded terrain mesh/elevation crop |
| POST | `/api/surface/frame` | One UTC's Sun/Earth geometry, disk visibility, horizon and provenance |
| POST | `/api/surface/timeline` | Adaptive point visibility series, limited to 31 days per request |
| POST | `/api/scenarios/evaluate` | One-to-three-site operation and optional electrical analysis |
| POST | `/api/matches/evaluate` | Explainable reactive site rankings |
| POST | `/api/windows/search` | Candidate operation windows, constraints and alternatives |
| POST | `/api/contingency/evaluate` | Computed annual contingency summaries |
| POST | `/api/simulation/dispersion` | Deterministic position-sensitivity sampling |
| POST | `/api/simulation/mast-sensitivity` | Mast-height sweep |
| POST / GET | `/api/scenarios`, `/api/scenarios/{id}` | Save/read an in-memory scenario snapshot |
| GET | `/api/export/{id}/json`, `/api/export/{id}/csv` | Export saved scenario data |
| WebSocket | `/api/ws/matches` | Revision-tagged matching requests/results |
| WebSocket | `/api/ws/simulation` | Streamed simulation session and control commands |

Surface latitude is restricted to −90° through −80°, with longitude supplied in degrees east from 0° through 360°. The surface-frame API accepts UTC-offset dates in 2025–2032. Scenario/window requests have their own validated date and duration bounds; operation-window duration is 1–30 days, and scenario intervals are limited to 366 days. These API bounds are not statements about a kernel's entire available coverage.

Example surface reading from PowerShell, with the backend running:

```powershell
$surfaceRequest = @{
    lat_deg = -86.56848542390216
    lon_deg = 45.03113900753911
    time_iso = '2027-01-01T00:00:00Z'
    mast_height_m = 2
    source = 'lola80'
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/surface/frame' -Method Post -ContentType 'application/json' -Body $surfaceRequest
```

Main scene/scenario/window outputs expose their input range, calculation time, methods and source information. Downloaded scenario exports retain inputs and provenance. Data-dependent routes report unavailable inputs rather than manufacturing observations; invalid requests are validated separately.

## Cloud deployment

The application is packaged as one same-origin frontend/API/WebSocket service. The multi-stage [Dockerfile](Dockerfile) builds the frontend with Node 22 and runs Python 3.12 as non-root UID 10001. Scientific files are initialized before the cloud launcher opens the application port.

### Docker Compose

Start Docker Desktop's Linux engine, ensure port 8000 is free, then run:

```powershell
Set-Location 'D:\nasa_space app'
docker compose config --quiet
docker compose up --build -d
docker compose logs -f lunascope
```

Open `http://localhost:8000` once readiness succeeds. The first start downloads/verifies the original inputs and prepares the decoded raster. The named `nasa-data` volume persists at `/app/data/nasa`. `docker compose down` stops the service while retaining that volume. Stop a separately running local server first, or change the host-side port mapping.

### Render and Railway

- [render.yaml](render.yaml) defines a Docker web service, `/api/ready` health check and 1 GB persistent disk at `/app/data/nasa`. Automatic deploys are disabled in the blueprint; review the provider's service/disk settings before creating the service.
- [railway.json](railway.json) selects the Dockerfile and readiness check. Attach a persistent volume at `/app/data/nasa` and ensure it is writable by UID 10001.
- Configure **one application process/replica**. Scenario storage and live sessions are process-local; shared persistence and session routing are required before scaling across replicas.
- The initial local Docker engine was stopped. The production image was subsequently built and smoke-tested successfully in the linked Linux CI run. **A live hosted cloud instance has not been created.**

### Runtime settings

| Variable | Meaning |
|---|---|
| `HOST` | `127.0.0.1` for ordinary local startup; `0.0.0.0` in the container/cloud launcher |
| `PORT` | Defaults to 8000; honors a provider-supplied port |
| `LUNASCOPE_DATA_DIR` | Absolute scientific-data directory; local default is `data/nasa`, container default is `/app/data/nasa` |
| `LUNASCOPE_AUTO_FETCH` | Cloud startup defaults to `true`; set `false` only with already prepared inputs and a manifest |
| `LUNASCOPE_ALLOWED_ORIGINS` | Comma-separated CORS origins; default `*`. Packaged deployment serves UI and API from the same origin |
| `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` | Set to 1 in Docker to limit per-process numerical-library thread allocation |

Optional local use of the cloud launcher, with scientific files already installed:

```powershell
$env:HOST = '0.0.0.0'
$env:PORT = '8000'
$env:LUNASCOPE_AUTO_FETCH = 'false'
.\.venv\Scripts\python.exe backend/scripts/start_cloud.py
```

Cloud initialization rejects source identities that differ from the tracked release manifest and checks the prepared raster and SPICE kernel types/loading. Persistent disk ownership, initial outbound network access and WebSocket support are hosting requirements. The application is packaged and tested for same-origin hosting; some older tool calls use relative API paths, so setting `VITE_API_URL` alone is not a complete split-hosting migration.

See [DEPLOYMENT.md](DEPLOYMENT.md) for provider instructions and resource guidance. A 2 GB memory allocation is a suggested starting point there, not a measured minimum. The project does not provide a shared scenario database or an authentication/account system.

## Architecture and data management

```text
Browser: React + TypeScript + Three.js
  -> REST / WebSockets
FastAPI
  -> metadata/terrain crops and sampled horizons
  -> SPICE Sun/Earth geometry and UTC conversion
  -> visibility, adaptive events, windows and matching
  -> configurable electrical model and exports
Local/persistent scientific-data directory
  -> original JP2/PDS label, SPICE kernels, manifest and decoded raster
```

| Component | Location / technology |
|---|---|
| Application launcher | `run.py`, compatibility `run_lunascope.py` |
| Backend API and schemas | `backend/app/api/`, FastAPI and Pydantic |
| Scientific calculations | `backend/app/core/`, NumPy, SciPy and SpiceyPy |
| Catalog | `backend/app/data/nasa_sites.json` |
| Download/preparation/validation | `backend/scripts/`, Rasterio and Pillow |
| Regression tests | `backend/tests/`, pytest, FastAPI test client and HTTP/WebSocket checks |
| Frontend | `frontend/src/`, React 19, TypeScript, Vite, Tailwind and Three.js |
| Built production UI | `frontend/dist/` |
| Tracked data evidence | `data/nasa_provenance.json`, `data/validation/` |
| Local scientific inputs | `data/nasa/` or `LUNASCOPE_DATA_DIR`; excluded from Git |
| Continuous verification | `.github/workflows/verify.yml` |

The regional decoded raster is memory-mapped; optional GeoTIFFs use geographic window reads. Horizons, terrain crops, ephemeris vectors and visibility series are cached. Meshes load progressively, and the renderer redraws when the scene/camera changes rather than continuously redrawing a static terrain view. Expensive API/stream calculations run outside the server event loop.

Caches and server-side scenario snapshots are in memory. Browser mission settings and schedule edits use local storage. Server restart clears stored scenarios and live sessions; downloaded JSON/CSV exports retain their data. The application does not claim durable multi-user scenario storage or a measured production concurrency capacity.

## Limitations and unsupported claims

| Area | Practical boundary |
|---|---|
| Terrain | 80 m pixel spacing in the recorded setup; gridded/interpolated heights cannot resolve lander-scale rocks, slopes or every short shadow |
| Uncertainty | Installed regional per-cell height error and effective resolution remain Unknown |
| Horizon | Finite radial sampling, 1° bearings and 150 km range can miss narrow or more distant obstructions |
| Timing | Ten-minute baseline can miss shorter unsampled events; refinement applies to detected transitions. Annual/mast/dispersion summaries remain hourly |
| Graphical shadows | Limited to the displayed mesh and shadow-map resolution; approximate soft-shadow/point-Sun rendering and optional inspection fill |
| Earth | Spherical phase/disk approximation; geometric visibility does not establish RF performance, relay access or DSN scheduling |
| Power | User-assumed hardware and load; no validated thermal survival, battery aging or flight-system prediction |
| Site selection | Reproducible project analysis points; not approved landing sites, a certified safety assessment or an exhaustive optimum |
| Permanent shadow | No PSR classification or volatile-resource claim is inferred from a short animation or an unavailable publication dataset |
| Astronomical validation | Twelve retained direction comparisons have limited epoch/site coverage; no universal accuracy guarantee |
| Hosting | One-process, in-memory scenario/session architecture; no live deployment, shared database or account system provided |
| Background media | Owner-supplied decorative MP4 and conceptual educator graphics; not NASA observation imagery |

These boundaries are part of the scientific interpretation of the results, not optional qualifiers to discard when presenting the project.

## Troubleshooting

| Symptom | Check / action |
|---|---|
| Missing-data warning or HTTP 503 | Install dependencies, run the official downloader and preparation script, then check `/api/data/status` and `/api/ready` |
| Hash or source-identity mismatch | Compare the local originals with the tracked manifest. Review the changed/corrupt input explicitly; do not bypass the check or replace it with generated terrain |
| Unreadable/incompatible kernel | Restore the recorded official kernel set. A matching filename alone does not establish a valid SPICE file type |
| 5 m download timeout | Use the installed official 80 m grid, retry NASA later, or ingest documented local GeoTIFFs; no 5 m result is available merely because ingestion is supported |
| No passing site/window | Inspect constraint violations and Unknown coverage. The app does not silently lower requirements to create a recommendation |
| 3D canvas unavailable | Use a browser with WebGL support. Numerical readings and measured horizon information remain separate from graphics availability |
| Dark terrain | Check the calculated Sun position and disk fraction; optional inspection fill makes geometry easier to inspect without changing scientific illumination |
| Frontend changes not visible | Rebuild `frontend/dist` or use the Vite development server; the Python launcher serves the committed build |
| Docker cannot connect to `dockerDesktopLinuxEngine` | Start Docker Desktop's Linux engine; Compose configuration validation alone does not start or test a container |
| Port 8000 already in use | Stop the other local server, select a different `PORT`, or change the host-side Compose port mapping |
| Saved scenario missing after restart | Server storage is in memory; retain downloaded exports |

## NASA Space Apps context and acknowledgements

LunaScope is an **independent project for the NASA International Space Apps Challenge**, as specified by its owner. Dataset use does not imply NASA sponsorship, endorsement, certification or acceptance of a competition submission. The exact challenge year, team identity and submission URL have not been supplied in this repository's project metadata; add verified submission details when available.

Scientific sources and methodological references:

- [NASA LRO/LOLA south-pole PDS archive](https://imbrium.mit.edu/BROWSE/LOLA_GDR/POLAR/SOUTH_POLE/) — installed regional elevation product and label.
- [NASA/JPL NAIF generic kernels](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/) and [NAIF documentation](https://naif.jpl.nasa.gov/naif/) — installed kernels, frames and time conversion.
- [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/) and [Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html) — independent retained observer comparisons.
- [NASA PGDA product 78](https://pgda.gsfc.nasa.gov/products/78) — optional high-resolution terrain/error source; recorded download attempts timed out.
- [NASA PGDA product 90](https://pgda.gsfc.nasa.gov/products/90) and [Zenodo record 17084058](https://zenodo.org/records/17084058) — inspected additional products, not integrated analysis outputs in the recorded setup.
- [NASA International Space Apps Challenge](https://www.spaceappschallenge.org/) — competition context.

Credit the LRO/LOLA team for terrain products and NASA/JPL/NAIF for SPICE and ephemerides. Preserve upstream provenance and consult each source's usage/citation guidance when redistributing data or using optional products. Inclusion here does not grant a blanket license for every upstream scientific file, dependency or owner-supplied video.

For the implementation audit and full upgrade file list, see [UPGRADE_REPORT.md](UPGRADE_REPORT.md). For detailed recorded checks, see [VERIFICATION.md](VERIFICATION.md). For hosting instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).
