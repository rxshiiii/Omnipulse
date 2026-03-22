# OmniPulse Frontend

React 18 + Tailwind dashboard for OmniPulse agent operations.

## Tech

- React 18 (CRA)
- Tailwind CSS 3
- React Query
- Zustand
- Recharts
- Axios

## Project Structure

- `src/App.jsx`: app shell + routes
- `src/pages/`: Dashboard, Compliance, Analytics, Loan Journey
- `src/components/`: UI widgets for queue, thread, draft, metrics
- `src/store/dashboardStore.js`: Zustand state
- `src/api/client.js`: REST + WebSocket client

## Local Setup

1. Install dependencies:

```bash
npm install
```

2. Start frontend:

```bash
npm start
```

3. Open:

```text
http://localhost:3000
```

## Required Environment Variables

- `REACT_APP_API_URL` (e.g. `http://localhost:8000`)
- `REACT_APP_WS_URL` (e.g. `ws://localhost:8000`)

## Build

```bash
npm run build
```

## Deploy Frontend on Vercel

Use a **New Project** from this repository with root directory `frontend`.

### Vercel Settings

- Framework Preset: Create React App
- Root Directory: `frontend`
- Build Command:

```bash
npm run build
```

- Output Directory:

```text
build
```

### Vercel Environment Variables

Set in Project Settings -> Environment Variables:

- `REACT_APP_API_URL=https://<your-render-backend>.onrender.com`
- `REACT_APP_WS_URL=wss://<your-render-backend>.onrender.com`

For local testing, use:

- `REACT_APP_API_URL=http://localhost:8000`
- `REACT_APP_WS_URL=ws://localhost:8000`

### Post-Deploy Checks

1. Open Vercel URL.
2. Check dashboard loads.
3. Confirm queue and thread APIs return data from Render backend.
4. Verify WebSocket badge turns connected.

## Troubleshooting

- If UI is empty, verify queue API:

```bash
curl "https://<your-render-backend>.onrender.com/api/agents/queue?bank_id=union_bank_demo"
```

- If WebSocket shows disconnected, confirm `REACT_APP_WS_URL` uses `wss://` for production.
