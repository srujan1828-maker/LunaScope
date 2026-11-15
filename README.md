# LunaScope — NASA Space Apps Challenge project

LunaScope compares lunar south-pole surface-operation windows using official NASA terrain and NASA/JPL ephemerides. It includes a six-page frontend, connected mission planner, an interactive Three.js surface generated from the measured elevation grid, terrain shadows, Sun/Earth sky geometry, editable timeline, educator diagrams, provenance and reactive matching. Cloud deployment configuration is included.

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
- Solar/Earth angular radii vary with distance. A 48-strip angular quadrature integrates the disk against the changing skyline rather than assuming one flat obstruction across the whole disk. This remains a spherical, angular-plane approximation.
- Scenario analysis and window searches use a ten-minute baseline with adaptive bisection to 30-second brackets around detected state changes and solar-limb grazing. Intervals integrate the entire requested duration, including partial boundaries. Interruptions shorter than the baseline can still be missed.
- The matcher applies consecutive-sunlight, visibility, shadow-gap and optional battery-reserve constraints, ranks actual calculations, and returns no passing primary if all locations fail.
- Legacy annual contingency is calculated for the requested calendar year from the official inputs; the fabricated multi-year table was removed. Annual, mast-sweep and spatial-dispersion summaries retain hourly sampling and disclose that approximation.
- Dispersion uses deterministic points on concentric ellipses, with terrain and geometry recalculated at each location. It is a spatial sensitivity calculation, not a landing-survival probability.
- Scenario JSON/CSV exports preserve inputs, computed results and provenance. Server scenario storage is in memory; downloaded exports remain available after restart.

## Interface

Home, Mission Planner, Horizon Simulator, Timeline, Educator Mode, and Data & Sources share mission settings and selected locations. The planner supports search, sorting, primary/backup choice and three-site comparison. Mission phases, dates and durations are editable and persist locally in the browser.

In **Horizon Simulator**, select a location and UTC time. The surface mesh preserves elevation differences at 1:1 scale in observer east/north/up coordinates, including lunar curvature. Drag to rotate, wheel to zoom, shift-drag to pan and click a displayed DEM sample to inspect or analyze it. Observer/Sun/Earth views, forward/back steps, playback speed, time reset and mission-time seeking update the scene, readings and horizon together. The Sun/Earth disks retain their computed angular sizes; Earth is a phase-lit sphere without weather imagery. The optional inspection fill light is a viewing aid, separate from solar exposure and power calculations.

Progressive 33×33 then 129×129 crops keep the full 7600×7600 raster out of the browser. Crop spacing is shown separately from the original 80 m pixels. Invalid cells leave holes; missing horizon sectors and geometry states remain Unknown. A hovered horizon shows the responsible terrain location and distance. Multi-site comparisons synchronize the same UTC across horizons and show full-window Sun/Earth/joint timelines, gaps, energy estimates and trade-offs. The power panel exposes fixed/tracking orientation, efficiencies, derating, capacity, load, initial charge and reserve.

### Optional high-resolution GeoTIFFs

```powershell
python backend/scripts/ingest_terrain.py --pgda-site01
```

This attempts NASA PGDA product 78's Connecting Ridge 5 m surface and height-error files. The NASA server timed out during this upgrade; no 5 m dataset has been installed or substituted. Retry when available, or ingest manually downloaded files:

```powershell
python backend/scripts/ingest_terrain.py --file 'C:\Data\Site01_final_adj_5mpp_surf.tif' --uncertainty 'C:\Data\Site01_final_adj_5mpp_toterr.tif' --id pgda-site01 --source-url 'https://pgda.gsfc.nasa.gov/products/78' --version 'Barker et al. 2021 / PGDA 78' --frame MOON_ME_DE421
```

The tool inspects CRS, radius, pixel size, dimensions, scale, units, NoData and uncertainty-raster alignment, records source/hash metadata and rejects incompatible frames. Registered sources appear after restarting the app. Their footprint is read in bounded raster windows. High-resolution terrain is used inside its footprint for a selected source, with explicitly documented regional LOLA context outside; internal high-resolution NoData stays missing. Fine pixel spacing does not establish equivalent effective resolution.

Your supplied MP4 remains the decorative background. It is not represented as NASA observation footage. A single video decoder and cached first-frame bridge smooth the repeat. Educator diagrams are conceptual explanations, not scientific input datasets.

## Accuracy and remaining unknowns

Official inputs do not make the application flight-qualified. The 80 m terrain grid cannot resolve lander-scale rocks, slopes, or short shadows. Ray and time sampling can miss narrow features and brief events. The visual shadow map covers the displayed crop and approximates a soft shadow from the Sun center; numerical regional visibility separately samples terrain out to 150 km. No permanent-shadow claim is inferred from a short animation. Grid slopes are regional estimates. Earth-center clearance is geometric; RF performance, relay coverage and DSN scheduling are unknown. Power hardware parameters are assumptions, and no thermal-survival model is claimed. Moon-centered light-time/stellar-aberration vectors are translated to the observer; full observer-centered relativistic corrections are not modeled.

LunaScope is an independent project for the NASA International Space Apps Challenge, as specified by the project owner. Using official NASA data does not imply NASA endorsement or certification. Select the exact challenge/year and include your team/submission URL in competition materials.

## Verification

```sh
python -m pytest backend/tests -q
cd frontend
npm run build
```

Tests include NASA file hashes, original PDS pixel comparisons, direct SPICE-vector checks, missing-data failure behavior, physics accounting, API/exports, matching and WebSocket commands. See [VERIFICATION.md](VERIFICATION.md) for measured results.

Independent JPL Horizons observer responses and a twelve-case comparison report are saved under [data/validation](data/validation). To refresh these network comparisons explicitly:

```powershell
python backend/scripts/validate_horizons.py
```

The recorded checks cover two measured locations and three UTC epochs on 2027-01-01, comparing Sun/Earth azimuth and elevation against Horizons DE441/MEAN_ME. They validate agreement for those cases only; they do not establish a global accuracy guarantee for terrain or power.

## Cloud deployment

The Dockerfile builds the frontend and runs one same-origin API/WebSocket service. Compose, Render and Railway configuration, persistent NASA-data storage, automatic verified scientific-data setup, readiness/liveness checks and CI image smoke testing are included. See [DEPLOYMENT.md](DEPLOYMENT.md) for commands, environment settings and validation limits. Docker Desktop's local engine was stopped, but [Linux CI](https://github.com/srujan1828-maker/LunaScope/actions/runs/43688943898) successfully built the production image and passed its readiness/frontend/surface smoke tests. A live hosted deployment has not been created.

See [UPGRADE_REPORT.md](UPGRADE_REPORT.md) for the audit, implementation details, actual data, approximation boundaries, access limitations, exact Windows setup and complete changed-file list.

## Sources and acknowledgements

- [NASA LOLA PDS archive](https://imbrium.mit.edu/BROWSE/LOLA_GDR/POLAR/SOUTH_POLE/)
- [NASA/JPL NAIF generic kernels](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/)
- [NASA's October 2024 Artemis candidate-region announcement](https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/)
- [NASA International Space Apps Challenge](https://www.spaceappschallenge.org/)

Please credit the NASA LRO/LOLA team for terrain products and NASA/JPL/NAIF for SPICE and ephemerides. Upstream data retain their source provenance and applicable usage guidance.
