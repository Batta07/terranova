import datetime
from db import get_db


def seed_if_empty():
    conn = get_db()
    cur = conn.cursor()
    if cur.execute('SELECT COUNT(*) FROM Ruoli').fetchone()[0] > 0:
        conn.close()
        return

    today = datetime.date.today().isoformat()

    # Ruoli
    # id: 1=Developer, 2=Designer, 3=Project Manager, 4=HR Manager, 5=CEO, 6=Marketing Manager
    cur.executemany('INSERT INTO Ruoli (ruolo) VALUES (?)', [
        ('Developer',),          # 1
        ('Designer',),           # 2
        ('Project Manager',),    # 3
        ('HR Manager',),         # 4
        ('CEO',),                # 5
        ('Marketing Manager',),  # 6
    ])

    # Gruppi (id_responsabile settato dopo l'inserimento utenti)
    # id: 1=Frontend, 2=Backend, 3=Design, 4=Marketing, 5=HR
    cur.executemany('INSERT INTO Gruppi (nome, descrizione, id_responsabile) VALUES (?,?,NULL)', [
        ('Frontend',  'Team sviluppo interfacce utente'),   # 1
        ('Backend',   'Team sviluppo server e database'),   # 2
        ('Design',    'Team UX/UI design'),                 # 3
        ('Marketing', 'Team marketing e comunicazione'),    # 4
        ('HR',        'Gestione risorse umane'),            # 5
    ])

    # Utenti
    # id:  1=Marco Rossi
    #      2=Giulia Bianchi
    #      3=Luca Verdi
    #      4=Anna Ferrari
    #      5=Paolo Ricci
    #      6=Giorgio Esposito
    #      7=Alessandro Vistoli  (CEO)
    #      8=Manuel Battaglia    (responsabile Frontend)
    #      9=Alberto Chesini     (responsabile Backend)
    #     10=Shiv Gupta          (responsabile Design)
    #     11=Manuel Ostojic      (responsabile Marketing)
    cur.executemany(
        'INSERT INTO Utenti (nome, cognome, email, id_gruppo, id_ruolo) VALUES (?,?,?,?,?)', [
            ('Marco',      'Rossi',     'marco.rossi@terranova.com',      1, 1),  # Frontend, Developer
            ('Giulia',     'Bianchi',   'giulia.bianchi@terranova.com',   3, 2),  # Design, Designer
            ('Luca',       'Verdi',     'luca.verdi@terranova.com',       2, 1),  # Backend, Developer
            ('Anna',       'Ferrari',   'anna.ferrari@terranova.com',     3, 2),  # Design, Designer
            ('Paolo',      'Ricci',     'paolo.ricci@terranova.com',      5, 4),  # HR, HR Manager
            ('Giorgio',    'Esposito',  'giorgio.esposito@terranova.com', 2, 1),  # Backend, Developer
            ('Alessandro', 'Vistoli',   'alessandro.vistoli@terranova.com', 2, 5), # Backend, CEO
            ('Manuel',     'Battaglia', 'manuel.battaglia@terranova.com', 1, 1),  # Frontend, Developer
            ('Alberto',    'Chesini',   'alberto.chesini@terranova.com',  2, 1),  # Backend, Developer
            ('Shiv',       'Gupta',     'shiv.gupta@terranova.com',       3, 2),  # Design, Designer
            ('Manuel',     'Ostojic',   'manuel.ostojic@terranova.com',   4, 6),  # Marketing, Marketing Manager
        ]
    )

    # Responsabili gruppi
    cur.execute('UPDATE Gruppi SET id_responsabile = 8  WHERE id = 1')  # Manuel Battaglia → Frontend
    cur.execute('UPDATE Gruppi SET id_responsabile = 9  WHERE id = 2')  # Alberto Chesini  → Backend
    cur.execute('UPDATE Gruppi SET id_responsabile = 10 WHERE id = 3')  # Shiv Gupta       → Design
    cur.execute('UPDATE Gruppi SET id_responsabile = 11 WHERE id = 4')  # Manuel Ostojic   → Marketing
    cur.execute('UPDATE Gruppi SET id_responsabile = 5  WHERE id = 5')  # Paolo Ricci      → HR

    cur.executemany(
        'INSERT INTO RichiesteVacanza '
        '(tipo, data_inizio, data_fine, stato, note_dipendente, data_creazione, data_aggiornamento, id_utente, id_approvatore) '
        'VALUES (?,?,?,?,?,?,?,?,?)', [
            # Aprile 2026 (solo giorni lavorativi)
            ('ferie',    '2026-04-14', '2026-04-15', 'approved', 'Pasqua in famiglia',       today, today, 1,  8),   # Marco Rossi - 2 gg
            ('ferie',    '2026-04-08', '2026-04-10', 'approved', 'Long weekend primaverile', today, today, 2,  10),  # Giulia Bianchi
            ('permesso', '2026-04-22', '2026-04-22', 'approved', None,                       today, today, 3,  9),   # Luca Verdi
            ('ferie',    '2026-04-28', '2026-04-28', 'pending',  'Ponte 1 maggio',           today, today, 4,  None),# Anna Ferrari - 1 gg
            ('permesso', '2026-04-09', '2026-04-09', 'pending',  None,                       today, today, 5,  None),# Paolo Ricci
            # Altri mesi (solo giorni lavorativi)
            ('ferie',    '2026-05-04', '2026-05-08', 'approved', 'Vacanza primaverile',      today, today, 2,  10),
            ('ferie',    '2026-06-15', '2026-06-19', 'rejected', 'Viaggio',                  today, today, 3,  9),
            ('ferie',    '2026-07-07', '2026-07-10', 'pending',  'Ferie estive',             today, today, 4,  None),
            ('ferie',    '2026-08-10', '2026-08-14', 'approved', 'Agosto al mare',           today, today, 1,  8),
            ('permesso', '2026-09-01', '2026-09-05', 'pending',  None,                       today, today, 5,  None),
        ]
    )

    cur.executemany(
        'INSERT INTO VincoliPresenza (permanente, min_dipendenti, data_inizio, data_fine, id_ruolo, id_gruppo) VALUES (?,?,?,?,?,?)', [
            (1, 2, None,         None,         1, 1),   # Sempre min 2 Developer in Frontend
            (1, 1, None,         None,         1, 2),   # Sempre min 1 Developer in Backend
            (0, 1, '2026-07-01', '2026-08-31', 1, 2),  # Estate: min 1 Developer in Backend
            (0, 1, '2026-12-20', '2026-12-31', 2, 3),  # Natale: min 1 Designer in Design
        ]
    )

    cur.executemany(
        'INSERT INTO PeriodiBlocchi (data_inizio, data_fine, motivo) VALUES (?,?,?)', [
            ('2026-12-21', '2026-12-23', 'Chiusura aziendale pre-natalizia'),
        ]
    )

    cur.executemany(
        'INSERT INTO Commenti (testo, data, id_richiesta, id_utente) VALUES (?,?,?,?)', [
            ('Richiesta ricevuta, in fase di valutazione', today, 1,  8),
            ('Approvata, buone vacanze!',                  today, 2,  10),
            ('Periodo non disponibile per troppi assenti', today, 3,  9),
            ('Verificherò la disponibilità del team',      today, 4,  11),
        ]
    )

    conn.commit()
    conn.close()
