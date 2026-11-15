# NASA-data integration verification — 15 November 2026

The active application has been migrated from synthetic terrain and assumed year tables to downloaded official NASA LRO/LOLA and NASA/JPL SPICE inputs.

The subsequent surface-simulator and cloud-packaging upgrade is described in UPGRADE_REPORT.md. Results below distinguish observed local tests from unverified external deployment.

## Inputs installed

- LDEM_80S_80M.JP2 (29,837,992 bytes), its original PDS label, and a decoded 7600×7600 signed 16-bit raster.
- JPL DE421 planetary ephemeris, DE421 binary lunar orientation, matching lunar frame, leap seconds and planetary constants.
- Source URLs, sizes and SHA-256 values in data/nasa_provenance.json.
- Thirteen locations derived from original raster cells and a real hillshade overview.

## Removed or replaced

- The procedural crater/terrain engine, hard-coded multi-year site metrics, synthetic Streamlit package and random safety-probability plugin were removed from the project.
- Duplicate inactive frontend workspaces and their drawn mock maps were removed.
- Official terrain now feeds horizons, dispersion, mast sweeps, power illumination and matching.
- SPICE replaces the approximate analytic Sun/Earth ephemeris; the terrain and geometry share MOON_ME_DE421.
- Annual contingency uses computed calendar-year statistics.
- Unverified DSN contact guesses were replaced with an explicit unknown status.
- Missing official scientific data returns unavailable; it never generates substitute measurements.

## Checks

- Backend: `python -m pytest backend/tests -q` — **50 passed** in 45.46 seconds; one third-party dependency deprecation warning.
- The checks include original JP2 pixel comparisons for all 13 catalog locations, hashes for all seven downloaded files, direct SPICE-vector projection, missing-data HTTP 503 behavior, matching, exports and WebSocket commands.
- Frontend: `npm run build` — passed style compilation, TypeScript checking and the production build.
- Browser: headless installed Chrome at 1440×1000 — all 13 sites evaluated, official LOLA hillshade loaded, site search and primary selection worked, horizon time controls updated, and all seven file provenance rows appeared. No browser JavaScript errors were recorded.
- Mobile: all six routes checked at 390×844 with no horizontal page overflow.
- Background video: observed playing in the production app; the native loop and first-frame transition bridge remain in place.
- Local service: `/api/health` reported official data ready, and the production app was served at `http://127.0.0.1:8000`.

Two issues found during integration were corrected before the passing rerun: annual-statistics NumPy scalar serialization and the signed-longitude API contract.

## Limits

LOLA pixel scale is 80 m. Gridded altimetry and derived regional slopes do not certify lander-scale safety. Visibility is sampled and derived, RF links and DSN scheduling remain unknown, and the application is not flight-qualified. The catalog contains dataset-derived analysis points, not NASA-approved landing sites. The decorative video and concept diagrams are not measurement datasets.

## Surface upgrade: measured checks

- Final combined run after the exact-pole follow-up: `python -m pytest backend/tests -q` — **64 passed**, one third-party Starlette/httpx deprecation warning, **144.01 seconds**. The preceding complete run also passed all 64 tests in 59.29 seconds; timings vary with local load.
- Production frontend build passed styles, strict TypeScript and Vite. The Three.js explorer is lazy-loaded separately. Vite reports the expected large 3D chunk warning; its compressed payload is approximately 145 kB. The Browserslist database update notice is unrelated to build correctness.
- New scientific regressions cover isolated flat/ridge/crater/missing landscapes, pole-meridian/ENU conventions, 0°/360° disk integration, Unknown propagation, original-raster mesh heights and scale, scene-vector/reading agreement, adaptive transition brackets, partial operation durations, GeoTIFF metadata/window/NoData behavior, incompatible kernel types and power efficiency accounting.
- The original suite and new window tests passed together (63 tests). An added kernel-type regression then exposed that SPICE can accept a non-kernel text file without an exception while previously loaded frames remain in its pool. The loader now checks each file's actual architecture/type before loading it; all 13 surface-science tests passed after that fix. The final combined rerun is recorded below.
- The fractional-stride test preserves 4,500-second spacing for a 1.25-hour candidate stride and integrates a 27-hour operation duration to floating-point tolerance. An initial strict equality assertion was corrected to a 1e-9-hour tolerance.
- Installed Chrome, headless, 1440×1100: 129×129 DEM mesh loaded; UTC input, forward stepping, play/pause, three-site horizons, DEM picking and picked-location analysis, power controls and JSON reading export passed. All six routes fit a 390×844 viewport. Zero JavaScript page errors and zero console errors were recorded. Canceled stale requests during navigation are expected.
- Rendered terrain captures at 00:00 and 12:00 UTC differed after the computed light direction changed (mean absolute RGB image change 0.3345 on a 0–255 scale in the tested view). This confirms a changing scene, not physical validation of a shadow map. The images were visually inspected.
- Window-finder browser checks passed editable constraints, a fractional candidate stride, application of the exact 12:00 UTC start and explained failing alternatives, with no page errors.
- Twelve independent saved JPL Horizons comparisons passed. Largest direction difference: 0.00003258584379173257°; chosen tolerance: 0.02°. Scope: Sun/Earth directions, two real terrain locations, 00:00/01:00/02:00 UTC on 2027-01-01. Horizons uses DE441/MEAN_ME versus the app's DE421/MOON_ME_DE421. Raw requests/responses are retained under data/validation.

