# Architettura — Terranova
## Sistema di Gestione del Calendario Ferie Aziendale

---

## 1. Stack tecnologico

### Flask (Python)
Flask è il framework web lato server che gestisce sia le chiamate API REST (sotto `/api/`) sia la distribuzione del frontend come file statico. È stato scelto per la sua leggerezza e la configurazione minima richiesta: un singolo file `app.py` contiene tutta la logica applicativa, i middleware di autenticazione e le route.

### MySQL
Il database relazionale usato per la persistenza dei dati. Gira in un container Docker separato e comunica con Flask tramite la rete interna Docker. È stato scelto per la sua solidità in ambienti multi-utente, il supporto nativo ai tipi `DATE`/`ENUM` e la compatibilità con lo schema progettato in fase di analisi.

### Docker
L'intera applicazione viene eseguita tramite Docker Compose, che orchestra due container separati: uno per Flask/Gunicorn e uno per MySQL. Garantisce un ambiente riproducibile e isolato su qualsiasi macchina. L'avvio completo avviene con un singolo comando: `docker compose up --build`.

### HTML
Il frontend è un'unica pagina HTML (`index.html`) che contiene tutte le schermate dell'applicazione come elementi `<section>` nel DOM. Non viene usato nessun framework o sistema di templating lato client: la struttura è statica e il contenuto viene popolato interamente via JavaScript.

### CSS
Foglio di stile unico (`styles.css`) che definisce il design dell'interfaccia. Utilizza variabili CSS custom per il sistema di colori, layout Flexbox per la struttura delle pagine e classi di stato (`.screen--active`, `.cal-day--nonbookable`) per guidare la logica visiva.

### JavaScript
Logica frontend completa in un unico file `app.js` vanilla, senza framework né bundler. Gestisce la navigazione tra schermate, le chiamate alle API tramite `fetch`, il rendering dinamico del calendario e dei componenti, e la gestione dello stato locale dell'interfaccia.

---

## 2. Modello client-server

Terranova segue un'architettura **monolitica client-server** in cui Flask svolge un doppio ruolo:

1. **File server** — serve `index.html`, `styles.css` e `app.js` direttamente dalla root del progetto (`static_folder='.'`). Il browser riceve l'intera SPA al primo accesso.
2. **API server** — espone un'API REST sotto `/api/` che il JavaScript chiama per leggere e scrivere dati. Ogni risposta è JSON.

```
Browser
  │
  ├── GET /            → Flask restituisce index.html
  ├── GET /styles.css  → Flask restituisce styles.css
  ├── GET /app.js      → Flask restituisce app.js
  │
  └── fetch('/api/...') → Flask elabora la richiesta
                            ├── verifica sessione (cookie)
                            ├── query MySQL
                            └── restituisce JSON
```

La separazione tra frontend e backend è logica, non fisica: entrambi girano nello stesso processo Python, nello stesso container.

---

## 3. Single Page Application (SPA)

Il frontend è una **SPA senza framework**: l'HTML di tutte le schermate è presente nel DOM sin dal caricamento. La navigazione avviene aggiungendo o rimuovendo la classe `screen--active` sugli elementi `<section id="screen-*">` tramite la funzione `navigateTo(screenId)`.

| Schermata | ID DOM |
|---|---|
| Login | `screen-login` |
| Dashboard | `screen-dashboard` |
| Le mie richieste | `screen-requests` |
| Nuova richiesta | `screen-new-request` |
| Dettaglio richiesta | `screen-request-detail` |
| Il mio team | `screen-team` |
| Amministrazione | `screen-admin` |
| Impostazioni | `screen-settings` |

Questo approccio elimina i tempi di navigazione tra pagine e mantiene lo stato in memoria, senza dipendere da un router lato client.

---

## 4. Autenticazione e sessioni

L'autenticazione è **session-based** tramite cookie firmato Flask:

1. L'utente accede selezionando la propria email (prototipo) — in produzione tramite Google OAuth 2.0.
2. Flask imposta un cookie di sessione firmato con `SECRET_KEY`. Il cookie è `HttpOnly` e `SameSite=Lax`.
3. Ogni chiamata a `/api/*` include automaticamente il cookie. Flask lo verifica, recupera `user_id` dalla sessione e carica il profilo utente dal database.
4. I permessi (`is_manager`, `is_ceo`) vengono derivati a runtime dalle relazioni nel database, non da campi hardcoded.

Il flusso completo di Google OAuth 2.0 è documentato separatamente in [`google_oauth_flow.md`](google_oauth_flow.md).

---

## 5. Architettura Docker

### Struttura dei container

