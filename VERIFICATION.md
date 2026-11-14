# Verification and claim audit — 14 November 2026

## Delivered application

The corrected source, compiled frontend and video have now been applied directly to D:\nasa_space app at the user's request. Existing dependency folders, virtual environment and unrelated files were preserved. Start with `python run.py` after installing backend/requirements.txt if needed.

## Confirmed checks

- Backend suite: **44 passed** after final simulation synchronization, in 50.53 seconds.
- Additional hardware synchronization regression: **1 passed**, in 50.31 seconds. This gives 45 individually passing backend checks; a combined 45-test run was not repeated.
- TypeScript: `tsc --noEmit` completed with no errors.
- Frontend production build: successful; 2,114 modules transformed, final JavaScript bundle approximately 342 kB before compression.
- Running server: startup completed on 127.0.0.1:8000.
- Real HTTP checks: frontend 200; health endpoint OK; matching evaluated all 10 sites and returned 10 passing sites under permissive constraints; video 200, video/mp4, 1,416,773 bytes.
- Impossible matching requirement: regression confirms 120 consecutive sunlight days in a short mission produces zero passing sites and no recommended primary.
- REST and WebSocket matching produce the same rankings; validation errors do not prevent a subsequent valid socket request.
- Duration check: a 24.5-hour mission reports exactly 24.5 hours; zero-length end samples do not add energy or availability.
- Energy check: with an empty battery and 100 W load for one hour, unmet load is 100 Wh, not a battery-side efficiency-adjusted amount.
- Snapshot check: changing the input object or a returned record does not mutate a saved scenario.
- Legacy module: initial run **22 passed, 1 UI cold-start timeout**. The UI check subsequently **passed in 90.60 seconds** after correcting its provenance disclosure and raising the cold-start timeout from 15 to 120 seconds. Functional assertions were retained. A combined 23-test run was not repeated.
- Actual server WebSocket: handshake, request, echoed revision and match response all passed against `/api/ws/matches`, in addition to the test-client regression checks.

## Repairs

| Finding | Delivered behavior |
|---|---|
| Hard-coded values labeled Published | API, UI, exports and documentation identify illustrative catalog and procedural terrain |
| Extra endpoint treated as a full hour | Actual interval lengths clip the final partial interval; endpoint contributes zero |
| Unmet load overstated by discharge loss | Reports unmet energy at the load |
| Approximate geometry described as exact | Precision claims withdrawn; independent ephemeris accuracy remains unvalidated |
| Polar rays clamped and longitudes approximated | Great-circle ray destinations and spherical horizon geometry |
| Horizon nearest-degree jumps and invalid limb weighting | Periodic interpolation and normalized linear limb-darkening integration; uniform disk is default |
| Repeated slow terrain calculations | Vectorized procedural sampling with bounded in-memory horizon cache |
| Newly selected streaming sites absent | Sessions rebuild site metadata and horizons, preserving existing battery state |
| Clock displayed 2027 but started in 2025 | Default timestamp corrected to 1 January 2027 UTC |
| Seeking charged/discharged battery implicitly | Display-only frames use zero elapsed time; seek resets initial battery state |
| Live settings diverged from planner | Antenna margin and panel/battery/load settings synchronize to the socket session |
| Unsafe/unbounded values accepted | Request validation for dates, finite hardware values, site IDs, search sampling and mast sweeps |
| Even dispersion sample counts yielded one fewer sample | Exact requested count, with geometry recomputed per sampled location |
| Generic annual backups ignored mission window | New matching engine computes the requested window; legacy annual contingency is separately labeled as assumed |
| Immutable record held shared mutable objects | Deep-copy isolation at save and retrieval |
| Missing WebSocket development proxy | Vite proxy supports HTTP and WebSocket traffic |

## Limits

Passing software tests does not authenticate lunar coordinates or establish scientific accuracy. No verified LOLA raster, source-mapped Wueller table, SPICE kernel or live NASA telemetry was integrated. Terrain safety, RF link success, DSN scheduling and landing survival probability are not verified. The app now states those limits. Published references remain references.

Visual desktop/mobile interaction and actual browser video playback could not be checked: the browser-control tool timed out twice. The video asset was confirmed through HTTP. A local-network permission was needed because Windows socket creation initially hung before application requests ran; tests passed after it was granted.

The subsequent frontend redesign implements all six pages from the pasted brief, including an editable mission-phase Gantt. The browser checks for this redesign are recorded below.

One dependency deprecation warning remains from the installed FastAPI/Starlette test client using httpx. It did not fail the tests. The subsequent redesign replaces remote fonts and the Tailwind browser script with system fonts and compiled local styles.

## Direct application verification

Applied directly to D:\nasa_space app on 14 November 2026. The combined backend suite passed: 45 tests in 25.49 seconds. TypeScript checking passed in the original frontend folder. Copied source and build file hashes matched the verified working copy. Replaced original files were backed up before writing.

## Six-page frontend verification

The application was rebuilt directly in D:\nasa_space app. Desktop (1440px) and mobile (390px) browser checks passed for six-page navigation, actual MP4 playback, muted/loop/inline attributes, matching responses, site search, primary selection, backup selection, three-site comparison, column sorting, zoom/reset/layer controls, horizon time scrubbing, phase-duration editing, educator interactions, source cards, route refresh, and mobile overflow. No JavaScript page errors were recorded. Browser screenshots were visually reviewed and small alignment/overlay issues were corrected. TypeScript and the production build passed. The earlier browser-control tool timed out; these checks used installed Chrome through Playwright.

Scientific limitations are unchanged: the app presents demonstration data and approximate models, with no claim of verified lunar terrain, terrain safety or NASA live telemetry.

## Background visibility repair

The two-video crossfade was replaced after a reported visibility regression. The application now uses one native autoplaying, muted, looping MP4, with explicit visible stacking above the document canvas. A cached first-frame canvas bridges the loop boundary without hiding the live video. A media error no longer removes the video elements. The original supplied MP4 is unchanged.

TypeScript and the production build passed. Browser verification checks actual screenshot differences between the rendered video and static fallback, in addition to decoded playback state, repeated loop boundaries, pause/resume, mobile screenshots, and JavaScript errors. Fresh browser profiles include a reduced-motion preference so that a static preference cannot silently disable the requested video background.
