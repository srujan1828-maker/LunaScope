# LunaScope 2.0
## Compare lunar landing sites. Find better surface-operation windows. Understand why.

**Revised product and implementation plan · 14 November 2026**

Prepared from the supplied LunaScope master blueprint and the challenge statement. This is a proposed build specification, not a completed simulation or flight-qualified planning tool. Priorities, schedules, performance budgets, and test tolerances below are proposed targets.

## 1. Product direction

Build an intuitive lunar south-pole comparison workspace that answers four questions:

1. Where will the Sun and Earth appear relative to the terrain horizon?
2. How do those conditions change across sites and dates?
3. When are sunlight and geometric Earth visibility available together?
4. Which site and start date better satisfy the user's selected constraints, and why?

**Primary interaction:** choose two or three sites → choose a date range and surface mission duration → compare synchronized horizons and timelines → inspect better windows → save a reproducible scenario.

Keep the original plan's terrain modelling, provenance, and backup-site concept. Move annual published statistics into a supporting research layer. Make date-specific comparison the main experience. “Best window” means a surface-operation window; it does not establish launch, transfer, descent, or landing feasibility.

### Challenge alignment

| Challenge need | Main feature | Evidence of success |
|---|---|---|
| Compare sites quickly | Two-to-three-site comparison tray with shared dates | User can explain a trade-off without switching pages |
| Compare dates quickly | Start-date heatmap and duration control | User finds an alternative window in a few interactions |
| See Sun and Earth relative to horizon | Synchronized 360° horizon plots with time cursor | Terrain obstruction is visible at the selected instant |
| Assess power potential | Solar visibility timeline; optional configured power estimate | Sun exposure and electrical power are separately labelled |
| Assess direct-to-Earth opportunities | Earth-center visibility windows, later station-specific geometry | User sees longest outage and understands model scope |
| Serve different audiences | Explore and Plan modes over one calculation engine | Beginner view stays simple; assumptions remain available |

## 2. What needs changing in the original blueprint

| Original approach | Problem | Revised decision |
|---|---|---|
| Year and required sunlit days first | Annual or seasonal maxima do not establish conditions on a selected date | Start with actual UTC dates and duration |
| Fixed 130-site CSV architecture | Archive contains geospatial assets; assumed column names and site counts need ingestion checks | Build an adapter and audit actual fields before exposing them |
| Primary and backup only | Frames exploration as failure recovery | Compare up to three peers; assign primary and backup after evaluation |
| Four large panels always visible | Too much information for first-time visitors | Progressive workspace with comparison first, details on demand |
| Sun constrained to ±1.54° across 80–90°S | Exact-pole behaviour is overgeneralized to a broad latitude band | Compute geometry at each site's actual coordinates [S1] |
| 1° horizon bins with rounded azimuth | Can miss narrow terrain features during solar grazing | Converge angular resolution and interpolate circularly |
| Grid directions treated as compass directions | Polar map grid north differs from local geographic north | Compute local directions in the Moon-fixed frame |
| Out-of-bounds DEM indices clipped to raster edge | Creates artificial terrain by repeating boundary pixels | Use adequate coverage or mark the result incomplete |
| Sun fraction > 0 called nominal science | Tiny exposure may not sustain the load | Label geometry states separately from engineering sufficiency |
| Earth-center visibility called an open link | A specific ground station may not be visible or available | Label geometric Earth visibility; add station modelling later |
| Terrain shadow called eclipse | Confuses terrain occlusion with celestial occultation | Use “terrain shadow”; model Earth blocking the Sun separately |
| Streamlit as the finished interface | Convenient prototype, less control over a tightly synchronized product | React/TypeScript interface; retain Python science modules |

**Source check:** the Zenodo record exists and describes landing-site shapefiles and illumination rasters for midsummer periods in 2025–2032. Its landing page does not establish the ready-made CSV schema used in the original reference code. Audit the downloaded attributes before promising any particular metric or site count. [S2]

## 3. The modern user experience

### Explore mode — default

