# Analisi dei Requisiti — Terranova
## Sistema di Gestione del Calendario Ferie Aziendale

---

## 1. Descrizione del dominio applicativo

Le aziende strutturate devono coordinare le ferie dei dipendenti rispettando contemporaneamente due esigenze opposte: la libertà del singolo di pianificare il proprio riposo e la necessità operativa di mantenere una copertura minima del personale. Senza uno strumento centralizzato, questa coordinazione avviene via email o fogli di calcolo condivisi, con frequenti sovrapposizioni, mancanza di visibilità e comunicazioni dispersive.

**Terranova** è un sistema informatico per la gestione del calendario ferie aziendale. Risolve tre problemi concreti:

1. **Visibilità condivisa** — ogni dipendente può vedere le ferie dei colleghi del proprio gruppo, evitando sovrapposizioni non intenzionali.
2. **Rispetto dei vincoli aziendali** — il sistema conosce le regole configurate dall'azienda (presenza minima per ruolo, periodi bloccati, finestre di prenotazione) e le applica automaticamente, segnalando le violazioni prima che diventino un problema.
3. **Flusso di approvazione tracciato** — ogni richiesta passa per un ciclo approvazione/rifiuto con commenti registrati, sostituendo le catene di email con una conversazione strutturata e auditabile.

---

## 2. Stakeholder e attori del sistema

| Attore | Ruolo nel sistema | Interesse principale |
|---|---|---|
| **Dipendente** | Utente finale che richiede le ferie | Pianificare le proprie ferie, conoscere lo stato delle richieste e avere visibilità sui colleghi |
| **Responsabile di gruppo** | Supervisore del team, anch'egli dipendente | Approvare o rifiutare le richieste del proprio gruppo, gestire i conflitti, garantire la copertura operativa |
| **Admin aziendale** | Amministratore del sistema | Configurare utenti, gruppi, ruoli, periodi di ferie e vincoli di presenza; monitorare la situazione complessiva |

> **Nota:** il Responsabile è a tutti gli effetti un utente del sistema — può lui stesso presentare richieste di ferie. Il suo ruolo aggiuntivo gli conferisce i permessi di approvazione sul proprio gruppo.

---

## 3. Requisiti funzionali

I requisiti funzionali sono suddivisi per attore e identificati con un codice univoco.

### RF-D — Dipendente

| ID | Requisito |
|---|---|
| RF-D01 | Il dipendente può effettuare il login tramite Google OAuth con l'email aziendale pre-autorizzata. |
| RF-D02 | Il dipendente visualizza un calendario condiviso con le proprie ferie, quelle dei colleghi del gruppo e i periodi prenotabili/bloccati. |
| RF-D03 | Il dipendente può inviare una nuova richiesta di ferie indicando data di inizio, data di fine e una nota opzionale. |
| RF-D04 | Il sistema verifica in tempo reale le regole aziendali durante la compilazione della richiesta e segnala eventuali violazioni prima dell'invio. |
| RF-D05 | Il dipendente può visualizzare lo storico delle proprie richieste con il relativo stato (in attesa, approvata, rifiutata). |
| RF-D06 | Il dipendente può aprire il dettaglio di una richiesta e leggere i commenti del responsabile. |
| RF-D07 | Il dipendente può aggiungere un commento a una propria richiesta per rispondere al responsabile. |

### RF-R — Responsabile di gruppo

| ID | Requisito |
|---|---|
| RF-R01 | Il responsabile visualizza tutte le richieste di ferie dei membri del proprio gruppo. |
| RF-R02 | Il responsabile può filtrare le richieste per stato (in attesa, approvate, rifiutate). |
| RF-R03 | Il responsabile può approvare o rifiutare una richiesta, anche in presenza di conflitti con i vincoli aziendali (previa motivazione). |
| RF-R04 | Il responsabile può aggiungere commenti a qualsiasi richiesta del proprio gruppo per comunicare con il dipendente. |
| RF-R05 | Il responsabile visualizza in evidenza le richieste che violano uno o più vincoli di presenza. |
| RF-R06 | Il responsabile ha accesso alle stesse funzionalità del dipendente per le proprie richieste personali. |

### RF-A — Admin aziendale

