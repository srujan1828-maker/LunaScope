# LunaScope scientific surface upgrade — 15 November 2026

## Inspected and preserved

Reviewed the FastAPI entry point, REST/WebSocket routes and schemas; all core geometry, terrain, visibility, matching, windows, power, dispersion, mast, annual and export modules; NASA preparation scripts, catalog and tests; React entry, shared mission state, six pages, existing tools, video, styles and build configuration. The audit and phase checklist are in SCIENTIFIC_UPGRADE.md. The existing project remains the application; its planner, matching, map, timelines, educational diagrams, exports, spatial/mast tools and looping video are preserved.

## Implemented

| Area | Delivered behavior |
|---|---|
| Terrain access | Original PDS label metadata, memory-mapped regional raster, bounded geographic crops, source and mesh spacing reported separately, invalid-data masks and holes. Optional GeoTIFF ingestion checks lunar CRS, frame, units, NoData and uncertainty alignment; reads only needed windows. |
| Astronomy | DE421 SPICE Sun/Earth vectors, UTC conversion, local observer translation, variable angular radii, spherical Earth phase, kernel-type and coverage errors with actionable messages. |
| Horizons | Spherical great-circle rays, local compass basis, per-azimuth obstruction coordinates/elevation/distance, periodic interpolation, explicit missing sectors and a documented reference meridian at the exact south pole. |
| Visibility | Disk quadrature across the varying sampled skyline, separate Earth-center and Earth-disk clearance, four states plus Unknown, full-duration exposure/gap/outage/joint metrics. |
| 3D explorer | Actual elevation mesh in Three.js, lunar curvature and 1:1 height scale, local shadows driven by calculated Sun direction, apparent Sun/Earth disks, observer/Sun/Earth camera views, orbit/pan/zoom, DEM-sample picking and optional elevation colors/inspection light. |
| Time controls | UTC input, play/pause, speed, forward/back step, reset, mission-time scrubber, synchronized scene/readings/horizon and comparison clocks. Stale location frames are excluded while a new location loads. |
| Window finder | Editable constraints and start stride; ten-minute baseline, adaptive 30-second transition brackets, exact-duration integration, hard constraints before transparent scoring, explicit failing/unknown alternatives. Applying a window retains its UTC hour. |
| Electrical model | Panel area/efficiency, tracking or fixed vertical orientation/azimuth, derating, load, battery capacity/initial charge, charging/discharging efficiency and reserve. Generation/load energy, minimum state of charge, reserve, unmet demand and zero-generation duration are shown. |
| Comparison | Up to three synchronized horizons and Sun/Earth directions, full-period Sun/Earth/joint timelines, exposure/outages, power results, elevation, uncertainty and narrative trade-offs. The primary site owns the 3D view. |
| Transparency | Dataset/frame/version, source links/hashes, kernel identities, calculation time/range, methods, assumptions, coverage and limits. Saved independent Horizons comparisons are shown in Data & Sources. |
| Performance | Progressive 33×33→129×129 meshes, bounded crops, raster-window reads, horizon/crop/ephemeris/result caches, rendering on demand, lazy 3D loading and optional streamed-session initialization. Expensive API/stream work runs away from the server event loop. |
| Cloud packaging | Multi-stage non-root Docker image, persistent scientific-data volume, verified startup preparation, configurable host/port/data directory, liveness/readiness, Compose, Render, Railway and a GitHub Actions build/container smoke-test workflow. |

## Scientific inputs actually present

NASA LRO/LOLA LDEM_80S_80M V2.1 and its PDS label are installed and decoded (7600×7600, signed 16-bit, 0.5 m height scaling, 80 m pixel scale, 1,737.4 km reference sphere). JPL de421.bsp, moon_pa_de421_1900-2050.bpc, moon_080317.tf, naif0012.tls and pck00011.tpc are installed. See data/nasa_provenance.json for their original URLs and SHA-256 hashes. The thirteen catalog points trace to actual raster cells; they are project analysis points, not NASA landing approvals.

NASA PGDA product 78's 5 m Connecting Ridge surface and height-error server repeatedly timed out from this machine. No 5 m measurement or uncertainty value has been invented. A retry/manual-ingestion pipeline is provided and its metadata and NoData behavior are tested with isolated fixtures. Product 90 and Zenodo 17084058 were inspected as additional sources; their regional uncertainty/illumination products have not been integrated. In particular, the Zenodo publication's results are not presented as outputs from this application.

## Calculated and approximate parts

Surface vertices, heights, terrain horizons and obstruction points derive from the installed measured/interpolated LOLA raster. Sun/Earth directions, distances and angular sizes derive from SPICE; disk visibility and operation metrics derive from these inputs. Electrical estimates use user-defined hardware assumptions.

The finite terrain mesh and shadow map are visual approximations, limited to the displayed crop. Inspection fill light is an explicit viewing aid and does not change solar exposure or power results. Numerical horizons use 1° azimuth rays to 150 km and finite radial samples; narrow ridges can be missed. Ten-minute baselines and adaptive refinement do not guarantee detection of shorter unsampled interruptions. Sun/Earth disks use spherical angular-plane integration. Light-time/aberration is Moon-centered followed by observer translation, without full observer-centered relativistic corrections. Annual, mast and spatial-dispersion temporal summaries retain disclosed hourly sampling. The power model does not estimate thermal survival or certify spacecraft performance.

