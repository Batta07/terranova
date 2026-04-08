# Manuale di installazione — Terranova

---

## Prerequisiti

Prima di procedere, assicurarsi di avere installato sulla propria macchina:

| Software | Versione minima | Come verificare |
|---|---|---|
| **Docker Desktop** | 4.x o superiore | `docker --version` |
| **Docker Compose** | incluso in Docker Desktop | `docker compose version` |

Non sono necessari Python, MySQL, né altri strumenti: tutto è incluso nei container Docker.

---

## Installazione

### 1. Ottenere il codice sorgente

Clonare il repository Git del progetto:

```bash
git clone <url-repository>
cd terranova
```

Oppure estrarre il file `.zip` del progetto e aprire un terminale nella cartella estratta.

---

### 2. Avviare l'applicazione

Eseguire il seguente comando dalla cartella del progetto:

```bash
docker compose up --build
```

Questo comando:
- Costruisce l'immagine Docker del backend Flask
- Avvia il container dell'applicazione
- Inizializza automaticamente il database e lo popola con dati di esempio

La prima esecuzione richiede qualche minuto per il download delle immagini base. Le esecuzioni successive saranno molto più rapide.

---

### 3. Accedere all'applicazione

Una volta avviata, aprire il browser e navigare a:

```
http://localhost:5001
```

L'applicazione è pronta quando nel terminale compare la riga:

```
terranova  | [INFO] Booting worker with pid: ...
```

---

### 4. Effettuare il login

Terranova in modalità prototipo non richiede una password. Nella schermata di login:

1. Cliccare sul menu a tendina
2. Selezionare uno degli utenti precaricati (es. *Manuel Battaglia*, *Alberto Chesini*, *Alessandro Vistoli*)
3. Cliccare **Accedi**

Gli utenti disponibili hanno ruoli diversi:

| Utente | Ruolo | Accesso |
|---|---|---|
| Alessandro Vistoli | CEO | Pannello admin completo |
| Manuel Battaglia | Developer (Responsabile Frontend) | Dashboard + approvazioni team |
| Alberto Chesini | Developer (Responsabile Backend) | Dashboard + approvazioni team |
| Marco Rossi | Developer | Dashboard dipendente |

---

### 5. Fermare l'applicazione

Per fermare i container:

```bash
docker compose down
```

Per fermare e **cancellare anche i dati** (reset completo):

```bash
docker compose down -v
```

---

## Documentazione API

La documentazione interattiva delle API REST è disponibile su:

```
http://localhost:5001/docs
```

Permette di visualizzare tutte le route disponibili e testarle direttamente dal browser.

---

## Risoluzione problemi comuni

| Problema | Causa probabile | Soluzione |
|---|---|---|
| Porta 5001 già in uso | Un altro processo usa la porta | Cambiare la porta in `docker-compose.yml` da `5001:5000` a `5002:5000` |
| Container non si avvia | Build fallita | Controllare l'output di `docker compose up --build` per errori |
| Pagina non carica | Container non ancora pronto | Attendere qualche secondo e ricaricare |
| Dati non aggiornati | Cache del browser | Premere `Ctrl+Shift+R` (hard refresh) |
