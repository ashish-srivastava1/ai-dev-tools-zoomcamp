# LearnLoop frontend

React 19 + Vite, react-router, Vitest + Testing Library. All backend calls go
through `src/api/client.js` (the only module that calls `fetch`).

```bash
npm install
npm run dev      # http://localhost:5173 - proxies /api and /health to the backend on :8000
npm test         # unit/component tests (Vitest, jsdom)
npm run lint     # oxlint
npm run build    # production build -> dist/ (served by FastAPI in the container)
```

`VITE_API_BASE_URL` (optional) points the UI at a different backend origin; by
default it uses the same origin (dev proxy / container).

## Structure

| Path | Purpose |
|---|---|
| `src/api/client.js` | API client: paths, bearer write token, `{detail}` -> `ApiError` with field errors |
| `src/pages/DashboardPage.jsx` | Key journey: stats, log-session form, per-track progress, 8-week trend, recent sessions |
| `src/pages/TracksPage.jsx` | Tracks CRUD + archive, modules per track |
| `src/pages/SessionsPage.jsx` | Log, filter, paginate, edit and delete sessions |
| `src/pages/SettingsPage.jsx` | Weekly goal, timezone, week start, optional write token |
| `src/components/` | SessionForm, TrackForm, ModuleList, ProgressBar, TrendChart, ErrorBanner |
| `src/lib/format.js` | Formatting and timezone-aware "today" helpers |
