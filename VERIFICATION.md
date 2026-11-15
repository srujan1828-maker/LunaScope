# NASA-data integration verification — 15 November 2026

The active application has been migrated from synthetic terrain and assumed year tables to downloaded official NASA LRO/LOLA and NASA/JPL SPICE inputs.

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
