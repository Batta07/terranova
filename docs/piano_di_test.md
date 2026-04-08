# Piano di Test — Terranova

I test riportati sono stati eseguiti manualmente sul prototipo in esecuzione locale tramite `docker compose up --build`.

---

## Ambiente di test

| Parametro | Valore |
|---|---|
| Browser | Google Chrome 124 |
| Sistema operativo | macOS |
| URL applicazione | `http://localhost:5001` |
| Dati di test | Generati automaticamente da `seed.py` al primo avvio |

---

## Casi di test

### Autenticazione

| ID | Scenario | Input | Risultato atteso | Risultato ottenuto | Esito |
|---|---|---|---|---|---|
| T-01 | Login con utente esistente | Email: `manuel@terranova.it` | Accesso alla dashboard, nome utente visibile in navbar | Dashboard caricata correttamente con nome "Manuel Battaglia" | ✅ Superato |
| T-02 | Login con email non registrata | Email: `sconosciuto@test.it` | Messaggio di errore, nessun accesso | Errore "Utente non trovato", rimane sulla schermata di login | ✅ Superato |
| T-03 | Accesso a pagina protetta senza login | Navigare su `/` senza sessione attiva | Reindirizzamento alla schermata di login | Schermata di login mostrata | ✅ Superato |
| T-04 | Logout | Click su "Esci" dal menu avatar | Sessione terminata, reindirizzamento al login | Sessione cancellata, login mostrato | ✅ Superato |

---

### Creazione richiesta di ferie

| ID | Scenario | Input | Risultato atteso | Risultato ottenuto | Esito |
|---|---|---|---|---|---|
| T-05 | Richiesta valida in giorni lavorativi | Utente: Marco Rossi — Date: lunedì-venerdì | Richiesta creata con stato "In attesa" | Richiesta salvata, badge "In attesa" visibile | ✅ Superato |
| T-06 | Richiesta che include il weekend | Date: venerdì 10 – lunedì 13 aprile | Blocco con messaggio di errore | Errore "Il periodo selezionato include giorni di weekend" | ✅ Superato |
| T-07 | Richiesta in periodo bloccato aziendale | Date: 21-23 dicembre 2026 | Celle rosse nel calendario, richiesta bloccata | Celle visualizzate in rosso, errore "Periodo non prenotabile" all'invio | ✅ Superato |
| T-08 | CEO invia richiesta | Utente: Alessandro Vistoli — date valide | Richiesta approvata automaticamente (nessuna attesa) | Stato immediato "Approvata" senza passare da "In attesa" | ✅ Superato |

---

### Approvazione e rifiuto

| ID | Scenario | Input | Risultato atteso | Risultato ottenuto | Esito |
|---|---|---|---|---|---|
| T-09 | Responsabile approva richiesta del team | Utente: Manuel Battaglia — approva richiesta di Marco Rossi | Stato aggiornato ad "Approvata" | Badge aggiornato a "Approvata", timeline aggiornata | ✅ Superato |
| T-10 | Responsabile rifiuta senza motivazione | Click su "Rifiuta" senza inserire testo | Blocco con richiesta di motivazione | Campo motivazione evidenziato, rifiuto non eseguito | ✅ Superato |
| T-11 | Dipendente tenta di approvare una richiesta | Utente: Marco Rossi (non responsabile) — tenta approvazione | Errore 403, azione non consentita | API restituisce 403 Forbidden | ✅ Superato |
| T-12 | Azione su richiesta già approvata | Responsabile tenta di agire su richiesta già approvata | Pulsanti di azione non disponibili | Pulsanti Approva/Rifiuta non mostrati per richieste già chiuse | ✅ Superato |

---

### Commenti

| ID | Scenario | Input | Risultato atteso | Risultato ottenuto | Esito |
|---|---|---|---|---|---|
| T-13 | Proprietario aggiunge commento | Marco Rossi commenta la propria richiesta | Commento salvato e visibile nel thread | Commento apparso con nome e data | ✅ Superato |
| T-14 | Utente non autorizzato tenta di commentare | Utente senza legame con la richiesta | Errore 403 | API restituisce "Non autorizzato a commentare questa richiesta" | ✅ Superato |

---

### Pannello amministrativo

| ID | Scenario | Input | Risultato atteso | Risultato ottenuto | Esito |
|---|---|---|---|---|---|
| T-15 | Creazione nuovo utente con ruolo CEO | Admin inserisce ruolo CEO | Blocco con messaggio di errore | Errore "Non è possibile creare un altro utente con ruolo CEO" | ✅ Superato |
| T-16 | Creazione nuovo gruppo | Nome: "DevOps", Descrizione: "Team infrastruttura" | Gruppo creato e visibile nella lista | Gruppo aggiunto correttamente | ✅ Superato |
| T-17 | Visualizzazione simulazione copertura | Accesso al tab "Simulazione" | Percentuali di copertura per gruppo e tasso di approvazione | Dati mostrati correttamente in base alle richieste presenti | ✅ Superato |

---

## Riepilogo

| Totale test | Superati | Falliti |
|---|---|---|
| 17 | 17 | 0 |
