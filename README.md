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
├── Makefile                              # Install / dev / test / build / deploy targets
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

## Getting Started

### Run locally

From the repository root:

```bash
make install   # one-time: uv sync + npm install
make dev       # backend on :8123 + Vite on :3000
```

Open **http://localhost:3000** in your browser. Press `Ctrl+C` to stop.

Requires [uv](https://docs.astral.sh/uv/) and Node.js >= 18. See
[Local Development](#local-development) for backend-only / frontend-only options.

### Production site

| Service | URL |
|---|---|
| **Website (use this)** | **https://satellite-rf-app.web.app** |
| Alternate Firebase URL | `https://satellite-rf-app.firebaseapp.com` |
| Backend API | `https://satellite-rf-backend-427295995162.us-west4.run.app` |
| Backend API docs | `https://satellite-rf-backend-427295995162.us-west4.run.app/docs` |

The website URL is the one to bookmark. The backend URL is used internally by
the frontend and for API testing — Cloud Run always includes the GCP project
number in its default `*.run.app` address and that cannot be shortened.

### First-time production setup

Do this once per machine / GCP project before the first deploy.

1. **Install tools:** [Docker Desktop](https://docs.docker.com/get-docker/)
   (must be running), [`gcloud` CLI](https://cloud.google.com/sdk/docs/install),
   and [Firebase CLI](https://firebase.google.com/docs/cli).

2. **Authenticate:**
   ```bash
   gcloud auth login
   gcloud config set project satellite-rf-app
   gcloud auth configure-docker us-west4-docker.pkg.dev

   firebase login
   ```

3. **Link Firebase to the GCP project** (required before the first
   `make deploy-frontend`; skip if hosting is already set up):
   ```bash
   firebase projects:addfirebase satellite-rf-app
   ```

4. **Create the Artifact Registry repo** (skip if it already exists):
   ```bash
   gcloud artifacts repositories create satellite-rf-backend \
     --repository-format=docker \
     --location=us-west4 \
     --project=satellite-rf-app
   ```

5. **Deploy the backend** (needed before the frontend can call the API):
   ```bash
   make build-backend TAG=v1
   make deploy-backend TAG=v1
   ```

6. **Set the backend URL** in
   [`frontend/.env.production`](frontend/.env.production). Look it up with:
   ```bash
   gcloud run services describe satellite-rf-backend \
     --region=us-west4 --format='value(status.url)'
   ```
   Set `VITE_API_BASE_URL` to that value (no trailing slash). This repo
   already points at the live backend; update the file only if you deploy to
   a different GCP project.

7. **Deploy the frontend:**
   ```bash
   make deploy-frontend
   ```

8. **Verify:**
   ```bash
   curl -fsS https://satellite-rf-backend-427295995162.us-west4.run.app/health
   # -> {"status":"ok"}
   ```
   Open **https://satellite-rf-app.web.app** in your browser.

### Subsequent deploys

Pick a **new tag** for each release (`v2`, `v3`, or a git short SHA):

```bash
make deploy TAG=v2
```

Or deploy backend and frontend separately:

```bash
make build-backend TAG=v2 && make deploy-backend TAG=v2
make deploy-frontend
```

---

## Make Targets

The [`Makefile`](Makefile) wraps the common workflows so you don't have to
remember long `docker buildx` / `gcloud` / `firebase` invocations. Run any
target from the repository root.

| Target | What it does |
|---|---|
| `make install` | `uv sync` in `backend/` and `npm install` in `frontend/` |
| `make dev` | Runs [`./dev.sh`](dev.sh) (backend on `:8123` + Vite on `:3000`) |
| `make dev-backend` | Backend only: `uv run uvicorn app.main:app --reload --port 8123` |
| `make dev-frontend` | Frontend only: `npm run dev` |
| `make test` | `uv run pytest` in `backend/` |
| `make build-backend` | `docker buildx build --platform linux/amd64 ... --push` to Artifact Registry |
| `make deploy-backend` | `gcloud run deploy` using the freshly-pushed image |
| `make build-frontend` | `npm run build` (produces `frontend/dist/`) |
| `make deploy-frontend` | `npm run deploy` → builds + `firebase deploy --only hosting` |
| `make deploy` | Full release: `build-backend` → `deploy-backend` → `deploy-frontend` |

### Overridable variables

All GCP / image names default to the values in the table above. Override
them on the command line for one-off builds:

```bash
make build-backend TAG=v2                    # versioned release tag
make build-backend PROJECT_ID=staging-proj   # different GCP project
make deploy TAG=$(git rev-parse --short HEAD)  # tag with the current git SHA
```

| Variable | Default | Purpose |
|---|---|---|
| `PROJECT_ID` | `satellite-rf-app` | GCP project to push/deploy into |
| `REGION` | `us-west4` | Artifact Registry + Cloud Run region |
| `REPO` | `satellite-rf-backend` | Artifact Registry repository name |
| `IMAGE` | `satellite-rf-backend` | Image name within the repo |
| `SERVICE` | `satellite-rf-backend` | Cloud Run service name |
| `TAG` | `latest` | Image tag for build + deploy (bump per release) |

---

## Local Development

### Quick start

From the repository root:

```bash
make install   # one-time: uv sync + npm install
make dev       # runs ./dev.sh: backend on :8123 + Vite on :3000
```

`make dev` is a thin wrapper around [`dev.sh`](dev.sh), which:
- runs `uv sync` in `backend/` to install Python deps,
- starts `uvicorn app.main:app` on `http://localhost:8123`,
- runs `npm install` in `frontend/` if needed, and
- starts the Vite dev server on `http://localhost:3000`.

Press `Ctrl+C` to stop the frontend; the backend is killed automatically.

### Backend only

Requires [uv](https://docs.astral.sh/uv/).

```bash
make dev-backend
```

Equivalent to:

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8123
```

The API will be available at `http://localhost:8123`, with interactive docs at
`http://localhost:8123/docs`.

### Backend tests

```bash
make test
```

Equivalent to `cd backend && uv run pytest`.

### Frontend only

Requires Node.js >= 18.

```bash
make dev-frontend
```

Equivalent to `cd frontend && npm run dev`.

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
VITE_API_BASE_URL=https://satellite-rf-backend-427295995162.us-west4.run.app npm run dev
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

See [First-time production setup](#first-time-production-setup) for the full
checklist. In short: Docker Desktop running, `gcloud` and `firebase` CLI
authenticated, Firebase linked to the GCP project, and an Artifact Registry
repo in `us-west4`:

```bash
gcloud artifacts repositories create satellite-rf-backend \
  --repository-format=docker \
  --location=us-west4 \
  --project=satellite-rf-app
```

### Rebuild & Redeploy

Run from the **repository root**. Pick a **new, unique tag** for every
release (e.g. `v1`, `v2`, ..., or a git short SHA). Reusing an existing tag
makes rollbacks harder and can leave Cloud Run on an older digest.

**With `make` (recommended):**

```bash
make build-backend TAG=v1        # build (linux/amd64) and push to Artifact Registry
make deploy-backend TAG=v1       # deploy that image to Cloud Run
```

Or chain everything (backend image build + deploy + frontend deploy) in
one step:

```bash
make deploy TAG=v1
```

**Verify the deploy:**

```bash
curl -fsS https://satellite-rf-backend-427295995162.us-west4.run.app/health
# -> {"status":"ok"}
```

<details>
<summary>What <code>make build-backend</code> / <code>deploy-backend</code> run under the hood</summary>

```bash
export TAG=v1   # bump each release, or use: $(git rev-parse --short HEAD)
export IMAGE=us-west4-docker.pkg.dev/satellite-rf-app/satellite-rf-backend/satellite-rf-backend:$TAG

docker buildx build --platform linux/amd64 \
  -t "$IMAGE" \
  -f backend/Dockerfile backend \
  --push

gcloud run deploy satellite-rf-backend \
  --image "$IMAGE" \
  --region us-west4 \
  --platform managed \
  --allow-unauthenticated \
  --project satellite-rf-app
```

`linux/amd64` is required by Cloud Run, even from an Apple Silicon Mac.

</details>

### Rollback

Rollbacks aren't wrapped in a `make` target — running them by hand keeps the
previous tag explicit and harder to fat-finger:

```bash
gcloud run deploy satellite-rf-backend \
  --image us-west4-docker.pkg.dev/satellite-rf-app/satellite-rf-backend/satellite-rf-backend:<previous-tag> \
  --region us-west4 --platform managed --allow-unauthenticated
```

If you'd rather use the Makefile (which already takes `TAG` as a variable),
you can target an earlier tag with `make deploy-backend TAG=<previous-tag>`
— but the explicit form above forces you to look up the real tag first.

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
- Firebase linked to the GCP project (once per project):
  ```bash
  firebase projects:addfirebase satellite-rf-app
  ```
- `frontend/.firebaserc` references the Firebase project `satellite-rf-app`
  (update if your project ID differs).
- [`frontend/.env.production`](frontend/.env.production) set to the Cloud Run
  backend URL (see [Changing the backend URL](#changing-the-backend-url-used-by-the-frontend)).

### Rebuild & Redeploy

**With `make` (recommended):**

```bash
make deploy-frontend     # build + firebase deploy --only hosting
```

Or just rebuild without deploying:

```bash
make build-frontend
```

<details>
<summary>What <code>make deploy-frontend</code> runs under the hood</summary>

```bash
cd frontend
npm install        # only if dependencies changed
npm run deploy     # = npm run build && firebase deploy --only hosting
```

If you want the two steps separately:

```bash
npm run build                      # produces dist/ using frontend/.env.production
firebase deploy --only hosting     # uploads dist/ to Firebase Hosting
```

</details>

The build picks up `VITE_API_BASE_URL` from
[`frontend/.env.production`](frontend/.env.production), which points at the
Cloud Run backend. The [`frontend/firebase.json`](frontend/firebase.json) is
configured for a single-page app — all routes rewrite to `index.html`.

### Changing the backend URL used by the frontend

Edit the one-line file
[`frontend/.env.production`](frontend/.env.production):

```
VITE_API_BASE_URL=https://satellite-rf-backend-427295995162.us-west4.run.app
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
cd /path/to/satellite_rf_app
make deploy TAG=v1   # bump TAG each release: v2, v3, ..., or $(git rev-parse --short HEAD)
curl -fsS https://satellite-rf-backend-427295995162.us-west4.run.app/health
# open https://satellite-rf-app.web.app
```

`make deploy` runs `build-backend` → `deploy-backend` → `deploy-frontend` in
order, so a single command rebuilds the image, ships it to Cloud Run, and
deploys the SPA to Firebase Hosting with the new backend URL baked in.

<details>
<summary>Equivalent raw commands</summary>

```bash
# --- 1. Backend ---
export TAG=v1
export IMAGE=us-west4-docker.pkg.dev/satellite-rf-app/satellite-rf-backend/satellite-rf-backend:$TAG
docker buildx build --platform linux/amd64 -t "$IMAGE" -f backend/Dockerfile backend --push
gcloud run deploy satellite-rf-backend --image "$IMAGE" \
  --region us-west4 --platform managed --allow-unauthenticated \
  --project satellite-rf-app

# --- 2. Frontend ---
cd frontend && npm run deploy
```

</details>

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

### Common deploy errors

| Error | Fix |
|---|---|
| `Cannot connect to the Docker daemon` | Start **Docker Desktop** and retry. |
| `Repository "satellite-rf-backend" not found` | Run the Artifact Registry create command in [First-time production setup](#first-time-production-setup). |
| Firebase `404` / `No Hosting site detected` on first deploy | Run `firebase projects:addfirebase satellite-rf-app`, then retry `make deploy-frontend`. |
| Frontend loads but API calls fail | Check `frontend/.env.production` has the correct Cloud Run URL, then redeploy the frontend. Also confirm the origin is in the CORS list in `backend/app/main.py`. |

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
