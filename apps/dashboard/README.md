# GuardianMesh Dashboard

A local-first operations dashboard for the GuardianMesh FastAPI service.

## Run locally

Keep the API running on port 8000, then open a second PowerShell terminal:

```powershell
cd C:\Users\Nithish\Downloads\GuardianMesh\GuardianMesh\apps\dashboard
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000>. Requests are proxied by the dashboard server, so Ring tokens and raw device IDs never reach the browser.

Set `GUARDIANMESH_API_URL` in `.env.local` only if the API is not running at `http://127.0.0.1:8000`.
