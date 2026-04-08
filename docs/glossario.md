# Glossario — Terranova

Elenco dei termini tecnici utilizzati nella documentazione del progetto.

---

| Termine | Definizione |
|---|---|
| **API** | Application Programming Interface — insieme di regole che permettono a due programmi di comunicare tra loro. In Terranova, il frontend chiama le API del backend per leggere e scrivere dati. |
| **REST API** | Stile architetturale per le API che usa i metodi HTTP standard (GET, POST, PUT, DELETE) e restituisce dati in formato JSON. |
| **JSON** | JavaScript Object Notation — formato testuale leggero usato per scambiare dati tra frontend e backend. Es: `{"nome": "Manuel", "ruolo": "Developer"}`. |
| **SPA** | Single Page Application — applicazione web in cui tutta l'interfaccia è caricata in una sola pagina HTML; la navigazione tra schermate avviene via JavaScript senza ricaricare la pagina. |
| **Frontend** | La parte dell'applicazione visibile all'utente, che gira nel browser. In Terranova: `index.html`, `styles.css`, `app.js`. |
| **Backend** | La parte dell'applicazione che gira sul server, gestisce la logica di business e comunica con il database. In Terranova: `app.py` (Flask). |
| **Flask** | Framework web leggero per Python usato per costruire il backend di Terranova. Gestisce le route HTTP e la logica applicativa. |
| **Gunicorn** | WSGI server di produzione per applicazioni Python. Sostituisce il server di sviluppo di Flask e gestisce le richieste in modo più stabile ed efficiente. |
| **WSGI** | Web Server Gateway Interface — interfaccia standard che definisce come un server web comunica con un'applicazione Python. |
| **MySQL** | Sistema di gestione di database relazionali open source. Usato in Terranova per memorizzare utenti, richieste, vincoli e commenti. |
| **SQL** | Structured Query Language — linguaggio usato per interrogare e manipolare database relazionali. |
| **Docker** | Piattaforma che permette di eseguire applicazioni in container isolati, garantendo che l'ambiente sia identico su qualsiasi macchina. |
| **Container** | Unità di esecuzione isolata creata da Docker, che include il codice, le dipendenze e la configurazione necessari per far girare un'applicazione. |
| **Docker Compose** | Strumento per definire e avviare applicazioni multi-container tramite un file di configurazione YAML (`docker-compose.yml`). |
| **Volume Docker** | Meccanismo di persistenza dei dati in Docker: permette ai dati del database di sopravvivere al riavvio del container. |
| **Sessione** | Meccanismo che permette al server di ricordare chi è un utente tra una richiesta e l'altra. In Flask, la sessione è memorizzata in un cookie firmato nel browser. |
| **Cookie** | Piccolo file di testo salvato dal browser che viene inviato automaticamente al server ad ogni richiesta. Usato per mantenere la sessione di login. |
| **OAuth 2.0** | Protocollo di autorizzazione standard che permette di autenticarsi tramite un provider esterno (es. Google) senza condividere la password con l'applicazione. |
| **Google OAuth** | Implementazione di OAuth 2.0 da parte di Google. Permette agli utenti di accedere a Terranova con il proprio account Google aziendale. |
| **Autenticazione** | Processo di verifica dell'identità di un utente (chi sei). |
| **Autorizzazione** | Processo di verifica dei permessi di un utente (cosa puoi fare). |
| **Route** | URL associato a una funzione nel backend. Es: la route `/api/requests` restituisce la lista delle richieste di ferie. |
| **Swagger / OpenAPI** | Standard per documentare le API REST in modo interattivo. In Terranova è accessibile su `/docs` e permette di testare le API dal browser. |
| **Flasgger** | Libreria Python che genera automaticamente la documentazione Swagger leggendo le docstring delle funzioni Flask. |
| **Glassmorphism** | Stile grafico caratterizzato da superfici traslucide con effetto vetro smerigliato (backdrop blur), bordi semi-trasparenti e sfondi sfumati. |
| **CSS Custom Properties** | Variabili definite in CSS (es. `--primary: #1A1A2E`) che permettono di centralizzare i valori del design system e riusarli in tutto il foglio di stile. |
| **Flexbox** | Sistema di layout CSS che permette di distribuire elementi in una riga o colonna con allineamento e spaziatura flessibili. |
| **Healthcheck** | Comando configurato nel Dockerfile che Docker esegue periodicamente per verificare che il container sia ancora funzionante. |
| **Seed** | Script (`seed.py`) che popola il database con dati di esempio al primo avvio, rendendo l'applicazione immediatamente utilizzabile senza configurazione manuale. |
| **PCTO** | Percorsi per le Competenze Trasversali e l'Orientamento — programma scolastico italiano che alterna formazione in aula con esperienza pratica in azienda o su progetti reali. |
