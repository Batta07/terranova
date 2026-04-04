# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Terranova is a **PCTO school project** — a holiday management system (gestionale ferie) for a company. It is a **frontend-only prototype** with no backend or real database. All data is hardcoded in JavaScript. The SQL files describe the intended relational database design for the full system.

**The evaluation focuses on**: requirements analysis, DB design, architecture, UI, and documentation — code is a bonus, not the core deliverable.

## Running the site locally

```bash
python3 -m http.server 8080 --directory site/
```

Then open `http://localhost:8080`.

## Repository structure

```
terranova/
├── site/           # The frontend prototype (HTML/CSS/JS)
│   ├── index.html  # Single-page app — all screens in one file
│   ├── styles.css  # All styles
│   └── app.js      # All logic (navigation, calendar, heatmap)
├── docs/           # Project documentation and DB design
│   ├── terranova.pdf              # Original requirements (PCTO spec)
│   ├── terranova_mockup/          # UI mockup screenshots (PNG)
│   ├── schema_er_terranova.sql    # DDL — full relational schema
│   ├── insert_terranova.sql       # Sample data inserts
│   └── select_terranova.sql       # Query collection (login, dashboard, admin, analytics)
├── Dockerfile
├── docker-compose.yml
└── DEPLOY.md
```

## Frontend architecture (site/)

The site is a **single HTML file** with vanilla JS. There is no build step, no bundler, no framework.

**Navigation model**: all screens exist in the DOM simultaneously as `<section id="screen-*">` elements. The JS `navigateTo(screenId)` function toggles the `screen--active` class to show/hide them. Screens: `login`, `dashboard`, `requests`, `new-request`, `request-detail`, `team`, `admin`, `settings`.

**State**: a single `state` object in `app.js` holds `currentScreen`, `calendarDate`, and `activeFilters`.

**Data**: `people` and `bookings` objects in `app.js` are hardcoded — they simulate what would come from the DB in a real backend.

**Admin panel**: uses a tab system (`data-admin-tab` attribute) with three panels: `users`, `rules`, `simulation`.

## Database design (docs/)

The schema has 8 tables with this dependency order for inserts:

1. `ruoli` → 2. `gruppi` → 3. `utenti` → ALTER `gruppi.id_responsabile` → 4. `periodi_vacanza` → 5. `periodi_bloccati` → 6. `vincoli_presenza` → 7. `richieste_vacanza` → 8. `commenti`

Key design decisions:
- `gruppi.id_responsabile` is a circular FK to `utenti` — added with ALTER TABLE after `utenti` is created
- `richieste_vacanza.id_approvatore` is nullable (NULL = not yet assigned)
- `periodi_bloccati.id_ruolo` is nullable (NULL = applies to all roles)
- The SQL dialect used is **PostgreSQL** (uses `generate_series`, `FILTER`, `INTERVAL`, string concatenation with `||`)

## Deployment (VPS)

See `DEPLOY.md`. The site is served via nginx in Docker — `Dockerfile` and `docker-compose.yml` are already configured for the VPS. Do not use Docker locally.
