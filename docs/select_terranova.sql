-- ══════════════════════════════════════════════════════════════
--  SISTEMA GESTIONE FERIE – Query di Select
--  Terranova
-- ══════════════════════════════════════════════════════════════


-- ──────────────────────────────────────────────────────────────
-- 1. ACCESSO (LOGIN con Google)
--    Recupera l'utente tramite email per verificare che sia
--    autorizzato (email precaricata dall'azienda nel DB)
-- ──────────────────────────────────────────────────────────────
SELECT id, nome, cognome, email, id_ruolo
FROM Utenti
WHERE email = 'marco.rossi@azienda.it';


-- ──────────────────────────────────────────────────────────────
-- 2. PROFILO UTENTE LOGGATO
--    Mostra i dati completi dell'utente con gruppo e ruolo
-- ──────────────────────────────────────────────────────────────
SELECT
    u.id,
    u.nome,
    u.cognome,
    u.email,
    r.ruolo,
    g.nome AS gruppo
FROM Utenti u
JOIN Gruppi g ON u.id_gruppo = g.id
JOIN Ruoli  r ON u.id_ruolo  = r.id
WHERE u.id = 1;


-- ──────────────────────────────────────────────────────────────
-- 3. LE MIE RICHIESTE DI FERIE
--    Tutte le richieste di un dipendente
-- ──────────────────────────────────────────────────────────────
SELECT
    id,
    data_inizio,
    data_fine,
    stato,
    note_dipendente,
    data_creazione
FROM RichiesteVacanza
WHERE id_utente = 1
ORDER BY data_creazione DESC;


-- ──────────────────────────────────────────────────────────────
-- 4. RICHIESTE IN ATTESA DEL MIO TEAM
--    Per il responsabile: vede le richieste pending del suo gruppo
-- ──────────────────────────────────────────────────────────────
SELECT
    rv.id,
    u.nome,
    u.cognome,
    rv.data_inizio,
    rv.data_fine,
    rv.stato,
    rv.note_dipendente
FROM RichiesteVacanza rv
JOIN Utenti u ON rv.id_utente = u.id
WHERE u.id_gruppo = 1
  AND rv.stato = 'pending'
ORDER BY rv.data_inizio ASC;


-- ──────────────────────────────────────────────────────────────
-- 5. COMMENTI DI UNA RICHIESTA
--    Mostra la conversazione su una specifica richiesta
-- ──────────────────────────────────────────────────────────────
SELECT
    c.id,
    u.nome,
    u.cognome,
    c.testo,
    c.data
FROM Commenti c
JOIN Utenti u ON c.id_utente = u.id
WHERE c.id_richiesta = 3
ORDER BY c.data ASC;


-- ──────────────────────────────────────────────────────────────
-- 6. TUTTE LE RICHIESTE (per admin)
--    Pannello admin: tutte le richieste con utente e approvatore
-- ──────────────────────────────────────────────────────────────
SELECT
    rv.id,
    u.nome        AS dipendente_nome,
    u.cognome     AS dipendente_cognome,
    rv.data_inizio,
    rv.data_fine,
    rv.stato,
    a.nome        AS approvatore_nome,
    a.cognome     AS approvatore_cognome
FROM RichiesteVacanza rv
JOIN Utenti          u  ON rv.id_utente      = u.id
LEFT JOIN Utenti     a  ON rv.id_approvatore = a.id
ORDER BY rv.data_creazione DESC;


-- ══════════════════════════════════════════════════════════════
--  QUERY AGGIUNTIVE – Analisi e reportistica
-- ══════════════════════════════════════════════════════════════


-- ──────────────────────────────────────────────────────────────
-- 7. RIEPILOGO FERIE PER UTENTE (Dashboard – card "Ferie residue")
--    Conta le richieste approvate per ogni dipendente
--    e mostra solo chi ha già usato più di 5 giorni approvati.
-- ──────────────────────────────────────────────────────────────
SELECT
    u.id,
    u.nome,
    u.cognome,
    COUNT(rv.id)                              AS totale_richieste_approvate,
    SUM(DATEDIFF(rv.data_fine, rv.data_inizio) + 1) AS giorni_approvati
FROM Utenti u
JOIN RichiesteVacanza rv ON rv.id_utente = u.id
WHERE rv.stato = 'approved'
GROUP BY u.id, u.nome, u.cognome
HAVING SUM(DATEDIFF(rv.data_fine, rv.data_inizio) + 1) > 5
ORDER BY giorni_approvati DESC;


-- ──────────────────────────────────────────────────────────────
-- 8. RICHIESTE IN ATTESA CON COMMENTI (Attività recente)
--    Richieste ancora pending che hanno almeno un commento —
--    alimenta il feed "Attività recente" nella Dashboard.
-- ──────────────────────────────────────────────────────────────
SELECT
    rv.id                                  AS richiesta_id,
    CONCAT(u.nome, ' ', u.cognome)         AS dipendente,
    rv.data_inizio,
    rv.data_fine,
    rv.stato,
    COUNT(c.id)                            AS num_commenti,
    MAX(c.data)                            AS ultimo_commento
FROM RichiesteVacanza rv
JOIN Utenti   u ON rv.id_utente    = u.id
JOIN Commenti c ON c.id_richiesta  = rv.id
WHERE rv.stato = 'pending'
GROUP BY rv.id, u.nome, u.cognome, rv.data_inizio, rv.data_fine, rv.stato
ORDER BY ultimo_commento DESC;


-- ──────────────────────────────────────────────────────────────
-- 9. QUANTE PERSONE SONO ASSENTI PER OGNI GIORNO DEL MESE
--    (Calendario – logica di occupazione per slot)
--    Conta le richieste approvate che coprono ciascuna data
--    di aprile 2026, utile per colorare le celle del calendario.
-- ──────────────────────────────────────────────────────────────
SELECT
    g.giorno,
    COUNT(rv.id) AS persone_assenti
FROM (
    SELECT DATE_ADD('2026-04-01', INTERVAL seq DAY) AS giorno
    FROM (
        SELECT 0 AS seq UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
        UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9
        UNION SELECT 10 UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14
        UNION SELECT 15 UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19
        UNION SELECT 20 UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24
        UNION SELECT 25 UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29
    ) seq_table
    WHERE DATE_ADD('2026-04-01', INTERVAL seq DAY) <= '2026-04-30'
) g
LEFT JOIN RichiesteVacanza rv
       ON rv.stato       = 'approved'
      AND g.giorno BETWEEN rv.data_inizio AND rv.data_fine
GROUP BY g.giorno
ORDER BY g.giorno;


-- ──────────────────────────────────────────────────────────────
-- 10. DIPENDENTI SENZA RICHIESTE IN CORSO (Team – chi è disponibile)
--     Membri del gruppo Frontend che NON hanno richieste attive oggi.
-- ──────────────────────────────────────────────────────────────
SELECT u.id, u.nome, u.cognome
FROM Utenti u
JOIN Gruppi g ON u.id_gruppo = g.id
WHERE g.nome = 'Frontend'
  AND u.id NOT IN (
      SELECT rv.id_utente
      FROM RichiesteVacanza rv
      WHERE rv.stato IN ('approved', 'pending')
        AND CURRENT_DATE BETWEEN rv.data_inizio AND rv.data_fine
  );


-- ──────────────────────────────────────────────────────────────
-- 11. CLASSIFICA GRUPPI PER RICHIESTE RIFIUTATE (Admin – pannello gruppi)
--     Mostra i gruppi con più richieste rifiutate.
-- ──────────────────────────────────────────────────────────────
SELECT
    g.nome                AS gruppo,
    COUNT(rv.id)          AS richieste_rifiutate
FROM RichiesteVacanza rv
JOIN Utenti u ON rv.id_utente = u.id
JOIN Gruppi g ON u.id_gruppo  = g.id
WHERE rv.stato = 'rejected'
GROUP BY g.nome
ORDER BY richieste_rifiutate DESC;


-- ──────────────────────────────────────────────────────────────
-- 12. APPROVATORI PIÙ ATTIVI (Admin – pannello approvatori)
--     Quante richieste ha gestito ogni approvatore.
--     Solo approvatori che hanno gestito almeno 3 richieste.
-- ──────────────────────────────────────────────────────────────
SELECT
    CONCAT(a.nome, ' ', a.cognome)                                      AS approvatore,
    COUNT(rv.id)                                                         AS totale_gestite,
    SUM(CASE WHEN rv.stato = 'approved' THEN 1 ELSE 0 END)              AS approvate,
    SUM(CASE WHEN rv.stato = 'rejected' THEN 1 ELSE 0 END)              AS rifiutate
FROM RichiesteVacanza rv
JOIN Utenti a ON rv.id_approvatore = a.id
GROUP BY a.id, a.nome, a.cognome
HAVING COUNT(rv.id) >= 3
ORDER BY totale_gestite DESC;


-- ══════════════════════════════════════════════════════════════
--  QUERY PANNELLO ADMIN
-- ══════════════════════════════════════════════════════════════


-- ──────────────────────────────────────────────────────────────
-- 13. TAB "UTENTI E GRUPPI" – Lista utenti con ruolo e gruppo
-- ──────────────────────────────────────────────────────────────
SELECT
    u.id,
    CONCAT(u.nome, ' ', u.cognome)              AS utente,
    u.email,
    r.ruolo,
    g.nome                                       AS gruppo,
    CONCAT(resp.nome, ' ', resp.cognome)         AS responsabile_gruppo
FROM Utenti u
JOIN Ruoli  r    ON u.id_ruolo   = r.id
JOIN Gruppi g    ON u.id_gruppo  = g.id
LEFT JOIN Utenti resp ON g.id_responsabile = resp.id
ORDER BY g.nome, r.ruolo, u.cognome;


-- ──────────────────────────────────────────────────────────────
-- 14. TAB "UTENTI E GRUPPI" – Tabella gruppi con conteggio membri
-- ──────────────────────────────────────────────────────────────
SELECT
    g.id,
    g.nome                                       AS gruppo,
    g.descrizione,
    CONCAT(resp.nome, ' ', resp.cognome)         AS manager,
    COUNT(u.id)                                  AS num_membri
FROM Gruppi g
LEFT JOIN Utenti resp ON g.id_responsabile = resp.id
LEFT JOIN Utenti u    ON u.id_gruppo       = g.id
GROUP BY g.id, g.nome, g.descrizione, resp.nome, resp.cognome
ORDER BY g.nome;


-- ──────────────────────────────────────────────────────────────
-- 15. TAB "REGOLE E VINCOLI" – Vincoli attivi
--     Mostra i vincoli di presenza con ruolo e gruppo associati.
-- ──────────────────────────────────────────────────────────────
SELECT
    vp.id,
    vp.permanente,
    vp.min_dipendenti,
    vp.data_inizio,
    vp.data_fine,
    r.ruolo,
    g.nome AS gruppo
FROM VincoliPresenza vp
LEFT JOIN Ruoli  r ON vp.id_ruolo  = r.id
LEFT JOIN Gruppi g ON vp.id_gruppo = g.id
ORDER BY vp.permanente DESC, vp.data_inizio;


-- ──────────────────────────────────────────────────────────────
-- 16. TAB "SIMULAZIONE" – Richieste in conflitto (sovrapposizioni)
--     Trova coppie di richieste approved/pending dello stesso gruppo
--     che si sovrappongono nel tempo.
-- ──────────────────────────────────────────────────────────────
SELECT
    r1.id                                          AS richiesta_a,
    CONCAT(u1.nome, ' ', u1.cognome)               AS dipendente_a,
    r2.id                                          AS richiesta_b,
    CONCAT(u2.nome, ' ', u2.cognome)               AS dipendente_b,
    g.nome                                         AS gruppo,
    GREATEST(r1.data_inizio, r2.data_inizio)        AS overlap_inizio,
    LEAST(r1.data_fine,      r2.data_fine)          AS overlap_fine
FROM RichiesteVacanza r1
JOIN RichiesteVacanza r2  ON r1.id < r2.id
JOIN Utenti           u1  ON r1.id_utente = u1.id
JOIN Utenti           u2  ON r2.id_utente = u2.id
JOIN Gruppi           g   ON u1.id_gruppo = g.id
                          AND u2.id_gruppo = g.id
WHERE r1.stato IN ('approved', 'pending')
  AND r2.stato IN ('approved', 'pending')
  AND r1.data_inizio <= r2.data_fine
  AND r1.data_fine   >= r2.data_inizio
ORDER BY overlap_inizio;


-- ──────────────────────────────────────────────────────────────
-- 17. TAB "SIMULAZIONE" – Copertura media gruppo nei prossimi 30 giorni
-- ──────────────────────────────────────────────────────────────
SELECT
    g.nome                                         AS gruppo,
    COUNT(DISTINCT u.id)                           AS totale_membri,
    COUNT(DISTINCT rv.id_utente)                   AS membri_con_ferie_previste,
    ROUND(
        100.0 * (COUNT(DISTINCT u.id) - COUNT(DISTINCT rv.id_utente))
        / NULLIF(COUNT(DISTINCT u.id), 0)
    , 1)                                           AS copertura_percentuale
FROM Gruppi g
JOIN Utenti u ON u.id_gruppo = g.id
LEFT JOIN RichiesteVacanza rv
       ON rv.id_utente   = u.id
      AND rv.stato        = 'approved'
      AND rv.data_fine   >= CURRENT_DATE
      AND rv.data_inizio <= DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY)
GROUP BY g.id, g.nome
ORDER BY copertura_percentuale ASC;