Open directly into a verified example with two sites and a supported date interval. Show a short instruction: “Move time to see when the terrain hides the Sun or Earth.” Avoid a login requirement for exploration.

- **Top controls:** site search, UTC start date, duration, Compare, and Find windows.
- **Map:** south-polar terrain context with selectable sites and a persistent comparison tray.
- **Comparison cards:** sunlight availability, longest terrain-shadow interval, Earth-center visibility fraction, longest Earth-center outage, and joint visibility time.
- **Horizon view:** one plot per site, aligned to the same azimuth/elevation axes; Sun and Earth markers move together in time.
- **Timeline:** sunlight fraction, Earth visibility, and overlap in separate rows per site.
- **Insight panel:** concise, computed explanations with links to the relevant event.

Plain-language tooltip examples: “Terrain blocks the Sun here,” “Earth's center clears this ridge,” and “This figure measures sunlight exposure, not electrical output.”

### Plan mode — progressively disclosed controls

Add constraint thresholds, panel and antenna heights, hardware assumptions, uncertainty views, data exports, and the provenance drawer. Switching modes must never silently change calculations or default assumptions.

### Visual direction

Use an ink/navy canvas, neutral terrain, amber Sun, cyan Earth, and lavender uncertainty. Pair colour with icons, text, and line patterns. Use generous spacing, clear typography, persistent UTC labels, and restrained animation.

The skyline is the main analytical visual. An optional 3D terrain inset provides orientation; every essential action also works through a 2D map, accessible charts, and tables. Avoid a decorative globe that delays the actual comparison.

Responsive behaviour: three columns on wide screens, stacked site cards on smaller screens, sticky time controls, and a table alternative. Support keyboard scrubbing, screen-reader event summaries, reduced motion, and non-colour status distinctions.

## 4. Feature roadmap by value

| Priority | Feature | User benefit | Scope and dependency |
|---|---|---|---|
| P0 | Synchronized site/date comparison | Directly solves the challenge | Two or three curated sites; one shared time range |
| P0 | Interactive 360° horizon | Explains why visibility changes | Real terrain horizon; selectable event markers |
| P0 | Sun, Earth, and overlap timelines | Makes interruption lengths obvious | Exact metric definitions and unknown states |
| P0 | Start-date window finder | Answers “When should operations begin?” | Search only supported dates and mission duration |
| P0 | Explain this result | Connects recommendations to evidence | Deterministic templates, not generated scientific claims |
| P0 | Provenance and scenario export | Makes comparisons reproducible | Source versions, assumptions, JSON and CSV |
| P1 | Panel/antenna height comparison | Shows practical terrain-clearance trade-offs | Separate heights and separate horizon caches |
| P1 | Power and battery sandbox | Converts exposure into an assumed energy story | Array orientation, load, efficiencies, reserve |
| P1 | Date-shift and landing-position sensitivity | Exposes fragile recommendations | Terrain coverage and explicit perturbation ranges |
| P1 | Guided learning stories | Helps educators and the public | Short narrative steps using actual computed scenarios |
| P1 | Read-only scenario links | Makes science/engineering review easier | Versioned snapshots; no account needed to view |
| P2 | Named Earth station windows | Improves DTE analysis | Station positions, Earth rotation, station elevation mask |
| P2 | 3D terrain inspection | Adds spatial understanding | Must match analytical data and coordinate frame |
| P2 | AI scenario assistant | Translates user intent into controls | Preview parsed inputs; physics remains deterministic |
| P2 | Shared review notes | Supports team coordination | Authentication, access controls, versioned comments |

Do not include rover route optimisation, relay constellation simulation, descent guidance, thermal survival, or landing-safety certification in the first release. These require additional models and distract from the stated challenge.

## 5. The signature feature: Find better windows

Inputs: selected sites, allowed start-date interval, required surface-operation duration, minimum sunlight threshold, maximum shadow gap, minimum Earth-center visibility, maximum Earth-center outage, and optional joint-visibility requirement.

Algorithm:

