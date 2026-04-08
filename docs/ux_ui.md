# Design UX/UI — Terranova
## Sistema di Gestione del Calendario Ferie Aziendale

---

## c) Sistema di stati visivi

Il sistema comunica lo stato di giorni e richieste esclusivamente attraverso colore e tipografia, senza icone ambigue o testo ridondante. Ogni stato ha un colore semantico coerente con il design system dell'interfaccia.

### Calendario — stati dei giorni

Il calendario mensile distingue sette condizioni visive, applicabili in combinazione:

| Stato | Classe CSS | Aspetto visivo | Significato |
|---|---|---|---|
| **Giorno libero** | `.cal-day` | Sfondo bianco, bordo sottile | Nessuna prenotazione, disponibile |
| **Oggi** | `.cal-day--today` | Bordo interno blu primario, numero in grassetto | Giorno corrente |
| **Occupato (mio)** | `.cal-day--booked` | Sfondo verde `rgba(46, 204, 113, 0.12)` | Ho ferie approvate in questo giorno |
| **Weekend** | `.cal-day--weekend` | Opacità ridotta al 50% | Sabato e domenica, non prenotabili |
| **Bloccato (fuori finestra)** | `.cal-day--blocked` | Sfondo grigio, numero barrato, cursore `not-allowed` | Fuori dai periodi di prenotazione aperti |
| **Non prenotabile (aziendale)** | `.cal-day--nonbookable` | Sfondo rosso `rgba(231, 76, 60, 0.15)`, bordo rosso, numero rosso, cursore `not-allowed` | Periodo bloccato dall'azienda (es. chiusura pre-natalizia) |
| **Clickable** | `.cal-day--clickable` | Hover viola, bordo accent | Giorno disponibile alla prenotazione |

Le prenotazioni dei colleghi appaiono come piccoli dot colorati all'interno della cella, uno per persona, con il colore assegnato all'utente dalla palette dell'applicazione. In questo modo in un solo colpo d'occhio si percepisce quante persone sono assenti nello stesso giorno.

La distinzione tra "bloccato" (fuori dalla finestra di prenotazione) e "non prenotabile" (periodo bloccato per motivo aziendale specifico) è intenzionale: il rosso del periodo aziendale comunica un vincolo attivo e motivato, diverso dalla semplice indisponibilità stagionale.

---

### Richieste — stati delle richieste

Lo stato di ogni richiesta è comunicato tramite **badge colorati** a pill (bordo arrotondato), usati sia nelle tabelle che nelle card e nel dettaglio richiesta:

| Stato | Classe CSS badge | Colore testo | Sfondo | Etichetta |
|---|---|---|---|---|
| **In attesa** | `.badge--warning` | Arancione `#c87f0a` | `rgba(243, 156, 18, 0.12)` | "In attesa" |
| **Approvata** | `.badge--success` | Verde `#1a8a4a` | `rgba(46, 204, 113, 0.12)` | "Approvata" |
| **Rifiutata** | `.badge--danger` | Rosso `#c0392b` | `rgba(231, 76, 60, 0.12)` | "Rifiutata" |
| **Info / neutro** | `.badge--info` | Blu `#2471a3` | `rgba(52, 152, 219, 0.12)` | Usato per tipo richiesta (es. "Permesso") |

I colori dei badge sono volutamente tenui (bassa opacità dello sfondo, colore testo scuro) per non appesantire visivamente le tabelle con molte richieste. La leggibilità rimane alta anche in densità elevata.

Nel pannello di dettaglio richiesta, lo stato è accompagnato da una **timeline di approvazione** che mostra la sequenza degli eventi (creazione → commenti → approvazione/rifiuto) in ordine cronologico, rendendo tracciabile l'intero ciclo di vita della richiesta.

---

### Filtri del calendario — feedback visivo attivo

I filtri del calendario (Le mie ferie / Colleghi / Tutto il gruppo / Periodi bloccati) sono **toggle button** che cambiano colore in base al filtro attivo, mantenendo la coerenza semantica con il calendario:

