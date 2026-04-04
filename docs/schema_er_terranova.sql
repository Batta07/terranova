-- ══════════════════════════════════════════════════════════════
--  SISTEMA GESTIONE FERIE – DDL
--  Generato dallo Schema ER Figma – Terranova
-- ══════════════════════════════════════════════════════════════


-- DROP (rispettando l'ordine delle FK)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS Commenti;
DROP TABLE IF EXISTS periodi_bloccati;
DROP TABLE IF EXISTS richieste_vacanza;
DROP TABLE IF EXISTS periodi_vacanza;
DROP TABLE IF EXISTS VincoliPresenza;
DROP TABLE IF EXISTS Utenti;
DROP TABLE IF EXISTS Gruppi;
DROP TABLE IF EXISTS Ruoli;
SET FOREIGN_KEY_CHECKS = 1;


-- 1. RUOLI
CREATE TABLE Ruoli (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    ruolo VARCHAR(100) NOT NULL
);


-- 2. GRUPPI
--    id_responsabile aggiunto dopo con ALTER TABLE
--    perché Utenti non esiste ancora in questo momento
CREATE TABLE Gruppi (
    id              INT          AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(255) NOT NULL,
    descrizione     VARCHAR(255),
    id_responsabile INT
);


-- 3. UTENTI
CREATE TABLE Utenti (
    id        INT          AUTO_INCREMENT PRIMARY KEY,
    nome      VARCHAR(40)  NOT NULL,
    cognome   VARCHAR(100) NOT NULL,
    email     VARCHAR(255) NOT NULL UNIQUE,
    id_gruppo INT          NOT NULL,
    id_ruolo  INT          NOT NULL,
    FOREIGN KEY (id_gruppo) REFERENCES Gruppi(id),
    FOREIGN KEY (id_ruolo)  REFERENCES Ruoli(id)
);

-- FK responsabile su Gruppi (aggiunta dopo la creazione di Utenti)
ALTER TABLE Gruppi
    ADD CONSTRAINT fk_gruppi_responsabile
    FOREIGN KEY (id_responsabile) REFERENCES Utenti(id);


-- 4. RICHIESTE_VACANZA
CREATE TABLE RichiesteVacanza (
    id                 INT          AUTO_INCREMENT PRIMARY KEY,
    data_inizio        DATE         NOT NULL,
    data_fine          DATE         NOT NULL,
    stato              ENUM('pending', 'approved', 'rejected') NOT NULL,
    note_dipendente    VARCHAR(255),
    data_creazione     DATE         NOT NULL,
    data_aggiornamento DATE         NOT NULL,
    id_utente          INT          NOT NULL,
    id_approvatore     INT,
    FOREIGN KEY (id_utente)      REFERENCES Utenti(id),
    FOREIGN KEY (id_approvatore) REFERENCES Utenti(id)
);


-- 5. VINCOLI_PRESENZA
CREATE TABLE VincoliPresenza (
    id              INT     AUTO_INCREMENT PRIMARY KEY,
    permanente      BOOLEAN NOT NULL,
    min_dipendenti  INT     NOT NULL,
    data_inizio     DATE,
    data_fine       DATE,
    id_ruolo        INT,
    id_gruppo       INT,
    CONSTRAINT chk_date CHECK (data_fine > data_inizio),
    FOREIGN KEY (id_ruolo)  REFERENCES Ruoli(id),
    FOREIGN KEY (id_gruppo) REFERENCES Gruppi(id)
);


-- 6. COMMENTI
CREATE TABLE Commenti (
    id           INT          AUTO_INCREMENT PRIMARY KEY,
    testo        VARCHAR(255) NOT NULL,
    data         DATE         NOT NULL,
    id_richiesta INT          NOT NULL,
    id_utente    INT          NOT NULL,
    FOREIGN KEY (id_richiesta) REFERENCES RichiesteVacanza(id),
    FOREIGN KEY (id_utente)    REFERENCES Utenti(id)
);