## Cloud and external-data checks

- `docker compose config --quiet`: passed.
- Render `render.yaml`: passed validation against the provider's published JSON schema.
- Railway schema download: HTTP 403; the checked-in JSON follows the documented configuration fields, but provider validation is not claimed.
- Cloud-style launcher with `PORT=8001`, existing NASA inputs and fetching disabled: official-input setup, `/api/live`, `/api/ready`, `/api/health` and `/api/surface/frame` passed locally. A Windows path-with-spaces launcher issue was fixed and the launcher rerun successfully.
- The local Docker Linux engine was stopped (missing dockerDesktopLinuxEngine pipe), so image verification ran in [GitHub Actions](https://github.com/srujan1828-maker/LunaScope/actions/runs/43688943898). Scientific/API tests, frontend build, production-image build and container readiness/frontend/surface smoke tests all passed on Linux for implementation commit 074af8f. No live hosted cloud service has been created.
- NASA PGDA 5 m surface/uncertainty downloads timed out. The application uses the installed 80 m official PDS grid. Optional GeoTIFF/uncertainty ingestion has automated metadata/NoData tests; no unavailable 5 m result is represented as present.

## Practical scientific limits

The 3D mesh is sampled and triangulated from the real raster without invented detail. Its displayed spacing can be coarser than the source pixel scale. Shadow maps cover the displayed crop and use approximate point-Sun/soft-shadow rendering; an optional inspection fill light is explicitly a viewing aid. Numerical visibility separately uses sampled regional rays. A ten-minute baseline with 30-second refinement around detected transitions can still miss shorter interruptions. Earth phase is a spherical model, not a weather observation. Annual, mast and dispersion summaries retain hourly temporal sampling. No short animation establishes a permanently shadowed region.

## Exact-pole regression follow-up

The horizon destination calculation now uses observer ENU unit vectors rotated along great circles instead of the longitude formula that becomes singular at the exact pole. The pole test checks all four cardinal bearings against the selected reference meridian. All 13 surface-science tests and the complete 64-test suite passed after this change. The restarted local surface API also passed the four-bearing pole check.

## Planner selection and terrain presentation follow-up

The default 2027-01-01 through 2027-01-15 window produces different measurements at all catalog points, although all thirteen fail the combined seven-day consecutive-sunlight and 50% Earth-visibility requirements. A direct matching API check found, for example, Site 01 at 52.6% Sun / 18.6% Earth / 4.76 consecutive Sun days, and Site 11 at 95.5% Sun / 0.0% Earth / 13.37 consecutive Sun days. The all-catalog summary was easy to mistake for a selected-location result.

The planner now presents selected-location metrics and its actual failure explanation above the catalog summary. Opening the explorer carries the selected location into the primary scene. A Chrome regression check verified different selected measurements, correct selection transfer, a 257×257 terrain mesh and zero page errors. The frontend production build passed. Backend calculations were inspected through the API; the complete backend suite was not rerun for this frontend-only change.

The terrain view uses a wider default crop, denser display mesh, lower overview camera, smaller compass markers and neutral inspection lighting. Visual inspection exposed shadow-map acne appearing as repeated bands; rendering bias/culling was adjusted and a second capture inspected. These settings affect graphical shadows, not the scientific terrain vertices, horizon calculation or numerical visibility. The 80 m source still cannot produce photographic surface detail.