1. Obtain a continuous computed interval covering every candidate start plus the requested mission duration.
2. Find and refine Sun/terrain and Earth/terrain transitions.
3. Slide the full mission interval over candidate start times.
4. Calculate total availability, longest gaps, longest continuous overlaps, and completeness for each site/window pair.
5. Apply hard requirements first. Incomplete data produce **Unknown**, never Pass.
6. Rank passing windows using transparent user priorities; show non-dominated trade-offs rather than one unexplained score.
7. If none pass, show the closest alternatives and the exact violated constraints. Never silently relax requirements.

Offer presets such as “Favour sunlight,” “Favour Earth visibility,” and “Minimise interruptions.” Explain their ordering. Let users inspect raw metrics before accepting a recommendation.

A useful result states: “This alternative reduces the longest shadow gap, but increases the longest Earth-center outage.” Fill all numerical values from calculated results; demonstration copy must not invent mission predictions.

## 6. Scientific computation specification

### Coordinates and data contract

Use east-positive lunar longitude, clearly specified latitude convention, UTC at the interface, and the selected ephemeris time scale internally. Keep terrain datum, observer height, and coordinate-frame identifiers explicit.

The NASA PGDA product page identifies its south-polar GeoTIFFs as metre-based stereographic products in the DE421 Moon Mean Earth frame and lists elevation, error, and effective-resolution products. Read the selected product metadata rather than hard-coding a filename or projection. [S3]

Use a documented compatible SPICE kernel set: planetary ephemeris SPK, lunar orientation binary PCK, lunar frame FK, and leap-second kernel. An ephemeris file alone does not define the required lunar surface orientation. Pin versions and coverage. DE440 lunar frame aliases need explicit handling when comparing to DE421 terrain. [S4]

JPL Horizons supports surface observers and provides an independent geometry reference. Match coordinates, height, frame, times, and apparent/geometric conventions before comparing results. Do not apply Earth's atmospheric refraction to the lunar observer. [S5]

### Terrain horizon

Transform observer and terrain samples to consistent Moon-fixed Cartesian coordinates. Project observer-to-terrain vectors into the local east/north/up basis. For each azimuth, retain the maximum elevation angle and the terrain point responsible for it.

This avoids confusing polar grid bearings with true local azimuth and avoids relying solely on a planar curvature approximation. At the exact pole, declare a reference meridian because local north is otherwise ambiguous.

Use multiple terrain resolutions: fine samples nearby and coarser coverage farther away. Determine ray length and angular spacing by convergence checks. Do not assume that an 80 km cutoff is universally sufficient; NASA illustrates shadows cast by terrain about 120 km away. [S1]

Preserve NoData and boundary gaps. Unknown obstructing terrain must not become an open sky. Store azimuth, horizon angle, blocker distance/position, observer height, DEM identifiers, and coverage flags. Use periodic interpolation at the 0°/360° seam.

### Sun visibility

Compute the Sun's topocentric direction and apparent angular radius. Estimate the fraction of the disk above the horizon.

The original circular-segment formula can be retained as a fast approximation only where the skyline is locally flat across the disk. Use disk sampling against the changing horizon for jagged terrain, with convergence checks. Distinguish a terrain-visibility estimate from actual sunlight when Earth occultation is relevant; either implement celestial occultation or visibly flag affected/unsupported intervals.

Define two separate quantities:

- **Sun-available time:** duration for which visible fraction meets a configured threshold.
- **Equivalent full-Sun exposure:** integral of visible fraction over time, in hours.

Neither quantity is automatically electrical energy.

### Earth visibility and communication

P0 metric: Earth's **center** clears the local antenna horizon plus a user-declared angular margin. Draw the Earth disk for context, but do not imply the center criterion represents every point on Earth.

Name the output “Earth-center geometric visibility (DTE proxy).” A constant clearance margin is a planning assumption, not a complete Fresnel-zone or radio-link calculation.