```
┌─────────────────────────────────────┐   rete interna Docker
│  Container: terranova               │ ─────────────────────────┐
│                                     │                           │
│  python:3.12-slim                   │   ┌─────────────────────┐│
│  ├── gunicorn (2 worker)            │   │  Container: db       ││
│  │   └── app.py (Flask)             │   │                      ││
│  │       ├── /api/*  (REST API)     │──▶│  mysql:8.0           ││
│  │       └── /*      (file statici) │   │  porta 3306          ││
│  │                                  │   │  [volume persistente]││
│  Porta interna: 5000                │   └─────────────────────┘│
│  Porta host:    5001                │                           │
│  Utente:        appuser (uid 1001)  │ ──────────────────────────┘
└─────────────────────────────────────┘
```

### Scelte di sicurezza nel Dockerfile

- Il processo gira come **utente non-root** (`appuser`, uid 1001) per limitare i privilegi in caso di compromissione.
- Il server di produzione è **Gunicorn** (2 worker), non il development server di Flask.
- Il container include un **HEALTHCHECK** che verifica ogni 30 secondi che l'applicazione risponda su `localhost:5000`.

### docker-compose.yml

```yaml
services:
  db:
    image: mysql:8.0
    container_name: terranova-db
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: terranova
      MYSQL_USER: terranova
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
    networks:
      - terranova_net

  terranova:
    build: .
    container_name: terranova
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "5001:5000"
    networks:
      - terranova_net

volumes:
  db_data:

networks:
  terranova_net:
    driver: bridge
```

`restart: unless-stopped` garantisce il riavvio automatico in caso di crash o reboot del sistema host. `depends_on` con `condition: service_healthy` assicura che Flask non parta prima che MySQL sia pronto ad accettare connessioni.

---

## 6. Diagramma C4 — Livello 2 (Container)

> **Prompt da usare per generare il diagramma visivo:**
>
> *"Crea un diagramma C4 livello 2 (Container Diagram) per un'applicazione chiamata Terranova. Il sistema ha un solo utente esterno: il Browser dell'utente. Il browser comunica con un container chiamato 'Flask App' (tecnologia: Python/Flask, eseguito su Gunicorn dentro Docker). La Flask App serve file statici HTML/CSS/JS (SPA) al browser e gestisce chiamate REST API JSON. La Flask App comunica con un secondo container chiamato 'Database' (tecnologia: MySQL 8.0, porta 3306, volume Docker). Usa i colori ufficiali C4: blu per i container interni, grigio per gli attori esterni. Includi frecce etichettate: Browser→Flask 'HTTPS / cookie di sessione', Flask→MySQL 'SQL queries (porta 3306, rete interna Docker)'. Stile pulito, sfondo bianco, font sans-serif."*

---

## 7. Diagramma architettura Docker

> **Prompt da usare per generare il diagramma visivo:**
>
> *"Crea un diagramma architetturale per un'applicazione Docker Compose. C'è un Host macOS (o Ubuntu VPS) che contiene un Docker Engine. Dentro Docker Engine ci sono due container affiancati collegati da una rete interna chiamata 'terranova_net'. Il primo container ha bordo blu, si chiama 'terranova', contiene: Gunicorn (WSGI server) → Flask app.py; ha un'etichetta 'porta 5001:5000' e 'appuser (uid 1001)'. Il secondo container ha bordo arancione, si chiama 'terranova-db', contiene: MySQL 8.0, porta 3306, un cilindro etichettato 'volume db_data'. Una freccia entra da sinistra dal Browser verso il container terranova con label 'HTTP :5001'. Una freccia collega terranova a terranova-db con label 'SQL :3306'. C'è anche un'etichetta 'HEALTHCHECK' su entrambi i container. Usa sfondo bianco, font sans-serif, stile tecnico pulito."*

---

## 8. API REST — Riferimento rapido

Tutte le route sono documentate interattivamente su `/docs` (Swagger UI, generato da Flasgger).

| Metodo | Path | Descrizione |
|---|---|---|
| POST | `/api/auth/login` | Login (seleziona utente per email) |
| POST | `/api/auth/logout` | Termina la sessione |
| GET | `/api/auth/me` | Utente corrente |
| GET | `/api/dashboard` | Statistiche + richieste recenti |
| GET | `/api/calendar/<year>/<month>` | Dati calendario mensile + giorni bloccati |
| GET/POST | `/api/requests` | Lista richieste / crea nuova richiesta |
| GET | `/api/requests/<id>` | Dettaglio richiesta + commenti |
| POST | `/api/requests/<id>/approve` | Approva (solo responsabile) |
| POST | `/api/requests/<id>/reject` | Rifiuta con motivazione (solo responsabile) |
| POST | `/api/requests/<id>/comments` | Aggiunge commento |
| GET | `/api/team` | Membri del team + richieste del gruppo |
| GET/POST | `/api/admin/users` | Admin: gestione utenti |
| GET/POST | `/api/admin/groups` | Admin: gestione gruppi |
| GET/POST | `/api/admin/rules` | Admin: vincoli di presenza |
| GET/POST | `/api/admin/blocked-periods` | Admin: periodi bloccati |
| GET | `/api/admin/simulation` | Admin: simulazione copertura |
| GET/POST | `/api/user/profile` | Profilo utente corrente |
