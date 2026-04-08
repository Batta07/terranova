import datetime
from db import get_db


def seed_if_empty():
    conn = get_db()
    cur = conn.cursor()
    if cur.execute('SELECT COUNT(*) FROM Ruoli').fetchone()[0] > 0:
        conn.close()
        return

    today = datetime.date.today().isoformat()

    cur.executemany('INSERT INTO Ruoli (ruolo) VALUES (?)', [
        ('Developer',), ('Designer',), ('Project Manager',), ('HR Manager',), ('CEO',),
    ])

    cur.executemany('INSERT INTO Gruppi (nome, descrizione, id_responsabile) VALUES (?,?,NULL)', [
        ('Frontend', 'Team sviluppo interfacce utente'),
        ('Backend',  'Team sviluppo server e database'),
        ('Design',   'Team UX/UI design'),
        ('HR',       'Gestione risorse umane'),
    ])

    cur.executemany(
        'INSERT INTO Utenti (nome, cognome, email, id_gruppo, id_ruolo) VALUES (?,?,?,?,?)', [
            ('Marco',   'Rossi',    'marco.rossi@azienda.it',      1, 1),
            ('Giulia',  'Bianchi',  'giulia.bianchi@azienda.it',   1, 2),
            ('Luca',    'Verdi',    'luca.verdi@azienda.it',       2, 1),
            ('Sara',    'Neri',     'sara.neri@azienda.it',        2, 3),
            ('Anna',    'Ferrari',  'anna.ferrari@azienda.it',     3, 2),
            ('Paolo',   'Ricci',    'paolo.ricci@azienda.it',      4, 4),
            ('Chiara',  'Conti',    'chiara.conti@azienda.it',     3, 3),
            ('Giorgio', 'Esposito', 'giorgio.esposito@azienda.it', 2, 5),
        ]
    )

    # Set group managers
    cur.execute('UPDATE Gruppi SET id_responsabile = 1 WHERE id = 1')  # Marco → Frontend
    cur.execute('UPDATE Gruppi SET id_responsabile = 4 WHERE id = 2')  # Sara  → Backend
    cur.execute('UPDATE Gruppi SET id_responsabile = 7 WHERE id = 3')  # Chiara→ Design
    cur.execute('UPDATE Gruppi SET id_responsabile = 6 WHERE id = 4')  # Paolo → HR

    cur.executemany(
        'INSERT INTO RichiesteVacanza '
        '(tipo, data_inizio, data_fine, stato, note_dipendente, data_creazione, data_aggiornamento, id_utente, id_approvatore) '
        'VALUES (?,?,?,?,?,?,?,?,?)', [
            ('ferie',    '2026-04-14', '2026-04-18', 'pending',  'Pasqua in famiglia',   today, today, 1, None),
            ('ferie',    '2026-05-01', '2026-05-10', 'approved', 'Vacanza primaverile',  today, today, 2, 6),
            ('ferie',    '2026-06-15', '2026-06-20', 'rejected', 'Viaggio',              today, today, 3, 6),
            ('ferie',    '2026-07-01', '2026-07-15', 'pending',  'Ferie estive',         today, today, 4, None),
            ('ferie',    '2026-08-10', '2026-08-20', 'approved', 'Agosto al mare',       today, today, 5, 6),
            ('permesso', '2026-09-01', '2026-09-05', 'pending',  None,                   today, today, 7, None),
        ]
    )

    cur.executemany(
        'INSERT INTO VincoliPresenza (permanente, min_dipendenti, data_inizio, data_fine, id_ruolo, id_gruppo) VALUES (?,?,?,?,?,?)', [
            (1, 2, None,         None,         1, 1),
            (1, 1, None,         None,         3, 2),
            (0, 1, '2026-07-01', '2026-08-31', 1, 2),
            (0, 1, '2026-12-20', '2026-12-31', 2, 3),
        ]
    )

    cur.executemany(
        'INSERT INTO Commenti (testo, data, id_richiesta, id_utente) VALUES (?,?,?,?)', [
            ('Richiesta ricevuta, in fase di valutazione', today, 1, 6),
            ('Approvata, buone vacanze!',                  today, 2, 6),
            ('Periodo non disponibile per troppi assenti', today, 3, 6),
            ('Verificherò la disponibilità del team',      today, 4, 4),
        ]
    )

    conn.commit()
    conn.close()