| Filtro | Colore attivo |
|---|---|
| Le mie ferie | Verde `#2ecc71` |
| Colleghi | Blu `#2980b9` |
| Tutto il gruppo | Viola `#8e44ad` |
| Periodi bloccati | Rosso `#e74c3c` |

Quando inattivi, i toggle sono grigi e discreti. Quando attivi, il colore del bottone corrisponde esattamente al colore degli elementi che mostrano nel calendario, creando una legenda implicita senza bisogno di testo aggiuntivo.

---

## d) Scelte di design motivate

### SPA invece di pagine separate

L'interfaccia è una **Single Page Application**: tutte le schermate esistono nel DOM sin dal caricamento, e la navigazione avviene toggling della classe `screen--active` via JavaScript. Non ci sono redirect o ricaricamenti di pagina.

**Motivazione:** un gestionale aziendale viene usato in sessioni continue, non come sito da sfogliare. L'utente tipico apre la dashboard, controlla il calendario, apre una richiesta, aggiunge un commento — tutto in sequenza rapida. I ricaricamenti di pagina aggiungerebbero latenza percepita senza nessun vantaggio. La SPA mantiene anche lo stato locale in memoria (es. il mese del calendario visualizzato) senza doverlo serializzare nell'URL.

---

### Navbar sempre visibile

La barra di navigazione superiore è fissa e sempre presente in tutte le schermate autenticate.

**Motivazione:** in un'applicazione con otto schermate distinte, nascondere la navbar richiederebbe all'utente di ricordare dove si trova e come tornare indietro. La navbar fissa dà sempre un punto di riferimento visivo e permette di cambiare contesto in un solo click. Il nome dell'utente e l'avatar nell'angolo destro fungono da conferma costante dell'identità autenticata, particolarmente utile in un sistema multi-ruolo dove la stessa persona può essere dipendente e responsabile.

---

### Filtri toggle invece di dropdown

I filtri del calendario sono bottoni toggle multipli attivabili simultaneamente, non un menu a tendina a selezione singola.

**Motivazione:** la sovrapposizione di informazioni è il valore principale del calendario condiviso. Un dropdown permetterebbe di vedere solo una categoria alla volta, annullando la possibilità di confrontare visivamente le proprie ferie con quelle dei colleghi. I toggle multipli permettono combinazioni arbitrarie (es. "mostrami le mie ferie E i periodi bloccati" ma non i colleghi) senza vincoli. La forma a pill con colori semantici li rende leggibili come una legenda interattiva del calendario.

---

### Interfaccia role-aware senza pagine separate per ruolo

L'interfaccia non ha URL o layout diversi per dipendenti, responsabili e CEO. Le sezioni aggiuntive (tab "Il mio team", pannello admin) appaiono o scompaiono dinamicamente in base al ruolo dell'utente autenticato.

**Motivazione:** il responsabile è a tutti gli effetti anche un dipendente — usa le stesse funzionalità di base più quelle aggiuntive. Creare un'interfaccia separata per ogni ruolo avrebbe duplicato la logica e reso più fragile la manutenzione. La soluzione adottata — mostrare/nascondere elementi via JS in base a `is_manager` e `is_ceo` — concentra tutta la logica di presentazione in un unico posto e riduce la superficie di errori.

---

### Glassmorphism come linguaggio visivo

L'interfaccia adotta un design system basato su **glassmorphism**: superfici traslucide con backdrop blur, sfondi sfumati animati, bordi semi-trasparenti.

**Motivazione:** un gestionale di ferie non ha bisogno di essere neutro e corporate. Un linguaggio visivo moderno e riconoscibile aumenta la percezione di qualità del prodotto e rende l'esperienza quotidiana meno simile a un software gestionale tradizionale. Le superfici vetrose permettono di mantenere una gerarchia visiva chiara (card in primo piano, sfondo in secondo) senza ricorrere a ombre pesanti o bordi netti.
