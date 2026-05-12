## Satellite RF Communications Calculator

Full-stack project for quickly exploring common satellite RF link calculations.
The backend is a **FastAPI** service deployed to **Google Cloud Run**, and the
frontend is a **React / TypeScript** single-page app powered by **Vite** and
deployed to **Firebase Hosting**.

### Features

- **Link Budget**: FSPL and received power.
- **EIRP**: Effective isotropic radiated power.
- **G/T**: Antenna gain to noise temperature.
- **Eb/N0**: From carrier-to-noise density and data rate.
- **Phased Array Gain**: From element gain, array size, and efficiency.
- **Azimuth / Elevation**: Pointing geometry to a satellite.
- **Scan Loss**, **Beam Off-Axis**, **Weather Loss**.
- **Duplex Satellite Link**: Forward + return bent-pipe link budget.

---

## Project Structure

```
satellite_rf_app/
├── README.md
├── .gitignore
├── dev.sh                                # One-shot local dev launcher
├── backend/
│   ├── Dockerfile                        # Cloud Run image build
│   ├── .dockerignore
│   ├── pyproject.toml                    # uv-managed Python deps
│   ├── .python-version
│   └── app/
│       ├── main.py                       # FastAPI app entry point
│       ├── routers/calculations.py       # /api/calculations/...
│       └── services/                     # Calculation logic
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── firebase.json                     # Firebase Hosting config
    ├── .firebaserc                       # Firebase project selector
    ├── .env.example                      # Local dev env template
    ├── .env.production                   # Prod build env (loaded by Vite)
    └── src/
        ├── App.tsx
        ├── apiClient.ts                  # API base URL + fetch wrapper
        └── components/                   # Per-calculation UIs
```

---

## Production URLs

| Service | URL |
|---|---|
| Frontend (Firebase Hosting) | `https://satellite-rf-app.web.app` |
| Backend (Cloud Run) | `https://satellite-rf-backend-REPLACE_ME.us-west4.run.app` |
| Backend API docs | `https://satellite-rf-backend-REPLACE_ME.us-west4.run.app/docs` |

> Replace the `REPLACE_ME` segment with the project-number prefix that Cloud
> Run assigns after the first deploy, and update
> [`frontend/.env.production`](frontend/.env.production) with the real URL.

---

## Local Development

### Quick start

From the repository root:

```bash
./dev.sh
```

This script:
- runs `uv sync` in `backend/` to install Python deps,
- starts `uvicorn app.main:app` on `http://localhost:8123`,
- runs `npm install` in `frontend/` if needed, and
- starts the Vite dev server on `http://localhost:3000`.

Press `Ctrl+C` to stop the frontend; the backend is killed automatically.

### Backend