| ID | Requisito |
|---|---|
| RF-A01 | L'admin può creare, modificare e disattivare utenti nel sistema (nome, cognome, email, gruppo, ruolo). |
| RF-A02 | L'admin può creare e gestire gruppi di lavoro, assegnando un responsabile a ciascuno. |
| RF-A03 | L'admin può configurare i periodi di ferie prenotabili (data inizio, data fine, regole associate). |
| RF-A04 | L'admin può definire vincoli di presenza: numero minimo di dipendenti presenti per ruolo e/o per gruppo, permanenti o limitati a un intervallo di date. |
| RF-A05 | L'admin può definire periodi bloccati in cui le ferie non sono consentite (es. pre-lancio prodotto, chiusura di bilancio). |
| RF-A06 | L'admin visualizza tutte le richieste di ferie dell'azienda con possibilità di filtro per stato, gruppo e periodo. |
| RF-A07 | L'admin può visualizzare una simulazione della copertura del personale per i prossimi 30 giorni, con evidenza dei gruppi sotto soglia e della copertura complessiva aziendale. |
| RF-A08 | L'admin può rilevare sovrapposizioni tra richieste dello stesso gruppo che mettono a rischio la copertura minima. |

---

## 4. Requisiti non funzionali

| ID | Categoria | Requisito |
|---|---|---|
| RNF-01 | Sicurezza | L'autenticazione avviene esclusivamente tramite Google OAuth 2.0. Nessuna password viene memorizzata nel database di Terranova. |
| RNF-02 | Autorizzazione | L'accesso è consentito solo agli utenti la cui email è pre-caricata dall'admin nella tabella `Utenti`. Tentativi di accesso con email non registrata vengono rifiutati con messaggio esplicito. |
| RNF-03 | Accessibilità | Il sistema è accessibile tramite qualsiasi browser web moderno, senza installazione di software aggiuntivo. |
| RNF-04 | Lingua | L'interfaccia è interamente in italiano. |
| RNF-05 | Usabilità | Le violazioni dei vincoli aziendali vengono segnalate inline durante la compilazione, prima che l'utente invii la richiesta. |
| RNF-06 | Tracciabilità | Ogni interazione rilevante (approvazione, rifiuto, commento) viene registrata con data e autore nella tabella `Commenti`. |
| RNF-07 | Scalabilità | La struttura dati supporta più gruppi, più ruoli e più periodi di ferie configurabili senza modifiche allo schema. |

---

## 5. Use case

### UC-01 — Login con Google OAuth

| Campo | Dettaglio |
|---|---|
| **Attore** | Dipendente / Responsabile / Admin |
| **Precondizione** | L'utente ha un account Google con l'email aziendale pre-caricata nel sistema |
| **Flusso principale** | 1. L'utente apre il sistema e clicca "Accedi con Google" 2. Viene reindirizzato alla pagina di consenso Google 3. Google restituisce il profilo con email 4. Il sistema verifica che l'email esista in `Utenti` 5. La sessione viene creata e l'utente accede alla dashboard |
| **Flusso alternativo** | Se l'email non è registrata: il sistema mostra "Account non autorizzato — contatta l'amministratore" e nega l'accesso |
| **Postcondizione** | L'utente è autenticato e visualizza la schermata appropriata al suo ruolo |

---

### UC-02 — Invio nuova richiesta di ferie

| Campo | Dettaglio |
|---|---|
| **Attore** | Dipendente |
| **Precondizione** | L'utente è autenticato |
| **Flusso principale** | 1. L'utente accede a "Nuova richiesta" 2. Seleziona data di inizio e data di fine 3. Il sistema verifica in tempo reale i vincoli applicabili 4. L'utente aggiunge una nota opzionale 5. L'utente invia la richiesta 6. La richiesta viene salvata con stato `pending` e il responsabile può visualizzarla |
| **Flusso alternativo A** | Se le date includono un periodo bloccato: i giorni appaiono in rosso nel calendario del form con messaggio "Periodo non disponibile" — la richiesta è bloccata |
| **Flusso alternativo B** | Se la richiesta viola un vincolo di copertura minima: viene mostrato un banner arancione di avviso — la richiesta può essere inviata comunque, ma viene marcata come "in conflitto" |
| **Postcondizione** | La richiesta è registrata in `RichiesteVacanza` con stato `pending` e `id_approvatore = NULL` |