P2 station mode computes the actual lunar-observer-to-ground-station direction, lunar terrain obstruction, Earth-side Moon elevation mask, and station geometry. Antenna pointing limits, RF link budget, weather, and network scheduling remain separate inputs or unsupported constraints. Station geometry still does not guarantee a usable booked link.

### Four geometry states

| Sun above selected visibility threshold | Earth center clear | Label |
|---|---|---|
| Yes | Yes | Sun + Earth visible |
| Yes | No | Sun visible; Earth blocked |
| No | Yes | Sun below threshold; Earth visible |
| No | No | Sun below threshold; Earth blocked |

Missing inputs create an additional **Unknown** state. Avoid “Nominal science,” “Safe,” or “Mission-ending” unless an appropriate operational model supports those conclusions.

### Optional power model

Use a separately declared panel normal and separate panel height:

`Psolar = irradiance(distance) × area × efficiency × visible_fraction × max(0, panel_normal · sun_direction) × derating`

Let users choose a fixed tilted panel or an ideal tracking model; label tracking assumptions. Calculate battery energy using charge/discharge efficiencies, capacity, initial energy, load profile, and reserve. Once energy reaches zero, record unmet demand; clamping to zero alone hides failure. Show “load unmet under these assumptions,” not a spacecraft-survival prediction.

### Timing and uncertainty

Use coarse evaluation for browsing, finer evaluation near transitions, and an adaptive event search for summary windows. Hourly samples alone are insufficient for reliable short outages. Report the event-refinement tolerance separately from the physical uncertainty caused by terrain resolution and model inputs.

Sensitivity envelopes vary landing position, DEM elevation where justified, start time, and hardware height. Without defensible probability distributions, show bounded ranges and scenarios rather than fabricated confidence percentages.

## 7. Metrics every comparison must define

| Metric | Definition |
|---|---|
| Sun availability (%) | Duration above configured disk-fraction threshold / interval duration |
| Equivalent full-Sun hours | Integral of disk-visible fraction over interval |
| Longest Sun-below-threshold gap | Longest continuous interval below the threshold |
| Earth-center availability (%) | Duration center clears antenna horizon and margin / interval duration |
| Longest Earth-center outage | Longest continuous blocked interval |
| Joint availability | Duration both geometry criteria hold |
| Longest joint window | Longest continuous overlap, not sum of disjoint periods |
| Minimum battery reserve | Minimum configured-model energy relative to reserve |
| Coverage | Whether the complete requested interval and terrain are supported |

For incomplete intervals, return primary comparison metrics as unavailable or explicitly partial; never silently shrink the denominator. Do not compare partial and complete results as if they were equivalent.

## 8. Architecture and implementation boundaries

Use one web frontend and one Python backend initially. Keep scientific functions independent of the web framework.

| Component | Responsibility | Proposed implementation |
|---|---|---|
| Client | Site selection, shared time cursor, comparison, accessible views | React + TypeScript; SVG/canvas charts |
| Polar map | Lunar terrain tiles and site selection | Custom polar projection; avoid Earth/Web-Mercator defaults |
| API | Request validation, scenarios, result delivery | FastAPI with explicit schemas |
| Science engine | Frames, horizons, ephemerides, visibility, interval metrics | Python, NumPy, rasterio, SPICE bindings |
| Precompute worker | Validated horizon and ephemeris bundles | Simple background process; queued jobs only when needed |
| Data storage | Versioned terrain, kernels, result bundles | File/object storage; lightweight scenario database |
| Optional 3D | Terrain context | Three.js after analytical views are validated |

Pin dependency versions during implementation after verifying compatibility. Streamlit may remain an internal science-debugging harness if that accelerates validation.

### Proposed API

- `GET /sites`: curated catalog, coverage, and source metadata.
- `POST /scenarios/evaluate`: selected sites, UTC range, heights, thresholds, and optional hardware model.
- `POST /windows/search`: start interval, duration, constraints, and priorities.
- `GET /jobs/{id}`: status for expensive uncached jobs.
- `POST /scenarios`: save an immutable scenario revision.
- `GET /scenarios/{id}`: retrieve inputs, results, and provenance together.

