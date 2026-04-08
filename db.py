import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'terranova.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS Ruoli (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        ruolo TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Gruppi (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        nome            TEXT    NOT NULL,
        descrizione     TEXT,
        id_responsabile INTEGER
    );

    CREATE TABLE IF NOT EXISTS Utenti (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        nome      TEXT    NOT NULL,
        cognome   TEXT    NOT NULL,
        email     TEXT    NOT NULL UNIQUE,
        id_gruppo INTEGER NOT NULL REFERENCES Gruppi(id),
        id_ruolo  INTEGER NOT NULL REFERENCES Ruoli(id)
    );

    CREATE TABLE IF NOT EXISTS RichiesteVacanza (
        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo               TEXT    NOT NULL DEFAULT 'ferie',
        data_inizio        TEXT    NOT NULL,
        data_fine          TEXT    NOT NULL,
        stato              TEXT    NOT NULL CHECK(stato IN ('pending','approved','rejected')),
        note_dipendente    TEXT,
        data_creazione     TEXT    NOT NULL,
        data_aggiornamento TEXT    NOT NULL,
        id_utente          INTEGER NOT NULL REFERENCES Utenti(id),
        id_approvatore     INTEGER          REFERENCES Utenti(id)
    );

    CREATE TABLE IF NOT EXISTS VincoliPresenza (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        permanente     INTEGER NOT NULL CHECK(permanente IN (0,1)),
        min_dipendenti INTEGER NOT NULL,
        data_inizio    TEXT,
        data_fine      TEXT,
        id_ruolo       INTEGER REFERENCES Ruoli(id),
        id_gruppo      INTEGER REFERENCES Gruppi(id)
    );

    CREATE TABLE IF NOT EXISTS Commenti (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        testo        TEXT    NOT NULL,
        data         TEXT    NOT NULL,
        id_richiesta INTEGER NOT NULL REFERENCES RichiesteVacanza(id),
        id_utente    INTEGER NOT NULL REFERENCES Utenti(id)
    );
    """)
    conn.commit()
    conn.close()