---

### UC-03 — Approvazione o rifiuto di una richiesta

| Campo | Dettaglio |
|---|---|
| **Attore** | Responsabile di gruppo |
| **Precondizione** | Il responsabile è autenticato; esiste almeno una richiesta `pending` nel suo gruppo |
| **Flusso principale** | 1. Il responsabile apre la sezione "Richieste del team" 2. Seleziona una richiesta in attesa 3. Visualizza i dettagli, il calendario del periodo e gli eventuali conflitti 4. Valuta la richiesta considerando il ruolo del richiedente e il periodo richiesto 5. Sceglie "Approva" o "Rifiuta" 6. Aggiunge un commento obbligatorio in caso di rifiuto, opzionale in caso di approvazione 7. Lo stato della richiesta viene aggiornato e il commento registrato |
| **Flusso alternativo** | Se la richiesta è in conflitto con i vincoli: viene mostrato un avviso esplicito — il responsabile può comunque procedere con l'approvazione inserendo una motivazione |
| **Postcondizione** | `RichiesteVacanza.stato` aggiornato a `approved` o `rejected`; `id_approvatore` impostato sull'utente corrente; commento registrato in `Commenti` |

---

### UC-04 — Configurazione vincoli di presenza

| Campo | Dettaglio |
|---|---|
| **Attore** | Admin aziendale |
| **Precondizione** | L'admin è autenticato e accede al pannello di amministrazione |
| **Flusso principale** | 1. L'admin accede al tab "Regole e Vincoli" 2. Seleziona "Aggiungi vincolo" 3. Configura: tipo (permanente o temporaneo), numero minimo di dipendenti, ruolo e/o gruppo applicabile, eventuale intervallo di date 4. Salva il vincolo |
| **Flusso alternativo** | Se il vincolo è temporaneo ma mancano le date: il sistema segnala l'errore e blocca il salvataggio |
| **Postcondizione** | Il vincolo è registrato in `VincoliPresenza` e viene applicato alle nuove richieste a partire dalla data configurata |

---

## 6. Regole di business

Le regole di business sono configurabili dall'admin e vengono applicate automaticamente dal sistema in fase di validazione delle richieste.

### RB-01 — Presenza minima per ruolo/gruppo

Per ogni gruppo e/o ruolo è possibile definire un numero minimo di dipendenti che devono essere presenti in azienda in ogni giorno lavorativo. Se una richiesta porterebbe il numero di presenti sotto questa soglia, il sistema la segnala come conflitto.

- **Tabella coinvolta:** `VincoliPresenza` (`permanente = TRUE`, `id_ruolo`, `id_gruppo`, `min_dipendenti`)
- **Esempio:** nel gruppo Frontend devono essere presenti almeno 2 Developer in ogni momento.

### RB-02 — Vincolo temporaneo su un periodo specifico

Analoga alla RB-01, ma attiva solo in un intervallo di date definito. Usata per gestire picchi operativi stagionali (estate, fine anno).

- **Tabella coinvolta:** `VincoliPresenza` (`permanente = FALSE`, `data_inizio`, `data_fine`)
- **Esempio:** durante luglio e agosto almeno 1 Developer del gruppo Backend deve essere presente.

### RB-03 — Periodi bloccati

L'azienda può bloccare completamente la prenotazione delle ferie in determinati intervalli (es. pre-lancio prodotto, chiusura di bilancio). In quei giorni nessuna richiesta può essere inviata. Il blocco può essere applicato a tutti i ruoli o limitato a uno specifico.

- **Tabella coinvolta:** `periodi_bloccati` (`data_inizio`, `data_fine`, `id_ruolo` nullable)
- **Esempio:** dal 20 al 21 dicembre le ferie sono bloccate per tutti.

### RB-04 — Finestre di prenotazione

Le ferie sono prenotabili solo in periodi esplicitamente aperti dall'azienda. Fuori da questi periodi, il calendario non permette la selezione.

