## Satellite RF Communications Calculator

Full-stack project for quickly exploring common satellite RF link calculations.
The backend is built with **FastAPI**, and the frontend is a **React / TypeScript** single-page app powered by **Vite**.

### Features

- **Link Budget**: FSPL and received power.
- **EIRP**: Effective isotropic radiated power.
- **G/T**: Antenna gain to noise temperature.
- **Eb/N0**: From carrier-to-noise density and data rate.
- **BCD Utility**: Encode/decode Binary Coded Decimal.
- **Phased Array Gain**: From element gain, array size, and efficiency.

---

### Backend (FastAPI)

Located in `backend/`.

- Entry module: `app/main.py` (FastAPI app instance is `app`).
- Routers under `app/routers/` expose calculation endpoints (all under `/api/calculations/...`).
- Calculation logic implemented in `app/services/`.

**Install dependencies**

```bash
cd /Users/jimlee/Projects/satellite_rf_app/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Run the backend**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`, with docs at `http://localhost:8000/docs`.

---

### Frontend (React / TypeScript)

Located in `frontend/`.

**Install dependencies**

```bash
cd /Users/jimlee/Projects/satellite_rf_app/frontend
npm install
```

**Run the dev server**

```bash
npm run dev
```

This starts Vite on `http://localhost:3000`. The frontend assumes the backend is running at `http://localhost:8000`.

---

### API Overview

All endpoints are prefixed with `/api` (e.g. `/api/calculations/link-budget`).
Payloads are JSON and follow standard RF units:

- **Link Budget**: `frequency_hz`, `distance_m`, `tx_power_dbw`, `tx_antenna_gain_db`, `rx_antenna_gain_db`, optional losses.
- **EIRP**: `tx_power_dbw`, `tx_antenna_gain_db`, optional `tx_losses_db`.
- **G/T**: `antenna_gain_db`, `system_noise_temp_k`.
- **Eb/N0**: `cn0_db_hz`, `data_rate_bps`.
- **BCD Encode**: `value`, `digits`.
- **BCD Decode**: `bcd_bits` bit string.
- **Phased Array Gain**: `element_gain_db`, `num_elements`, optional `array_efficiency`.

You can explore and test these directly via the automatically generated Swagger UI at `/docs`.