Return typed statuses such as complete, partial, unsupported, and failed. Validate coordinate ranges, end-after-start, coverage, site-count limits, and computational cost. Cancel obsolete requests when users change settings; never render an old result under new controls.

### Scenario record

Store schema version, scenario ID, site coordinates and coordinate frame, UTC bounds, mission duration, panel height, antenna height, visibility thresholds, clearance assumptions, power configuration, DEM checksums, kernel versions, engine version, sampling policy, results, events, and coverage warnings.

Cache keys must include all calculation-affecting inputs. Reusing one cached horizon for different observer heights is invalid. Separate instantaneous marker data from interval aggregates so time scrubbing does not recompute the entire analysis.

### Proposed performance budgets

For precomputed demo scenarios: interactive controls within 3 seconds of opening, site changes within 500 ms, and smooth cached time scrubbing. These are engineering budgets, not measured performance. Display progress and cancellation for uncached jobs; never substitute synthetic numbers while waiting.

## 9. Provenance users can understand

Each metric has two independent labels:

1. **Origin:** published value, computed geometry, or model with user assumptions.
2. **Quality:** validated, approximate, incomplete, or unsupported.

For example, a computed power curve has source-backed geometry plus assumed hardware inputs. One “Assumed” badge should not obscure which parts come from measurements or calculations.

The drawer exposes source URL, product version, coordinate convention, units, computation version, selected thresholds, sampling/refinement policy, and limitations. Export JSON for reproduction and CSV for analysis. A printable report is P1. Shared links should pin scenario revisions and provenance rather than silently recomputing with newer sources.

## 10. Delivery plan

Assumption: a small team with frontend and scientific Python capability. Durations are planning estimates; the data/frame audit is a gate, not an optional cleanup task.

| Stage | Suggested effort | Deliverable | Exit gate |
|---|---|---|---|
| 0. Scope and source audit | 1–2 days | Data manifest; supported sites and dates | Actual files, units, frames, licensing, and coverage identified |
| 1. Thin science slice | 3–5 days | One site's horizon and Sun/Earth geometry | Independent reference comparison and synthetic tests pass |
| 2. Comparison workspace | 3–4 days | Two-to-three synchronized site views | Same time cursor, correct labels, keyboard access |
| 3. Window finder | 2–3 days | Date search and explainable alternatives | Boundary, overlap, and no-solution tests pass |
| 4. Reproducibility and polish | 2–3 days | Exports, guided demo, cached scenarios | Reload reproduces results; novice walkthrough succeeds |
| 5. Advanced planning | Subsequent iteration | Height, power, sensitivity, station mode | Each feature has model-specific validation |

### Minimum challenge demonstration

If time is limited, ship three curated sites, one verified date interval, synchronized horizons/timelines, a constrained window finder, provenance, and a scenario export. Choose dates only after inspecting validated results so the demonstration contains a meaningful trade-off.

A 48-hour interface prototype is plausible only if validated scientific bundles already exist. Otherwise reduce the feature set; do not claim to have built and validated the entire modelling pipeline in a weekend.

### Demonstration narrative

1. Open two real sites on identical dates.
2. Scrub to a computed shadow or Earth-blockage event.
3. Select “Explain” to highlight the blocking terrain direction.
4. Search for another start date and compare the resulting trade-offs.
5. Save a scenario with its assumptions and data sources.

## 11. Validation and acceptance

**Geometry:** compare Sun/Earth angular directions with an independent reference for multiple sites and times under matched conventions. Investigate differences above a provisional 0.01° angular-direction target; this is a software consistency target, not total physical accuracy.

**Terrain:** test a smooth sphere, a synthetic ridge, the azimuth seam, polar bearings, mast-height changes, NoData, and raster boundaries. Recompute with finer sampling and longer ray reach until the selected convergence criterion is met. Document any sites that fail.