- **Tabella coinvolta:** `periodi_vacanza` (`data_inizio`, `data_fine`)
- **Esempio:** periodo estivo dal 22 giugno al 31 agosto; periodo natalizio dal 22 al 31 dicembre.

### RB-06 — Continuità dei giorni lavorativi a cavallo del weekend

Un blocco di ferie che include venerdì e il lunedì successivo è considerato continuo ai fini del conteggio dei giorni e dei vincoli di durata minima/massima. I giorni di sabato e domenica vengono "saltati" ma non interrompono la continuità della richiesta.

- **Esempio:** una richiesta dal giovedì al martedì successivo (GIO, VEN, LUN, MAR) conta come 4 giorni lavorativi consecutivi, non come due blocchi separati.
- **Tabella coinvolta:** logica applicativa — nessuna modifica allo schema.

---

### RB-05 — Approvazione in deroga

Il responsabile può approvare una richiesta anche se viola uno o più vincoli, a sua discrezione. In questo caso deve registrare un commento che motivi la decisione. Il sistema non blocca l'azione ma la traccia.

- **Tabella coinvolta:** `Commenti` (commento obbligatorio del responsabile), `RichiesteVacanza.stato = 'approved'`

---

## 7. Matrice dei permessi

| Azione | Dipendente | Responsabile | Admin |
|---|---|---|---|
| Login con Google | ✓ | ✓ | ✓ |
| Visualizzare il proprio profilo | ✓ | ✓ | ✓ |
| Visualizzare calendario condiviso del gruppo | ✓ | ✓ | ✓ |
| Inviare una nuova richiesta di ferie | ✓ | ✓ | ✗ |
| Visualizzare le proprie richieste | ✓ | ✓ | ✓ |
| Leggere commenti su una propria richiesta | ✓ | ✓ | ✓ |
| Aggiungere un commento a una propria richiesta | ✓ | ✓ | ✓ |
| Visualizzare le richieste del proprio team | ✗ | ✓ | ✓ |
| Approvare o rifiutare richieste del team | ✗ | ✓ (solo suo gruppo) | ✓ |
| Aggiungere commenti alle richieste del team | ✗ | ✓ | ✓ |
| Approvare in deroga a un vincolo | ✗ | ✓ | ✓ |
| Gestire utenti (crea, modifica, disattiva) | ✗ | ✗ | ✓ |
| Gestire gruppi e assegnare responsabili | ✗ | ✗ | ✓ |
| Configurare periodi di ferie prenotabili | ✗ | ✗ | ✓ |
| Configurare vincoli di presenza | ✗ | ✗ | ✓ |
| Configurare periodi bloccati | ✗ | ✗ | ✓ |
| Visualizzare report di copertura e simulazioni | ✗ | ✗ | ✓ |

---

## 8. Vincoli e assunzioni

1. **Un utente, un gruppo** — ogni dipendente appartiene a esattamente un gruppo di lavoro. L'appartenenza multipla non è prevista in questa versione del sistema.
2. **Il responsabile è un membro del gruppo** — non è una figura esterna; ha gli stessi diritti del dipendente per le proprie ferie, più i permessi aggiuntivi di approvazione sul gruppo.
3. **Nessuna registrazione autonoma** — gli utenti non possono creare un account in autonomia. Ogni accesso presuppone che l'email sia già stata inserita dall'admin. Questo garantisce che solo personale aziendale acceda al sistema.
4. **Gestione credenziali delegata a Google** — il sistema non memorizza né gestisce password. Il reset delle credenziali avviene tramite il flusso standard Google Workspace. Il campo `google_id` nella tabella `Utenti` viene valorizzato al primo login.
5. **Richiesta con conflitto non bloccata** — una richiesta che viola un vincolo di copertura non viene automaticamente rifiutata. Viene marcata come "in conflitto" e la decisione finale spetta al responsabile, che può approvare in deroga.
6. **Commenti non modificabili** — una volta inserito, un commento non può essere modificato o cancellato, per garantire l'integrità della traccia di comunicazione.
7. **Dialetto SQL** — lo schema è progettato per **MySQL** (usa `AUTO_INCREMENT`, `ENUM`, `DATEDIFF`, `DATE_ADD`). Le query analitiche di reportistica sono compatibili con MySQL 8+.
