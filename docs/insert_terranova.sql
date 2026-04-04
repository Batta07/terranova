-- ══════════════════════════════════════════════════════════════
--  SISTEMA GESTIONE FERIE – Query di Inserimento
--  Terranova
-- ══════════════════════════════════════════════════════════════


-- 1. RUOLI
INSERT INTO Ruoli (ruolo) VALUES
    ('Developer'),
    ('Designer'),
    ('Project Manager'),
    ('HR Manager'),
    ('CEO');


-- 2. GRUPPI (senza id_responsabile, aggiornato dopo)
INSERT INTO Gruppi (nome, descrizione, id_responsabile) VALUES
    ('Frontend', 'Team sviluppo interfacce utente', NULL),
    ('Backend',  'Team sviluppo server e database',  NULL),
    ('Design',   'Team UX/UI design',                NULL),
    ('HR',       'Gestione risorse umane',            NULL);


-- 3. UTENTI
INSERT INTO Utenti (nome, cognome, email, id_gruppo, id_ruolo) VALUES
    ('Marco',   'Rossi',    'marco.rossi@azienda.it',    1, 1),
    ('Giulia',  'Bianchi',  'giulia.bianchi@azienda.it', 1, 2),
    ('Luca',    'Verdi',    'luca.verdi@azienda.it',     2, 1),
    ('Sara',    'Neri',     'sara.neri@azienda.it',      2, 3),
    ('Anna',    'Ferrari',  'anna.ferrari@azienda.it',   3, 2),
    ('Paolo',   'Ricci',    'paolo.ricci@azienda.it',    4, 4),
    ('Chiara',  'Conti',    'chiara.conti@azienda.it',   3, 3),
    ('Giorgio', 'Esposito', 'giorgio.esposito@azienda.it', 2, 5);

-- Aggiornamento responsabili dei gruppi
UPDATE Gruppi SET id_responsabile = 1 WHERE id = 1;
UPDATE Gruppi SET id_responsabile = 4 WHERE id = 2;
UPDATE Gruppi SET id_responsabile = 7 WHERE id = 3;
UPDATE Gruppi SET id_responsabile = 6 WHERE id = 4;


-- 4. RICHIESTE_VACANZA
INSERT INTO RichiesteVacanza (data_inizio, data_fine, stato, note_dipendente, data_creazione, data_aggiornamento, id_utente, id_approvatore) VALUES
    ('2026-04-14', '2026-04-18', 'pending',  'Pasqua in famiglia',  CURRENT_DATE, CURRENT_DATE, 1, NULL),
    ('2026-05-01', '2026-05-10', 'approved', 'Vacanza primaverile', CURRENT_DATE, CURRENT_DATE, 2, 6),
    ('2026-06-15', '2026-06-20', 'rejected', 'Viaggio',             CURRENT_DATE, CURRENT_DATE, 3, 6),
    ('2026-07-01', '2026-07-15', 'pending',  'Ferie estive',        CURRENT_DATE, CURRENT_DATE, 4, NULL),
    ('2026-08-10', '2026-08-20', 'approved', 'Agosto al mare',      CURRENT_DATE, CURRENT_DATE, 5, 6),
    ('2026-09-01', '2026-09-05', 'pending',  NULL,                  CURRENT_DATE, CURRENT_DATE, 7, NULL);


-- 5. VINCOLI_PRESENZA
INSERT INTO VincoliPresenza (permanente, min_dipendenti, data_inizio, data_fine, id_ruolo, id_gruppo) VALUES
    (TRUE,  2, NULL,         NULL,         1, 1),
    (TRUE,  1, NULL,         NULL,         3, 2),
    (FALSE, 1, '2026-07-01', '2026-08-31', 1, 2),
    (FALSE, 1, '2026-12-20', '2026-12-31', 2, 3);


-- 6. COMMENTI
INSERT INTO Commenti (testo, data, id_richiesta, id_utente) VALUES
    ('Richiesta ricevuta, in fase di valutazione', CURRENT_DATE, 1, 6),
    ('Approvata, buone vacanze!',                  CURRENT_DATE, 2, 6),
    ('Periodo non disponibile per troppi assenti', CURRENT_DATE, 3, 6),
    ('Verificherò la disponibilità del team',      CURRENT_DATE, 4, 4);