**Events:** compare adaptive results to dense reference sampling, including brief gaps and grazing cases. A proposed one-minute refinement tolerance is algorithmic only; report larger terrain-driven uncertainty where applicable.

**Window search:** test disjoint visibility intervals, exact thresholds, end-of-data windows, duration longer than coverage, no passing sites, and missing inputs. Verify that the whole mission interval is evaluated.

**Power:** test panel facing away from the Sun, empty/full battery, efficiencies, varying load, reserve crossing, and unmet demand. Verify separate panel and antenna heights.

**Usability:** ask five unfamiliar users to compare two sites and find a lower-interruption window. Target four of five completing the task within two minutes without coaching, and being able to explain the Earth-visibility limitation.

**Reproducibility:** exported scenario inputs and pinned data versions must reproduce metrics within the declared numerical tolerance. Mark unavailable historical versions explicitly.

## 12. Risks and sensible fallbacks

| Risk | Response |
|---|---|
| Terrain products are large | Curated tiles and precomputed profiles; arbitrary pins later |
| Coordinate-frame mismatch | Block scientific release until reconciled; keep metadata visible |
| Published archive lacks desired field | Compute it independently or mark unavailable; do not invent a column |
| External service is unavailable | Use validated cached scenarios with their dates and source versions |
| Detailed 3D slows the app | Preserve the analytical 2D experience as default |
| Ranking hides trade-offs | Hard constraints plus raw metrics and transparent ordering |
| Users confuse geometry with readiness | Consistent labels and contextual scope statements |
| AI explains beyond the evidence | Template explanations first; later constrain AI to scenario results |

## 13. Build brief for another AI or development team

Build LunaScope 2.0 from this specification. Deliver the P0 comparison workflow before optional features. Begin by auditing actual terrain and source assets; do not fabricate candidate coordinates, field names, visibility percentages, or outage durations. Use deterministic scientific computation and immutable scenario provenance. Default to two sites on shared UTC dates, with synchronized horizon plots and separate sunlight, Earth-center visibility, and overlap timelines. Treat incomplete coverage as Unknown. Keep power estimates separate from sunlight and station communication separate from Earth-center visibility. Implement real-data export and an explainable window finder. Keep any illustrative fixtures isolated and clearly labelled. Ship only the supported sites and dates that pass validation.

**Product promise:** Make lunar lighting and Earth-visibility trade-offs understandable in a few interactions, while preserving enough evidence for a technical user to inspect every result.

## 14. Verified references and remaining audit work

Sources checked on 14 November 2026. Source pages and documentation were reviewed for this plan; terrain archives were not processed and no mission-window predictions were calculated.

- **[S1] NASA:** [The Sun's Path at Different Lunar Latitudes](https://svs.gsfc.nasa.gov/5038) and [Shadows near the Moon's South Pole](https://science.nasa.gov/resource/shadows-near-the-moons-south-pole/). Supports latitude-dependent geometry and distant terrain-shadow context.
- **[S2] Wueller et al.:** [Zenodo data record](https://zenodo.org/records/17084058), [paper DOI](https://doi.org/10.1029/2025JE009434). The record describes geospatial assets and midsummer 2025–2032 coverage. Attribute schemas, candidate counts, and precise definitions require download/audit.
- **[S3] NASA PGDA:** [A New View of the Lunar South Pole from LOLA](https://pgda.gsfc.nasa.gov/products/90). Documents available terrain products, their frame, and error/resolution layers. [High-resolution site topography](https://pgda.gsfc.nasa.gov/products/78) is an additional candidate source.
- **[S4] JPL NAIF:** [Lunar frame/kernel readme](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/aareadme.txt) and [lunar/Earth frame tutorial](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/Tutorials/pdf/individual_docs/23_lunar-earth_pck-fk.pdf). Supports compatible frame/orientation kernel selection.
- **[S5] JPL:** [Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html) and [API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html). Reference for observer coordinates and ephemeris requests.

The proposed architecture, UI, ranking rules, delivery estimates, and acceptance criteria are design recommendations, not features supplied by these sources.
