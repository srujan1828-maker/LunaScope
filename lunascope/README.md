# Legacy LunaScope Streamlit demonstration

This separate prototype is retained for compatibility and teaching. It is not the primary React/FastAPI app. Run `python run_lunascope.py` with the dependencies in this directory if you want to explore it.

The default catalog contains 15 hard-coded synthetic sites and assumed annual metrics. Terrain is procedural unless a raster is explicitly supplied and successfully read. A filename or presence check does not validate a scientific source. Astronomy is approximate and has no independent accuracy benchmark. Monte Carlo slopes, illumination and DTE are generated from assumed statistical distributions, not verified landing hazards. The slope sampler uses a gamma distribution. Its weighted “survival” score is an illustrative classification score, not a measured safety probability. Runtime depends on hardware and inputs.

Tests exercise bounds, consistency, reproducibility, and UI wiring. They do not authenticate data or prove physical accuracy. Published-source references identify future data sources; the active fallback is assumed/synthetic. Prior “scientifically rigorous”, fixed performance, verified-location, NASA participation and ground-truth claims are withdrawn.

See ../README.md and ../VERIFICATION.md for the supported application, limitations, and verification evidence.
