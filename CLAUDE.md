# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Terranova is a **PCTO school project** — a holiday management system (gestionale ferie) for a company. It has a Flask + SQLite backend that also serves the frontend as static files.

**The evaluation focuses on**: requirements analysis, DB design, architecture, UI, and documentation — code is a bonus, not the core deliverable.

## Running the site — ALWAYS use Docker

**Always run this project with Docker. Never suggest python directly, never suggest venv, never suggest any other method.**

```bash
docker compose up --build
```

Then open `http://localhost:5000`.

To stop:
```bash
docker compose down
```

## Repository structure

```
terranova/
├── app.py          # Flask backend + static file serving
├── db.py           # SQLite schema init
├── seed.py         # Sample data
├── index.html      # Single-page app frontend
├── styles.css      # All styles
├── app.js          # All frontend logic
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── docs/           # Project documentation and DB design
    ├── terranova.pdf
    ├── terranova_mockup/
    ├── schema_er_terranova.sql
    ├── insert_terranova.sql
    ├── select_terranova.sql
    ├── analisi_requisiti.md
    └── scelte_progettuali.md
```

## Frontend architecture

Single HTML file with vanilla JS, no build step, no framework. Flask serves it as a static file.

**Navigation model**: all screens exist in the DOM as `<section id="screen-*">` elements. `navigateTo(screenId)` toggles `screen--active`. Screens: `login`, `dashboard`, `requests`, `new-request`, `request-detail`, `team`, `admin`, `settings`.

**Admin panel**: tab system via `data-admin-tab` — three panels: `users`, `rules`, `simulation`.

## Backend

Flask app (`app.py`) serves the frontend from the root directory (`static_folder='.'`) and exposes a REST API under `/api/`. SQLite database (`terranova.db`) is created and seeded automatically on first run.

## Database design (docs/)

SQLite in development/Docker. Schema defined in `db.py` (not the SQL files — those are for documentation/MySQL).

Key design decisions:
- `Gruppi.id_responsabile` is a circular FK to `Utenti` — set after users are inserted
- `RichiesteVacanza.id_approvatore` is nullable (NULL = not yet assigned)
- `periodi_bloccati.id_ruolo` is nullable (NULL = applies to all roles)

## API routes

All routes are in `app.py`. Auth is session-based (Flask `session`).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/users` | List all users (for dev login picker) |
| POST | `/api/auth/login` | Login by email (no password — dev mode) |
| POST | `/api/auth/logout` | Clear session |
| GET | `/api/auth/me` | Current user |
| GET | `/api/dashboard` | Dashboard stats + recent requests |
| GET | `/api/calendar/<year>/<month>` | Bookings for calendar rendering |
| GET | `/api/heatmap/<year>/<month>` | Presence heatmap per team member |
| GET/POST | `/api/requests` | List own requests / create new |
| GET | `/api/requests/<id>` | Request detail + comments + timeline |
| POST | `/api/requests/<id>/approve` | Approve (manager only) |
| POST | `/api/requests/<id>/reject` | Reject with motivation (manager only) |
| POST | `/api/requests/<id>/comments` | Add comment |
| GET | `/api/team` | Team members + all group requests |
| GET | `/api/admin/users` | Admin: all users |
| GET | `/api/admin/groups` | Admin: all groups with member count |
| GET/POST | `/api/admin/rules` | Admin: presence constraints |
| GET | `/api/admin/simulation` | Admin: conflicts + coverage stats |
| GET/POST | `/api/user/profile` | View/update own profile |

**Auth in dev**: no Google OAuth — login picks any user by email from `/api/auth/users`. The `is_manager` flag is derived from `Gruppi.id_responsabile == user.id`.

## Deployment (VPS)

See `DEPLOY.md`. Docker is used both locally and on the VPS.
