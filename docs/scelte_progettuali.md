# Scelte progettuali – Terranova

Questo documento risponde alle domande aperte (in verde) presenti nel documento dei requisiti PCTO.

---

## 1. Modalità di login

**Scelta:** login tramite **Google OAuth 2.0 (Sign in with Google)**.

Il dipendente clicca il pulsante "Accedi con Google" e viene reindirizzato alla pagina di autenticazione di Google. Dopo l'autorizzazione, Google restituisce al sistema un token contenente l'email e il profilo dell'utente. Il sistema verifica che l'email sia presente nella tabella `utenti` (pre-caricata dall'admin) — se non lo è, l'accesso viene negato.

Nessuna password viene mai memorizzata nel database di Terranova. La gestione delle credenziali è interamente delegata a Google.

**Flusso:**
1. L'utente clicca "Accedi con Google"
2. Viene reindirizzato alla pagina di consenso Google
3. Google restituisce un token OAuth con email e profilo
4. Il backend verifica che l'email esista in `utenti`
5. Se sì: sessione creata, accesso consentito
6. Se no: errore "Account non autorizzato — contatta l'amministratore"

**Come appare nell'interfaccia:**

Il form di login è diviso in due colonne:
- A sinistra: pulsante "Accedi con Google" (con logo Google), nessun campo email/password
- A destra: branding visivo con logo e payoff

---

## 2. Campi della tabella `utenti` e loro vincoli

| Colonna | Tipo | Vincoli | Note |
|---|---|---|---|
| `id` | INT | PRIMARY KEY | |
| `nome` | VARCHAR(100) | NOT NULL | |
| `cognome` | VARCHAR(100) | NOT NULL | |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Deve corrispondere all'email Google |
| `google_id` | VARCHAR(255) | NOT NULL, UNIQUE | L'ID univoco restituito da Google OAuth |
| `id_gruppo` | INT | NOT NULL, FK → `gruppi.id` | |
| `id_ruolo` | INT | NOT NULL, FK → `ruoli.id` | |

Con Google OAuth non servono più `password_hash`, `reset_token` e `reset_token_expiry` — il reset password è gestito interamente da Google.

Un utente appartiene a **un solo gruppo** (relazione molti-a-uno tramite `id_gruppo`). Il ruolo (`id_ruolo`) determina i permessi: `dipendente`, `responsabile`, `admin`.

---

## 3. Reset password: modalità e tabelle coinvolte

**Scelta:** non applicabile — gestita interamente da Google.

Usando Google OAuth, il reset della password avviene tramite il flusso standard di Google ("Password dimenticata?" nella pagina Google). Terranova non gestisce né memorizza credenziali, quindi non serve nessuna tabella o logica di reset.

**Tabelle coinvolte:** nessuna — il campo `reset_token` e `reset_token_expiry` sono stati rimossi dalla tabella `utenti`.

**Come appare nell'interfaccia:**

Nella schermata di login non è presente il link "Password dimenticata?". Se un dipendente non riesce ad accedere al proprio account Google, deve contattare direttamente l'amministratore Google Workspace aziendale.

---

## 4. Legame tra `gruppi` e `utenti`

**Scelta:** relazione **molti-a-uno diretta tramite FK** nella tabella `utenti`.

Ogni utente ha una colonna `id_gruppo` che punta a `gruppi.id`. Un utente appartiene a un solo gruppo. Un gruppo può avere più utenti.

Il responsabile del gruppo è memorizzato in `gruppi.id_responsabile` (FK verso `utenti.id`), aggiunta con ALTER TABLE dopo la creazione di `utenti` per evitare la dipendenza circolare.

```
utenti.id_gruppo  ──FK──►  gruppi.id
gruppi.id_responsabile  ──FK──►  utenti.id
```

**Perché non una tabella di associazione:** un utente appartiene a un solo gruppo per scelta aziendale (semplicità organizzativa). Se in futuro si volesse permettere l'appartenenza multipla, si aggiungerebbe una tabella ponte `utenti_gruppi`.

---

## 5. Come indicare nell'interfaccia i giorni disponibili, in conflitto o occupati

**Scelta:** sistema di **classi CSS sui giorni del calendario** con colori e badge sovrapposti.

| Stato del giorno | Aspetto visivo |
|---|---|
| Giorno normale | sfondo neutro, numero in grigio |
| Oggi | bordo o sfondo evidenziato (classe `cal-day--today`) |
| Weekend | sfondo leggermente scuro, non selezionabile (classe `cal-day--weekend`) |
| Periodo non prenotabile / bloccato | sfondo tratteggiato o rosso tenue (classe `cal-day--blocked`) |
| Ferie proprie approvate | sfondo verde con dot colorato (classe `cal-day--booked`) |
| Ferie di un collega | badge con iniziali e colore personale sovrapposto alla cella |
| Giorno in conflitto (troppi assenti) | badge arancione o bordo rosso sulla cella |

Nella parte inferiore del calendario è presente una **legenda** con i colori associati a ciascun membro del team.

I filtri sopra il calendario ("Le mie ferie", "Colleghi", "Gruppo", "Non-bookable") permettono di attivare o nascondere le diverse categorie di eventi.

---

## 6. Come il sistema segnala violazioni di regole (lato dipendente — form nuova richiesta)

**Scelta:** **validazione inline nel form** con messaggi di errore sotto i campi e un banner di riepilogo prima del submit.

Quando il dipendente seleziona le date nel form "Nuova richiesta", il sistema verifica in tempo reale:

| Violazione | Segnalazione visiva |
|---|---|
| Periodo non prenotabile | campo data evidenziato in rosso, messaggio "Periodo non disponibile" |
| Durata inferiore al minimo (es. < 5 giorni) | warning giallo sotto il campo con il vincolo violato |
| Durata superiore al massimo | warning giallo con il limite consentito |
| Troppi colleghi già assenti in quelle date | banner arancione sopra il pulsante di invio: "Attenzione: copertura minima non garantita" |
| Giorni bloccati inclusi nell'intervallo | i giorni appaiono in rosso nel calendario mini del form |

Il dipendente può **comunque inviare la richiesta** anche in presenza di warning (non di errori bloccanti). La richiesta viene marcata come "in conflitto" e il responsabile ne viene informato.

---

## 7. Come il sistema evidenzia violazioni di regole (lato admin — pannello regole)

**Scelta:** nel pannello admin, tab "Simulazione", vengono mostrate **card di riepilogo** con i dati aggregati:

- **"Richieste in conflitto"** — numero di sovrapposizioni rilevate nel periodo corrente, con lista delle coppie in conflitto
- **"Tasso approvazione stimato"** — percentuale calcolata sui vincoli attivi e le richieste pendenti
- **"Copertura media team"** — presenza media prevista per i prossimi 30 giorni

Nel tab "Utenti e gruppi", le richieste con conflitti attivi vengono evidenziate con un badge arancione `badge--warning` nella colonna Stato.

Il responsabile, nella schermata di dettaglio richiesta, può vedere un avviso esplicito se la richiesta è in conflitto con le regole configurate, e può scegliere di approvarla comunque inserendo una motivazione nel campo dedicato.