Permanent-shadow classification, lander-scale hazards, a verified radio link, DSN scheduling and relay coverage are not supplied. No lander-safety or mission-certification claim is made. Height uncertainty and effective resolution remain Unknown for the installed regional grid. Multi-site comparison uses one shared 3D viewport and synchronized charts, rather than several simultaneous WebGL scenes.

## Verification and access limits

Actual automated/browser results are recorded in VERIFICATION.md. Independent JPL Horizons returned twelve Sun/Earth direction cases for two terrain locations at three UTC epochs; maximum angular difference was 0.00003258584379173257°, below the explicitly chosen 0.02° comparison tolerance. This is a DE421-vs-DE441 direction comparison for those cases, not validation of terrain shadows, electrical performance or every mission date. Raw API responses and query URLs are retained in data/validation.

Compose configuration passed; the Render blueprint passed the provider's published JSON schema. A cloud-style startup on port 8001 using the installed scientific inputs passed liveness, readiness, health and a surface-frame request. Docker Desktop's local Linux engine was stopped; the production image was subsequently built and smoke-tested successfully by GitHub Actions on Linux. A live cloud deployment has not been created. Fetching the Railway JSON schema returned HTTP 403; its configuration follows the official documented fields. The [Linux verification run](https://github.com/srujan1828-maker/LunaScope/actions/runs/43688943898) passed scientific tests, frontend build, production-image build and container readiness/frontend/surface smoke checks for implementation commit 074af8f. No cloud account, paid service, image registry or domain has been created.

## Exact Windows setup

From PowerShell, using Python 3.11+ (this workspace was checked with Python 3.14):

```powershell
Set-Location 'D:\nasa_space app'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/scripts/fetch_nasa_data.py
.\.venv\Scripts\python.exe backend/scripts/prepare_nasa_data.py
.\.venv\Scripts\python.exe run.py
```

Open http://127.0.0.1:8000/#/horizon. The built frontend is included. For frontend development with Node 20+:

```powershell
Set-Location 'D:\nasa_space app\frontend'
npm ci
npm run build
```

For cloud-style local startup with data already installed:

```powershell
Set-Location 'D:\nasa_space app'
$env:HOST='0.0.0.0'
$env:PORT='8000'
$env:LUNASCOPE_AUTO_FETCH='false'
.\.venv\Scripts\python.exe backend/scripts/start_cloud.py
```

Docker/Render/Railway instructions and volume/replica requirements are in DEPLOYMENT.md. Scenario storage remains in memory; download exports to retain them across restarts.

## Changed files

The complete change list for this upgrade is appended below, including source, tests, deployment configuration, provenance fixtures and regenerated frontend bundles. The downloaded rasters/kernels and local dependencies remain excluded from Git.

- `.dockerignore`
- `.env.example`
- `.github/workflows/verify.yml`
- `DEPLOYMENT.md`
- `Dockerfile`
- `README.md`
- `SCIENTIFIC_UPGRADE.md`
- `UPGRADE_REPORT.md`
- `VERIFICATION.md`
- `backend/app/api/routes.py`
- `backend/app/api/schemas.py`
- `backend/app/api/surface.py`
- `backend/app/api/ws.py`
- `backend/app/core/annual_metrics.py`
- `backend/app/core/ephemeris.py`
- `backend/app/core/events.py`
- `backend/app/core/horizon.py`
- `backend/app/core/landing_dispersion.py`
- `backend/app/core/mast_sensitivity.py`
- `backend/app/core/matching.py`
- `backend/app/core/nasa_data.py`
- `backend/app/core/power_model.py`
- `backend/app/core/simulation_engine.py`
- `backend/app/core/spice_geometry.py`
- `backend/app/core/surface.py`
- `backend/app/core/terrain.py`
- `backend/app/core/visibility.py`
- `backend/app/core/window_finder.py`
- `backend/app/main.py`
- `backend/scripts/fetch_nasa_data.py`
- `backend/scripts/ingest_terrain.py`
- `backend/scripts/start_cloud.py`
- `backend/scripts/validate_horizons.py`
- `backend/tests/test_nasa_sources.py`
- `backend/tests/test_surface_science.py`
- `backend/tests/test_window_finder.py`
- `compose.yaml`
- `data/validation/horizons_report.json`
- `data/validation/lola-sp-001-earth-horizons.json`
- `data/validation/lola-sp-001-sun-horizons.json`
- `data/validation/lola-sp-002-earth-horizons.json`
- `data/validation/lola-sp-002-sun-horizons.json`
- `frontend/dist/assets/SurfaceExplorer-DwOFwDgc.js`
- `frontend/dist/assets/index-3aRq5y4x.js`
- `frontend/dist/assets/index-BYtwm8N-.js`
- `frontend/dist/assets/index-CPJqpvqK.css`
- `frontend/dist/assets/index-bxPMwbVr.css`
- `frontend/dist/index.html`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/RedesignedApp.tsx`
- `frontend/src/components/PowerSimulationDrawer.tsx`
- `frontend/src/components/SurfaceExplorer.tsx`
- `frontend/src/components/TerrainViewport.tsx`
- `frontend/src/components/ValidationPanel.tsx`
- `frontend/src/components/WindowFinderModal.tsx`
- `frontend/src/components/surfaceTypes.ts`
- `frontend/src/main.tsx`
- `frontend/src/mission.ts`
- `frontend/src/pages.tsx`
- `frontend/src/styles/surface.css`
- `frontend/src/styles/utilities.css`
- `frontend/src/types/index.ts`
- `railway.json`
- `render.yaml`