Requires [uv](https://docs.astral.sh/uv/).

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8123
```

The API will be available at `http://localhost:8123`, with interactive docs at
`http://localhost:8123/docs`.

### Backend tests

```bash
cd backend
uv run pytest
```

### Frontend

Requires Node.js >= 18.

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at `http://localhost:3000` and proxies `/api` requests
to the backend at port 8123 via the Vite dev-server proxy (configured in
[`frontend/vite.config.ts`](frontend/vite.config.ts)).

> **Local dev vs production:** In local development the frontend sends
> relative `/api/...` requests that the Vite proxy forwards to the backend on
> `localhost:8123`. In production there is no proxy — the frontend calls the
> Cloud Run backend URL directly (see *Frontend Deployment* below).

#### API Base URL Behavior

The frontend uses the `VITE_API_BASE_URL` environment variable to decide
where API requests are sent:

| Environment | `VITE_API_BASE_URL` | API calls go to |
|---|---|---|
| Local dev (`npm run dev`) | **unset** (default) | Relative `/api/...` — handled by the Vite dev proxy to `localhost:8123` |
| Production build (`npm run build`) | Read from `frontend/.env.production` | Full URL, e.g. `https://satellite-rf-backend-...run.app/api/...` |

Vite automatically loads [`frontend/.env.production`](frontend/.env.production)
when it builds in production mode, so a plain `npm run build` always produces
a deploy-ready bundle.

To override in local development (e.g. to point at the remote backend):

```bash
VITE_API_BASE_URL=https://satellite-rf-backend-REPLACE_ME.us-west4.run.app npm run dev
```

---

## Deployment — Backend (Cloud Run)

The backend is a Dockerized FastAPI service deployed to **Google Cloud Run**.

| Detail | Value |
|---|---|
| GCP Project | `satellite-rf-app` |
| Artifact Registry region | `us-west4` |
| Artifact Registry repo | `satellite-rf-backend` |
| Cloud Run service | `satellite-rf-backend` |
| Image path | `us-west4-docker.pkg.dev/satellite-rf-app/satellite-rf-backend/satellite-rf-backend` |

### Prerequisites (one-time)

- [Docker](https://docs.docker.com/get-docker/) with `buildx` (bundled with
  Docker Desktop).
- [`gcloud` CLI](https://cloud.google.com/sdk/docs/install) authenticated
  against the project:
  ```bash
  gcloud auth login
  gcloud config set project satellite-rf-app
  gcloud auth configure-docker us-west4-docker.pkg.dev
  ```
- An Artifact Registry repo named `satellite-rf-backend` in `us-west4`
  (create once with `gcloud artifacts repositories create ...`).

### Rebuild & Redeploy

Run from the **repository root**. Pick a **new, unique tag** for every
release (e.g. `v1`, `v2`, ..., or a git short SHA). Reusing an existing tag
makes rollbacks harder and can leave Cloud Run on an older digest.

**1. Pick a tag and export it:**

```bash
export TAG=v1   # bump each release (v2, v3, ...), or use: $(git rev-parse --short HEAD)
export IMAGE=us-west4-docker.pkg.dev/satellite-rf-app/satellite-rf-backend/satellite-rf-backend:$TAG
```

**2. Build and push the Docker image** (linux/amd64 is required by Cloud
Run, even from an Apple Silicon Mac):

```bash
docker buildx build --platform linux/amd64 \
  -t "$IMAGE" \
  -f backend/Dockerfile backend \
  --push
```

**3. Deploy the new image to Cloud Run:**

```bash
gcloud run deploy satellite-rf-backend \
  --image "$IMAGE" \
  --region us-west4 \
  --platform managed \
  --allow-unauthenticated
```

**4. Verify the deploy:**

```bash
curl -fsS https://satellite-rf-backend-REPLACE_ME.us-west4.run.app/health
# -> {"status":"ok"}
```

### Rollback

```bash
gcloud run deploy satellite-rf-backend \
  --image us-west4-docker.pkg.dev/satellite-rf-app/satellite-rf-backend/satellite-rf-backend:<previous-tag> \
  --region us-west4 --platform managed --allow-unauthenticated
```

List previously-built tags:

```bash
gcloud artifacts docker images list \
  us-west4-docker.pkg.dev/satellite-rf-app/satellite-rf-backend/satellite-rf-backend \
  --include-tags
```

---

## Deployment — Frontend (Firebase Hosting)

The frontend is a React + TypeScript + Vite SPA deployed to **Firebase
Hosting**.

### Prerequisites (one-time)

- [Firebase CLI](https://firebase.google.com/docs/cli) installed and
  authenticated (`firebase login`).
- `frontend/.firebaserc` references the Firebase project `satellite-rf-app`
  (update if your project ID differs).

### Rebuild & Redeploy

Run from the **`frontend/` directory**:

```bash
cd frontend
npm install        # only if dependencies changed
npm run deploy     # builds with production env, then deploys hosting
```

`npm run deploy` is a shortcut for `npm run build && firebase deploy --only
hosting`. Run them separately if needed:

```bash
npm run build                      # produces dist/ using frontend/.env.production
firebase deploy --only hosting     # uploads dist/ to Firebase Hosting
```

The build picks up `VITE_API_BASE_URL` from
[`frontend/.env.production`](frontend/.env.production), which points at the
Cloud Run backend. The [`frontend/firebase.json`](frontend/firebase.json) is
configured for a single-page app — all routes rewrite to `index.html`.

### Changing the backend URL used by the frontend

Edit the one-line file
[`frontend/.env.production`](frontend/.env.production):

```
VITE_API_BASE_URL=https://satellite-rf-backend-REPLACE_ME.us-west4.run.app
```

then redeploy with `npm run deploy`. For a one-off build against a different
backend (e.g. a staging environment) without editing the file:

```bash
VITE_API_BASE_URL=https://staging-backend.run.app npm run build
firebase deploy --only hosting
```

---

## Full Release Checklist

A typical end-to-end release from a clean `main` branch:

```bash
# --- 1. Backend ---
cd /path/to/satellite_rf_app
export TAG=v1   # bump each release
export IMAGE=us-west4-docker.pkg.dev/satellite-rf-app/satellite-rf-backend/satellite-rf-backend:$TAG
docker buildx build --platform linux/amd64 -t "$IMAGE" -f backend/Dockerfile backend --push
gcloud run deploy satellite-rf-backend --image "$IMAGE" \
  --region us-west4 --platform managed --allow-unauthenticated
curl -fsS https://satellite-rf-backend-REPLACE_ME.us-west4.run.app/health

# --- 2. Frontend ---
cd frontend
npm run deploy
```

If you change the backend URL in `frontend/.env.production`, also add the
new hosting origin to the CORS allow-list in
[`backend/app/main.py`](backend/app/main.py) and redeploy the backend.

---

## Notes & Gotchas

### CORS

The FastAPI backend must include every origin that will call it in its CORS
`allow_origins` list ([`backend/app/main.py`](backend/app/main.py)). The
current allowed origins are:

| Origin | Purpose |
|---|---|
| `http://localhost:3000` | Local Vite dev server |
| `http://localhost:5173` | Alternate Vite dev port |
| `https://satellite-rf-app.web.app` | Firebase Hosting (primary) |
| `https://satellite-rf-app.firebaseapp.com` | Firebase Hosting (alternate) |

If you add a new hosting domain or change the Firebase project, update the
CORS list in `main.py` **and** redeploy the backend.

### Architecture Overview

```
+---------------------+         +-----------------------------+
|  Firebase Hosting   |  HTTPS  |  Google Cloud Run           |
|  (static SPA)       | ----->  |  (FastAPI Docker image)     |
|  satellite-rf-app   |         |  satellite-rf-backend-...   |
|  .web.app           |         |  .us-west4.run.app          |
+---------------------+         +-----------------------------+
        ^                                ^
        |  npm run deploy                |  docker buildx build ... --push
        |  (build + firebase deploy)     |  gcloud run deploy
        |                                |
   frontend/                        backend/
```

- **Local dev** — Vite proxies API requests (`localhost:3000` ->
  `localhost:8123`); no CORS needed for local-to-local calls.
- **Production** — The browser loads the SPA from Firebase Hosting and makes
  direct `fetch()` calls to the Cloud Run backend URL. CORS headers are
  required because the two origins differ.

### Docker Platform

Cloud Run requires a `linux/amd64` image. The `--platform linux/amd64` flag
in the `docker buildx build` command ensures the image is built for the
correct architecture, even when building on an Apple Silicon (arm64) Mac.

---

## API Overview

All endpoints are prefixed with `/api` (e.g. `/api/calculations/link-budget`).
Payloads are JSON and follow standard RF units:

- **Link Budget**: `frequency_hz`, `distance_m`, `tx_power_dbw`,
  `tx_antenna_gain_db`, `rx_antenna_gain_db`, optional losses.
- **EIRP**: `tx_power_dbw`, `tx_antenna_gain_db`, optional `tx_losses_db`.
- **G/T**: `antenna_gain_db`, `system_noise_temp_k`.
- **Eb/N0**: `cn0_db_hz`, `data_rate_bps`.
- **Phased Array Gain**: `element_gain_db`, `num_elements`, optional
  `array_efficiency`.
- **Azimuth / Elevation**, **Scan Loss**, **Beam Off-Axis**, **Weather Loss**,
  **Duplex Satellite Link** — see Swagger UI for full schemas.

Explore and test these directly via the automatically generated Swagger UI
at `/docs`.
