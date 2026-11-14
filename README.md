# LunaScope 2.1 — interactive lunar planning demonstration

This application computes mission-window comparisons, procedural horizons, approximate Sun/Earth geometry, solar exposure, battery energy balance, and reactive primary/backup recommendations. Live means computed results delivered interactively; there is no live NASA telemetry feed.

## Start

Install Python dependencies with `python -m pip install -r backend/requirements.txt`, then run `python run.py`. Open http://127.0.0.1:8000. A built frontend is included. For frontend development: `cd frontend`, `npm ci`, `npm run dev`. The Vite proxy supports both HTTP and WebSocket traffic. Rebuild with `npm run build`.

## Live matching

The workspace evaluates all 10 demonstration sites automatically after mission dates, duration, mast height, antenna margin, hardware, or matching requirements change. Filters cover minimum solar coverage, minimum Earth visibility (optional communications), maximum shadow duration, minimum consecutive sunlight, and optional battery reserve. Results include scored rankings, explanations, primary recommendation and passing backups. An impossible requirement yields no passing primary. Search and sorting are available in the matching table. Set primary updates the map, comparison tray, charts and selected simulation sites.

`POST /api/matches/evaluate` and `/api/ws/matches` use the same engine. WebSocket messages contain `{ "revision": 1, "parameters": { ... } }`. Responses echo revision so the frontend can discard obsolete results. Requests are debounced; HTTP is used if the socket cannot connect. Each result is a mission-window snapshot, not a prediction based on external live observations.

## Data and scientific limits

| Quantity | Actual input / status |
|---|---|
| Catalog and annual metrics | Hard-coded demonstration assumptions. Coordinates and values have no verified row-level source mapping. Ten examples are not the official current NASA candidate list. |
| Terrain / map | Procedural model using assumed landmarks and harmonics. No LOLA DEM is loaded by the primary backend. |
| Sun / Earth | Approximate analytical formulas, not an independently validated implementation of Meeus, SPICE, Horizons, or DE440. |
| Horizon | Vectorized spherical ray geometry, 360 compass samples, near samples from 20m and radial samples out to 120km. Geometry does not establish surface accuracy. |
| Sun exposure | Uniform circular disk against a locally flat skyline, periodic horizon interpolation. Optional linear limb-darkening flux integration. Complex terrain silhouettes across the disk are not integrated. |
| DTE / DSN | Earth-center geometric visibility with an angular margin. No RF link budget, booked DSN contact, or network availability is verified. |
| Battery | User-configured constant load, panel efficiency and charge/discharge losses. No thermal model, degradation, or hardware certification. |
| Dispersion | Deterministic concentric sample points over the procedural terrain; not Monte Carlo or validated landing-survival probability. |
| Terrain safety | Unknown. No slopes, rock hazards or lander stability data are verified. |
| Scenario storage | In-memory snapshots with copy isolation. Restart clears saved scenarios; downloaded JSON/CSV remain usable. |

Endpoint geometry is retained for plots, but metrics and power integrate only the actual mission intervals; the end sample contributes zero hours. A partial final hour is clipped. Transitions are sampled hourly and can differ by up to one sample; high precision timing is not claimed. Match scores are explicit weighted coverage scores, not landing probabilities. Legacy annual contingency uses the demonstration annual table; live matching uses the configured date window.

The separately retained `lunascope/` Streamlit prototype has different synthetic data and algorithms. Its README explains that status. `run.py` is the primary supported entry point for this React/FastAPI application.

## Verification

Run `python -m pytest backend/tests -q` from the project root. Run `npx tsc --noEmit` and `npm run build` in `frontend/`. Tests check software behavior and physical accounting; passing tests do not validate the actual lunar surface, ephemeris accuracy, or NASA affiliation. Measured results from this repair are recorded in VERIFICATION.md.

## Research references (not integrated data)

- Wueller et al., DOI: https://doi.org/10.1029/2025JE009434 and https://zenodo.org/records/17084058
- NASA candidate-region update: https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/
- NASA illumination context: https://science.nasa.gov/photojournal/south-pole-illumination-map/
- NASA SPICE: https://naif.jpl.nasa.gov/naif/

The cited paper is real, but these demonstration values are not its results. NASA Space Apps participation, NASA endorsement, flight qualification, and research validation are not established by this repository.

## Frontend redesign — 14 November 2026

The default frontend now follows the supplied six-page brief:

- Home: cinematic video hero, mission-planning and site-exploration links, capabilities, three-step guide and final CTA.
- Mission Planner: shared mission settings, live backend matching, interactive polar map, search and column sorting, primary and backup selection, three-site comparison, explanations and scenario export.
- Horizon Simulator: date, duration and mast controls, Sun/Earth markers, scrubber and playback, illumination/contact chart, battery sandbox, dispersion and mast sensitivity tools.
- Timeline: eight editable mission phases, dates, durations, statuses, Gantt view, alignment to the selected mission, and JSON export.
- Educator Mode: interactive ridge-clearance and communication diagrams with explanations.
- Data & Sources: six authoritative references and explicit integration/provenance status.

The supplied MP4 is copied to `frontend/public/assets/lunar-background.mp4`. One MP4 asset is reused across pages with muted inline playback, overlays, playback control, and a static SVG fallback. A cached first-frame canvas softly covers the native loop boundary. Only one video decoder is used, its opacity remains visible, and the original MP4 file is unchanged. The 10 actual demonstration catalog rows are displayed instead of claiming 130 loaded sites. Defaults match the brief (120 sunlight days, 180 mission days); a 14-day demonstration preset is available. An impossible requirement correctly produces no passing recommendation. A verified terrain requirement yields Unknown because no verified slope dataset is connected.

Mission settings, primary/backup/comparison selections and edited timeline phases persist locally in the browser. All site-analysis calculations continue to use the working FastAPI backend. Styles are compiled locally with Tailwind for existing tools; the frontend no longer needs remote font or Tailwind scripts to load. Run `npm run dev` for development or `npm run build` for the single-port production server.
