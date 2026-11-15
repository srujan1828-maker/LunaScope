# LunaScope — NASA Space Apps Challenge project

LunaScope compares lunar south-pole surface-operation windows using official NASA terrain and NASA/JPL ephemerides. It includes a six-page frontend, a connected mission planner, real terrain map, horizon/time simulation, editable mission timeline, educator diagrams, data provenance, and reactive primary/backup matching.

## Official scientific inputs

| Input | Integrated use |
|---|---|
| NASA LRO/LOLA `LDEM_80S_80M` V2.1, PDS dataset `LRO-L-LOLA-4-GDR-V1.0` | Elevations and spherical terrain horizons at 80 m/pixel. Heights are stored with the published 0.5 m scaling relative to the 1,737.4 km sphere. |
| NASA/JPL `de421.bsp` | Sun/Earth/Moon geometry for the requested mission dates. |
| NAIF `moon_pa_de421_1900-2050.bpc` and `moon_080317.tf` | Lunar orientation in `MOON_ME_DE421`, matching the terrain reference frame. |
| NAIF `naif0012.tls`, `pck00011.tpc` | Time conversion and planetary constants. |

Source URLs, retrieval time, sizes and SHA-256 hashes are recorded in [data/nasa_provenance.json](data/nasa_provenance.json), and shown on the Data & Sources page. The map is a hillshade derived from this raster, not a procedural crater drawing. No synthetic fallback dataset is used. Missing scientific inputs return HTTP 503 with setup instructions.

The 13 analysis locations are actual cells selected reproducibly from the official raster: high ground, regional grid slope ≤8°, at least 20 km spacing, within 120 km of the pole. Their row/column, coordinates, elevation and source are recorded in [nasa_sites.json](backend/app/data/nasa_sites.json). This is LunaScope's selection method; these points are **not** represented as NASA-approved landing sites or as the official Artemis candidate-region list.

## Run locally

Use Python 3.11 or later and Node.js 20 or later. From the repository root:

```sh
python -m pip install -r backend/requirements.txt
python backend/scripts/fetch_nasa_data.py
python backend/scripts/prepare_nasa_data.py
python run.py
```

Open **http://127.0.0.1:8000**. The built frontend is included. `run_lunascope.py` is a compatibility entry point for the same app. Official raw inputs total approximately 47 MB; the decoded raster needs approximately 116 MB. These files are downloaded locally and excluded from Git, while their source manifest and derived location catalog are tracked.

Frontend development:

```sh
cd frontend
npm ci
npm run dev
```

The development proxy forwards REST and WebSocket traffic to port 8000. `npm run build` compiles styles, runs TypeScript checking and produces the production bundle.

## How analysis works

- A spherical raycaster samples the official LOLA raster in 360 compass directions out to 150 km. Near samples start at the 80 m grid scale; no invented micro-terrain is added.
- SPICE supplies Sun and Earth vectors with `LT+S` corrections in the same DE421 frame. Local observer geometry includes the actual raster elevation and finite body distance.
- Solar-disk exposure and Earth-center clearance are derived from those inputs. Hourly samples integrate the exact requested duration, including partial final intervals.
- The matcher applies consecutive-sunlight, visibility, shadow-gap and optional battery-reserve constraints, ranks actual calculations, and returns no passing primary if all locations fail.
- Legacy annual contingency is now calculated for the requested calendar year from the official inputs; the fabricated multi-year table was removed.
- Dispersion uses deterministic points on concentric ellipses, with terrain and geometry recalculated at each location. It is a spatial sensitivity calculation, not a landing-survival probability.
- Scenario JSON/CSV exports preserve inputs, computed results and provenance. Server scenario storage is in memory; downloaded exports remain available after restart.

## Interface

Home, Mission Planner, Horizon Simulator, Timeline, Educator Mode, and Data & Sources share mission settings and selected locations. The planner supports search, sorting, primary/backup choice and three-site comparison. Mission phases, dates and durations are editable and persist locally in the browser.

Your supplied MP4 remains the decorative background. It is not represented as NASA observation footage. A single video decoder and cached first-frame bridge smooth the repeat. Educator diagrams are conceptual explanations, not scientific input datasets.

## Accuracy and remaining unknowns

Official inputs do not make the application flight-qualified. The 80 m terrain grid cannot resolve lander-scale rocks, slopes, or short shadows. Ray and time sampling can miss narrow features and brief events. Grid slopes are derived regional slopes, not certified landing-safety thresholds. Direct-to-Earth clearance is geometric; RF performance, relay coverage and DSN scheduling are unknown. Power hardware parameters are user assumptions, and no thermal-survival model is claimed.

LunaScope is an independent project for the NASA International Space Apps Challenge, as specified by the project owner. Using official NASA data does not imply NASA endorsement or certification. Select the exact challenge/year and include your team/submission URL in competition materials.

## Verification

```sh
python -m pytest backend/tests -q
cd frontend
npm run build
```

Tests include NASA file hashes, original PDS pixel comparisons, direct SPICE-vector checks, missing-data failure behavior, physics accounting, API/exports, matching and WebSocket commands. See [VERIFICATION.md](VERIFICATION.md) for measured results.

## Sources and acknowledgements

- [NASA LOLA PDS archive](https://imbrium.mit.edu/BROWSE/LOLA_GDR/POLAR/SOUTH_POLE/)
- [NASA/JPL NAIF generic kernels](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/)
- [NASA's October 2024 Artemis candidate-region announcement](https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/)
- [NASA International Space Apps Challenge](https://www.spaceappschallenge.org/)

Please credit the NASA LRO/LOLA team for terrain products and NASA/JPL/NAIF for SPICE and ephemerides. Upstream data retain their source provenance and applicable usage guidance.
