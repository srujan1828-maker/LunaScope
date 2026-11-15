# Deploy LunaScope as one web service

The production container builds React and serves its assets, REST API and WebSockets from the same FastAPI service. No NASA API key is required. Use a container platform with persistent disk storage and WebSocket support. Configure one application process/replica: scenarios and live sessions currently use process memory.

## Windows / Docker Desktop

Start Docker Desktop with its Linux-container engine, then run in PowerShell:

```powershell
Set-Location 'D:\nasa_space app'
docker compose up --build -d
docker compose logs -f lunascope
```

Open http://localhost:8000 after `/api/ready` reports ready. The first start downloads approximately 47 MB of official files, verifies them against this release's recorded hashes and decodes the 116 MB raster. Allow several minutes. The named `nasa-data` volume preserves the files across container replacements. `docker compose down` stops the service while retaining that volume.

To use port 8000 in Docker, stop a separately running local LunaScope server on that port first. Alternatively change the host side of `8000:8000` in compose.yaml.

## Render

Create a Blueprint from this GitHub repository using `render.yaml`. It defines a Docker web service and a 1 GB persistent disk at `/app/data/nasa`. Review the platform's service/disk billing before creation. Automatic deploys are disabled in the blueprint; deploy the selected commit manually. Render supplies `PORT`; the container listens on `0.0.0.0` and uses `/api/ready` for health checks.

If the platform's smallest service cannot accommodate scientific arrays during concurrent requests, allocate more memory; 2 GB is a sensible starting allocation for this application, not a measured minimum. Avoid multiple replicas until scenario storage is moved to a shared database and live sessions have a routing strategy.

## Railway or another container host

Import the repository; `railway.json` selects the Dockerfile and readiness check. Attach a volume mounted at `/app/data/nasa`, set `LUNASCOPE_DATA_DIR=/app/data/nasa`, `LUNASCOPE_AUTO_FETCH=true` and `HOST=0.0.0.0`. Use the provider's `PORT`. The runtime user is UID 10001; the mounted directory must be readable and writable by that user. If a provider mounts an empty root-owned volume, initialize its ownership using that provider's volume administration tools.

The same Dockerfile works on a VM with Docker. Terminate HTTPS at the hosting provider or reverse proxy; forward both ordinary requests and WebSocket upgrade traffic to the service. Keep frontend and backend at the same origin. If a separate frontend is required, set `VITE_API_URL` at build time and `LUNASCOPE_ALLOWED_ORIGINS` to the exact frontend origins. The current deployment is designed around a same-origin UI.

## Settings

| Variable | Default / use |
|---|---|
| `HOST` | `0.0.0.0` in the container; `127.0.0.1` for ordinary local run.py |
| `PORT` | 8000, or host-supplied value |
| `LUNASCOPE_DATA_DIR` | `/app/data/nasa` in Docker; an absolute persistent directory |
| `LUNASCOPE_AUTO_FETCH` | `true`: fetch/verify official inputs before serving |
| `LUNASCOPE_ALLOWED_ORIGINS` | `*`; use exact comma-separated origins if split hosting is needed |
| `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` | 1 in Docker, preventing per-request thread over-allocation |

With automatic fetching disabled, install the same release's official inputs and manifest in the data directory beforehand. The application never substitutes synthetic terrain. Failed downloads, incompatible inputs or hash differences stop startup with an explanation.

`/api/live` reports process liveness. `/api/ready` returns 503 if required scientific files are missing. `/api/health` includes the data status. The cloud launcher prepares data before opening the port. No cloud account, domain, paid service or live deployment has been created by adding these files.

## Verification boundary

The repository includes a GitHub Actions workflow that runs scientific tests, builds the frontend and Docker image, then exercises container readiness and a surface frame. The [implementation verification run](https://github.com/srujan1828-maker/LunaScope/actions/runs/43688943898) passed dependency setup, NASA ingestion, scientific tests, frontend build, production image build and container smoke testing on Linux. Check newer runs for subsequent commits. Local Compose configuration can be checked without starting a container:

```powershell
docker compose config --quiet
```

The local Docker engine was stopped; image/build validation was completed on GitHub's Linux runner instead. This verifies the container, while a live hosted deployment remains a separate step. Consult [Render Docker documentation](https://render.com/docs/docker), [Render Blueprint specification](https://render.com/docs/blueprint-spec) and [Railway configuration reference](https://docs.railway.com/config-as-code/reference) for provider setup.
