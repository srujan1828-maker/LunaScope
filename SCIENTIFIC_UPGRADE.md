# Surface-simulation audit and implementation checklist

Audit: 15 November 2026. Baseline: commit 6738f7d.

Inspected the FastAPI entry point, REST and WebSocket routes, request schemas, all scientific core modules, NASA ingestion scripts and catalog, backend tests, React entry point and shared mission state, six pages, map, video, export, window, power, dispersion, mast and streamed-simulation components, styles and build configuration.

Architecture: React 19 / TypeScript / Vite, FastAPI / NumPy / SciPy / Rasterio / SpiceyPy. `run.py` serves the API and bundled frontend on Windows. Existing planner, reactive matching, comparison, horizons, exports, timeline, spatial and mast sensitivity, power and background video remain useful and will be preserved.

Already real: downloaded PDS LOLA LDEM_80S_80M V2.1, DE421 SPK and matching lunar PCK/FK, UTC conversion with NAIF leap seconds. No production synthetic terrain remains. Existing analytic assumptions: fixed solar radius in visibility, hourly windows, a one-dimensional flat skyline segment across the Sun, regional terrain slopes, simplified panel and battery hardware, sampled spherical rays. DSN and lander-scale safety are unknown.

Implementation checklist (results recorded in VERIFICATION.md):

- [x] Metadata-driven terrain access, masked NoData, geographic crops, optional high-resolution GeoTIFF/uncertainty ingestion.
- [x] Independent saved JPL Horizons comparison, frame/time/kernel errors reported clearly.
- [x] Horizon obstruction coordinates, compass basis, pole meridian and missing-sector coverage.
- [x] Variable angular disks integrated against the changing skyline; explicit Unknown state.
- [x] Actual DEM mesh in Three.js with local ENU coordinates, 1:1 vertical scale, terrain shadows and terrain picking.
- [x] Synchronized UTC controls, Sun/Earth sky disks, readings, horizon and timelines.
- [x] Sub-hour sampling and adaptive transition refinement for complete-duration searches; transparent failure alternatives.
- [x] Exposed power orientation/efficiency/derating/reserve controls and energy-accounting readings.
- [x] Synchronized multi-site scientific comparison, source/coverage/uncertainty disclosure.
- [x] Regression/physics/browser validation, performance checks, Windows instructions and changed-file report.

Rendering will remain a visualization approximation: shadow-map resolution and the finite displayed crop cannot reproduce all distant or sub-grid occlusions. Numerical visibility uses the regional horizon separately. No permanent-shadow classification is inferred from a short animation. Official inputs do not certify predictions.

## External limits

The 5 m PGDA server was unreachable (connection timeouts). The metadata/NoData/uncertainty ingestion pipeline is implemented and tested with isolated fixtures; the actual scene uses the installed official 80 m PDS terrain. JPL Horizons was reachable and its twelve comparisons passed. Docker configuration and cloud startup were checked, but the Docker Linux engine was not running, so no local image build or live cloud deployment is claimed.
