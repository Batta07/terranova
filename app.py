import os
import datetime
import calendar as cal_module
from flask import Flask, session, request, jsonify, send_from_directory
from flasgger import Swagger
from db import get_db, init_db
from seed import seed_if_empty

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'terranova-dev-secret-2026')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

swagger_config = {
    'headers': [],
    'specs': [{'endpoint': 'apispec', 'route': '/apispec.json', 'rule_filter': lambda rule: rule.rule.startswith('/api/'), 'model_filter': lambda tag: True}],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'specs_route': '/docs',
}
swagger_template = {
    'info': {'title': 'Terranova API', 'description': 'Gestionale ferie Terranova', 'version': '1.0'},
    'securityDefinitions': {'SessionCookie': {'type': 'apiKey', 'in': 'cookie', 'name': 'session'}},
}
Swagger(app, config=swagger_config, template=swagger_template)

PALETTE = ['#2ECC71', '#8e44ad', '#2980b9', '#e67e22', '#1abc9c', '#e74c3c', '#f39c12', '#16a085']

_bootstrapped = False


@app.before_request
def bootstrap():
    global _bootstrapped
    if not _bootstrapped:
        init_db()
        seed_if_empty()
        _bootstrapped = True


# ── Helpers ─────────────────────────────────────────────────────────────────

def _require_session():
    uid = session.get('user_id')
    if not uid:
        return None, (jsonify({'error': 'Unauthorized'}), 401)
    conn = get_db()
    row = conn.execute(
        '''SELECT u.id, u.nome, u.cognome, u.email, u.id_gruppo, u.id_ruolo,
                  r.ruolo, g.nome AS gruppo,
                  CASE WHEN g.id_responsabile = u.id THEN 1 ELSE 0 END AS is_manager
           FROM Utenti u
           JOIN Ruoli r ON r.id = u.id_ruolo
           JOIN Gruppi g ON g.id = u.id_gruppo
           WHERE u.id = ?''', (uid,)
    ).fetchone()
    conn.close()
    if not row:
        session.clear()
        return None, (jsonify({'error': 'Unauthorized'}), 401)
    return row, None


def _user_dict(row):
    return {
        'id': row['id'],
        'nome': row['nome'],
        'cognome': row['cognome'],
        'email': row['email'],
        'ruolo': row['ruolo'],
        'gruppo': row['gruppo'],
        'id_gruppo': row['id_gruppo'],
        'id_ruolo': row['id_ruolo'],
        'is_manager': bool(row['is_manager']),
        'is_ceo': row['ruolo'] == 'CEO',
    }


def _days_between(start_str, end_str):
    start = datetime.date.fromisoformat(start_str)
    end = datetime.date.fromisoformat(end_str)
    return (end - start).days + 1


def _get_blocked_ranges(conn):
    """Return list of (date_start, date_end) for all PeriodiBlocchi."""
    rows = conn.execute('SELECT data_inizio, data_fine FROM PeriodiBlocchi').fetchall()
    return [(datetime.date.fromisoformat(r['data_inizio']), datetime.date.fromisoformat(r['data_fine'])) for r in rows]


def _overlaps_blocked(start_str, end_str, blocked_ranges):
    start = datetime.date.fromisoformat(start_str)
    end = datetime.date.fromisoformat(end_str)
    for bs, be in blocked_ranges:
        if start <= be and end >= bs:
            return True
    return False


def _has_weekend(start_str, end_str):
    start = datetime.date.fromisoformat(start_str)
    end = datetime.date.fromisoformat(end_str)
    d = start
    while d <= end:
        if d.weekday() >= 5:
            return True
        d += datetime.timedelta(days=1)
    return False


def _format_date_it(date_str):
    if not date_str:
        return '--'
    d = datetime.date.fromisoformat(date_str)
    months = ['Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic']
    return f"{d.day} {months[d.month - 1]} {d.year}"


# ── Static / SPA ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def catch_all(path):
    full = os.path.join(app.static_folder, path)
    if os.path.isfile(full):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# ── Auth ─────────────────────────────────────────────────────────────────────

@app.route('/api/auth/users', methods=['GET'])
def auth_users():
    """
    Lista tutti gli utenti (per il login in modalità dev).
    ---
    tags: [Auth]
    responses:
      200:
        description: Lista utenti
    """
    conn = get_db()
    rows = conn.execute('SELECT id, nome, cognome, email FROM Utenti ORDER BY nome, cognome').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """
    Effettua il login selezionando un utente per email.
    ---
    tags: [Auth]
    parameters:
      - in: body
        schema:
          properties:
            email: {type: string, example: 'manuel@terranova.it'}
    responses:
      200:
        description: Login effettuato
      404:
        description: Utente non trovato
    """
    data = request.get_json(force=True)
    email = (data or {}).get('email', '').strip()
    if not email:
        return jsonify({'error': 'email required'}), 400
    conn = get_db()
    row = conn.execute(
        '''SELECT u.id, u.nome, u.cognome, u.email, u.id_gruppo, u.id_ruolo,
                  r.ruolo, g.nome AS gruppo,
                  CASE WHEN g.id_responsabile = u.id THEN 1 ELSE 0 END AS is_manager
           FROM Utenti u
           JOIN Ruoli r ON r.id = u.id_ruolo
           JOIN Gruppi g ON g.id = u.id_gruppo
           WHERE u.email = ?''', (email,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'User not found'}), 404
    session['user_id'] = row['id']
    return jsonify(_user_dict(row))


@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    """
    Termina la sessione corrente.
    ---
    tags: [Auth]
    responses:
      200:
        description: Logout effettuato
    """
    session.clear()
    resp = jsonify({})
    resp.delete_cookie('session')
    return resp


@app.route('/api/auth/me', methods=['GET'])
def auth_me():
    """
    Restituisce il profilo dell'utente autenticato.
    ---
    tags: [Auth]
    responses:
      200:
        description: Utente corrente
      401:
        description: Non autenticato
    """
    user, err = _require_session()
    if err:
        return err
    return jsonify(_user_dict(user))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    """
    Restituisce statistiche e richieste recenti per la dashboard.
    ---
    tags: [Dashboard]
    responses:
      200:
        description: Dati dashboard (richieste in attesa, ferie usate, richieste recenti)
      401:
        description: Non autenticato
    """
    user, err = _require_session()
    if err:
        return err
    uid = user['id']
    today = datetime.date.today().isoformat()
    conn = get_db()

    pending_count = conn.execute(
        "SELECT COUNT(*) FROM RichiesteVacanza WHERE id_utente=? AND stato='pending'", (uid,)
    ).fetchone()[0]

    days_used = conn.execute(
        "SELECT data_inizio, data_fine FROM RichiesteVacanza WHERE id_utente=? AND stato='approved'",
        (uid,)
    ).fetchall()
    days_used = sum(_days_between(r['data_inizio'], r['data_fine']) for r in days_used
                    if r['data_fine'] < today)

    recent = conn.execute(
        '''SELECT id, tipo, data_inizio, data_fine, stato FROM RichiesteVacanza
           WHERE id_utente=? ORDER BY data_creazione DESC LIMIT 4''',
        (uid,)
    ).fetchall()

    conn.close()

    return jsonify({
        'in_approvazione': pending_count,
        'ferie_passate': days_used,
        'recent_requests': [
            {
                'id': r['id'],
                'tipo': r['tipo'],
                'data_inizio': r['data_inizio'],
                'data_fine': r['data_fine'],
                'stato': r['stato'],
                'giorni': _days_between(r['data_inizio'], r['data_fine']),
            }
            for r in recent
        ],
    })


@app.route('/api/calendar/<int:year>/<int:month>', methods=['GET'])
def calendar_data(year, month):
    """
    Restituisce prenotazioni e giorni bloccati per il mese indicato.
    ---
    tags: [Calendario]
    parameters:
      - in: path
        name: year
        type: integer
        example: 2026
      - in: path
        name: month
        type: integer
        example: 4
    responses:
      200:
        description: Dati calendario (persone, prenotazioni, giorni bloccati)
      401:
        description: Non autenticato
    """
    user, err = _require_session()
    if err:
        return err
    uid = user['id']
    id_gruppo = user['id_gruppo']

    month_start = f"{year:04d}-{month:02d}-01"
    last_day = cal_module.monthrange(year, month)[1]
    month_end = f"{year:04d}-{month:02d}-{last_day:02d}"

    conn = get_db()
    rows = conn.execute(
        '''SELECT rv.id_utente, rv.data_inizio, rv.data_fine,
                  u.nome, u.cognome, u.id_gruppo
           FROM RichiesteVacanza rv
           JOIN Utenti u ON u.id = rv.id_utente
           WHERE rv.stato IN ('approved','pending')
             AND rv.data_inizio <= ? AND rv.data_fine >= ?''',
        (month_end, month_start)
    ).fetchall()

    blocked_rows = conn.execute(
        'SELECT data_inizio, data_fine FROM PeriodiBlocchi WHERE data_inizio <= ? AND data_fine >= ?',
        (month_end, month_start)
    ).fetchall()
    conn.close()

    # Compute blocked days for this month
    blocked_days = set()
    for br in blocked_rows:
        bs = datetime.date.fromisoformat(br['data_inizio'])
        be = datetime.date.fromisoformat(br['data_fine'])
        for day_num in range(1, last_day + 1):
            d = datetime.date(year, month, day_num)
            if bs <= d <= be:
                blocked_days.add(day_num)

    people = {}
    bookings = {}

    for row in rows:
        u_id = row['id_utente']
        key = str(u_id)
        if key not in people:
            if u_id == uid:
                filter_val = 'mine'
            elif row['id_gruppo'] == id_gruppo:
                filter_val = 'group'
            else:
                filter_val = 'colleagues'
            people[key] = {
                'name': f"{row['nome'][0]}. {row['cognome']}",
                'color': PALETTE[(u_id - 1) % len(PALETTE)],
                'group': str(row['id_gruppo']),
                'filter': filter_val,
            }
        # Convert ISO date range to day-of-month range (clipped to this month)
        start = datetime.date.fromisoformat(row['data_inizio'])
        end = datetime.date.fromisoformat(row['data_fine'])
        start_day = max(start.day, 1) if start.year == year and start.month == month else 1
        end_day = min(end.day, last_day) if end.year == year and end.month == month else last_day
        bookings.setdefault(key, []).append([start_day, end_day])

    return jsonify({'people': people, 'bookings': bookings, 'blocked_days': sorted(blocked_days)})


@app.route('/api/heatmap/<int:year>/<int:month>', methods=['GET'])
def heatmap(year, month):
    """
    Restituisce la heatmap di presenza del team per settimana.
    ---
    tags: [Calendario]
    parameters:
      - in: path
        name: year
        type: integer
        example: 2026
      - in: path
        name: month
        type: integer
        example: 4
    responses:
      200:
        description: Livelli di presenza per membro del gruppo (high/med/low)
      401:
        description: Non autenticato
    """
    user, err = _require_session()
    if err:
        return err
    id_gruppo = user['id_gruppo']

    last_day = cal_module.monthrange(year, month)[1]
    month_start = f"{year:04d}-{month:02d}-01"
    month_end = f"{year:04d}-{month:02d}-{last_day:02d}"

    # 4 week buckets
    buckets = [(1, 7), (8, 14), (15, 21), (22, last_day)]

    conn = get_db()
    members_rows = conn.execute(
        'SELECT id, nome, cognome FROM Utenti WHERE id_gruppo=? ORDER BY id', (id_gruppo,)
    ).fetchall()

    bookings_rows = conn.execute(
        '''SELECT rv.id_utente, rv.data_inizio, rv.data_fine
           FROM RichiesteVacanza rv
           WHERE rv.id_utente IN (SELECT id FROM Utenti WHERE id_gruppo=?)
             AND rv.stato IN ('approved','pending')
             AND rv.data_inizio <= ? AND rv.data_fine >= ?''',
        (id_gruppo, month_end, month_start)
    ).fetchall()
    conn.close()

    # Build set of absent days per user
    absent_days = {}
    for brow in bookings_rows:
        u_id = brow['id_utente']
        start = datetime.date.fromisoformat(brow['data_inizio'])
        end = datetime.date.fromisoformat(brow['data_fine'])
        for day_num in range(1, last_day + 1):
            d = datetime.date(year, month, day_num)
            if start <= d <= end and d.weekday() < 5:  # Mon-Fri only
                absent_days.setdefault(u_id, set()).add(day_num)

    def _presence_level(u_id, bucket_start, bucket_end):
        workdays = sum(
            1 for d in range(bucket_start, bucket_end + 1)
            if datetime.date(year, month, d).weekday() < 5
        )
        if workdays == 0:
            return 'high'
        absent = len(absent_days.get(u_id, set()) & set(range(bucket_start, bucket_end + 1)))
        presence = 1 - absent / workdays
        if presence >= 0.8:
            return 'high'
        elif presence >= 0.5:
            return 'med'
        return 'low'

    members_out = []
    for m in members_rows:
        members_out.append({
            'name': f"{m['nome'][0]}. {m['cognome']}",
            'data': [_presence_level(m['id'], bs, be) for bs, be in buckets],
        })

    return jsonify({'members': members_out})


# ── Requests ─────────────────────────────────────────────────────────────────

@app.route('/api/requests', methods=['GET'])
def requests_list():
    """
    Elenca le richieste di ferie dell'utente autenticato.
    ---
    tags: [Richieste]
    responses:
      200:
        description: Lista richieste
      401:
        description: Non autenticato
    """
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    rows = conn.execute(
        '''SELECT id, tipo, data_inizio, data_fine, stato, note_dipendente, data_creazione
           FROM RichiesteVacanza WHERE id_utente=? ORDER BY data_creazione DESC''',
        (user['id'],)
    ).fetchall()
    conn.close()
    return jsonify([
        {
            'id': r['id'],
            'tipo': r['tipo'],
            'data_inizio': r['data_inizio'],
            'data_fine': r['data_fine'],
            'stato': r['stato'],
            'note_dipendente': r['note_dipendente'],
            'data_creazione': r['data_creazione'],
            'giorni': _days_between(r['data_inizio'], r['data_fine']),
        }
        for r in rows
    ])


@app.route('/api/requests/<int:req_id>', methods=['GET'])
def request_detail(req_id):
    """
    Restituisce il dettaglio di una richiesta con commenti e timeline.
    ---
    tags: [Richieste]
    parameters:
      - in: path
        name: req_id
        type: integer
    responses:
      200:
        description: Dettaglio richiesta
      404:
        description: Non trovata
    """
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    row = conn.execute(
        '''SELECT rv.*, u.nome AS u_nome, u.cognome AS u_cognome, u.id_gruppo AS u_gruppo,
                  a.nome AS a_nome, a.cognome AS a_cognome
           FROM RichiesteVacanza rv
           JOIN Utenti u ON u.id = rv.id_utente
           LEFT JOIN Utenti a ON a.id = rv.id_approvatore
           WHERE rv.id = ?''', (req_id,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404

    comments = conn.execute(
        '''SELECT c.id, c.testo, c.data, u.nome, u.cognome
           FROM Commenti c JOIN Utenti u ON u.id = c.id_utente
           WHERE c.id_richiesta = ? ORDER BY c.data, c.id''',
        (req_id,)
    ).fetchall()
    conn.close()

    stato = row['stato']
    timeline = [
        {'label': 'Inviata',             'date': _format_date_it(row['data_creazione']), 'done': True,  'active': False},
        {'label': 'Responsabile',        'date': _format_date_it(row['data_aggiornamento']) if stato != 'pending' else 'In corso', 'done': stato != 'pending', 'active': stato == 'pending'},
        {'label': 'Approvata',           'date': _format_date_it(row['data_aggiornamento']) if stato == 'approved' else '--', 'done': stato == 'approved', 'active': stato == 'rejected'},
    ]

    return jsonify({
        'id': row['id'],
        'tipo': row['tipo'],
        'data_inizio': row['data_inizio'],
        'data_fine': row['data_fine'],
        'stato': row['stato'],
        'note_dipendente': row['note_dipendente'],
        'data_creazione': row['data_creazione'],
        'data_aggiornamento': row['data_aggiornamento'],
        'giorni': _days_between(row['data_inizio'], row['data_fine']),
        'utente': {'id': row['id_utente'], 'nome': row['u_nome'], 'cognome': row['u_cognome']},
        'approvatore': {'nome': row['a_nome'], 'cognome': row['a_cognome']} if row['a_nome'] else None,
        'comments': [
            {'id': c['id'], 'testo': c['testo'], 'data': c['data'],
             'utente': {'nome': c['nome'], 'cognome': c['cognome']}}
            for c in comments
        ],
        'timeline': timeline,
        'is_own': row['id_utente'] == user['id'],
    })


@app.route('/api/requests', methods=['POST'])
def request_create():
    """
    Crea una nuova richiesta di ferie o permesso.
    ---
    tags: [Richieste]
    parameters:
      - in: body
        schema:
          properties:
            type: {type: string, example: 'ferie', enum: [ferie, permesso]}
            start_date: {type: string, example: '2026-07-01'}
            end_date: {type: string, example: '2026-07-05'}
            notes: {type: string, example: 'Vacanza estiva'}
    responses:
      201:
        description: Richiesta creata
      400:
        description: Dati mancanti o vincoli violati
    """
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    tipo = data.get('type', 'ferie')
    start = data.get('start_date', '')
    end = data.get('end_date', '')
    notes = data.get('notes', '')
    if not start or not end:
        return jsonify({'error': 'start_date and end_date required'}), 400
    if _has_weekend(start, end):
        return jsonify({'error': 'Il periodo selezionato include giorni di weekend'}), 400
    conn_check = get_db()
    blocked = _get_blocked_ranges(conn_check)
    conn_check.close()
    if _overlaps_blocked(start, end, blocked):
        return jsonify({'error': 'Il periodo selezionato include giorni non prenotabili'}), 400

    # Validate min/max giorni against VincoliPresenza for this user's group
    giorni_lavorativi = sum(
        1 for i in range((_days_between(start, end)))
        if (datetime.date.fromisoformat(start) + datetime.timedelta(days=i)).weekday() < 5
    )
    conn_rules = get_db()
    vincoli = conn_rules.execute(
        '''SELECT min_giorni, max_giorni FROM VincoliPresenza
           WHERE id_gruppo = ? AND (id_ruolo IS NULL OR id_ruolo = ?)
             AND (permanente = 1
                  OR (data_inizio IS NOT NULL AND data_fine IS NOT NULL
                      AND data_inizio <= ? AND data_fine >= ?))''',
        (user['id_gruppo'], user['id_ruolo'], end, start)
    ).fetchall()
    conn_rules.close()
    for v in vincoli:
        if v['min_giorni'] and giorni_lavorativi < v['min_giorni']:
            return jsonify({'error': f'La richiesta deve essere di almeno {v["min_giorni"]} giorni lavorativi'}), 400
        if v['max_giorni'] and giorni_lavorativi > v['max_giorni']:
            return jsonify({'error': f'La richiesta non può superare {v["max_giorni"]} giorni lavorativi'}), 400

    today = datetime.date.today().isoformat()
    is_ceo = user['ruolo'] == 'CEO'
    stato_iniziale = 'approved' if is_ceo else 'pending'
    approvatore = user['id'] if is_ceo else None
    conn = get_db()
    cur = conn.execute(
        '''INSERT INTO RichiesteVacanza
           (tipo, data_inizio, data_fine, stato, note_dipendente, data_creazione, data_aggiornamento, id_utente, id_approvatore)
           VALUES (?,?,?,?,?,?,?,?,?)''',
        (tipo, start, end, stato_iniziale, notes or None, today, today, user['id'], approvatore)
    )
    new_id = cur.lastrowid
    conn.commit()
    row = conn.execute(
        'SELECT id, tipo, data_inizio, data_fine, stato, note_dipendente, data_creazione FROM RichiesteVacanza WHERE id=?',
        (new_id,)
    ).fetchone()
    conn.close()
    return jsonify({
        'id': row['id'],
        'tipo': row['tipo'],
        'data_inizio': row['data_inizio'],
        'data_fine': row['data_fine'],
        'stato': row['stato'],
        'note_dipendente': row['note_dipendente'],
        'data_creazione': row['data_creazione'],
        'giorni': _days_between(row['data_inizio'], row['data_fine']),
    }), 201


@app.route('/api/requests/<int:req_id>/approve', methods=['POST'])
def request_approve(req_id):
    """
    Approva una richiesta (solo responsabile del gruppo).
    ---
    tags: [Richieste]
    parameters:
      - in: path
        name: req_id
        type: integer
    responses:
      200:
        description: Richiesta approvata
      403:
        description: Non autorizzato
    """
    user, err = _require_session()
    if err:
        return err
    return _change_stato(req_id, 'approved', user)


@app.route('/api/requests/<int:req_id>/reject', methods=['POST'])
def request_reject(req_id):
    """
    Rifiuta una richiesta con motivazione obbligatoria (solo responsabile).
    ---
    tags: [Richieste]
    parameters:
      - in: path
        name: req_id
        type: integer
      - in: body
        schema:
          properties:
            motivation: {type: string, example: 'Copertura insufficiente nel periodo'}
    responses:
      200:
        description: Richiesta rifiutata
      400:
        description: Motivazione mancante
      403:
        description: Non autorizzato
    """
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    if not (data.get('motivation') or '').strip():
        return jsonify({'error': 'motivation required for rejection'}), 400
    return _change_stato(req_id, 'rejected', user)


def _change_stato(req_id, new_stato, user):
    data = request.get_json(force=True) or {}
    motivation = (data.get('motivation') or '').strip()
    today = datetime.date.today().isoformat()
    conn = get_db()
    row = conn.execute(
        'SELECT rv.id_utente, u.id_gruppo FROM RichiesteVacanza rv JOIN Utenti u ON u.id=rv.id_utente WHERE rv.id=?',
        (req_id,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    # Check manager permission
    manager_check = conn.execute(
        'SELECT id_responsabile FROM Gruppi WHERE id=?', (row['id_gruppo'],)
    ).fetchone()
    if not manager_check or manager_check['id_responsabile'] != user['id']:
        conn.close()
        return jsonify({'error': 'Forbidden — not the group manager'}), 403

    conn.execute(
        'UPDATE RichiesteVacanza SET stato=?, id_approvatore=?, data_aggiornamento=? WHERE id=?',
        (new_stato, user['id'], today, req_id)
    )
    if motivation:
        conn.execute(
            'INSERT INTO Commenti (testo, data, id_richiesta, id_utente) VALUES (?,?,?,?)',
            (motivation, today, req_id, user['id'])
        )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'new_stato': new_stato})


@app.route('/api/requests/<int:req_id>/comments', methods=['POST'])
def request_comment(req_id):
    """
    Aggiunge un commento a una richiesta (solo proprietario, manager del gruppo o CEO).
    ---
    tags: [Richieste]
    parameters:
      - in: path
        name: req_id
        type: integer
      - in: body
        schema:
          properties:
            text: {type: string, example: 'Ho verificato la disponibilità'}
    responses:
      201:
        description: Commento aggiunto
      403:
        description: Non autorizzato a commentare
    """
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'text required'}), 400
    today = datetime.date.today().isoformat()
    conn = get_db()
    # Solo il creatore, il manager del suo gruppo o il CEO possono commentare
    req_row = conn.execute(
        '''SELECT rv.id_utente, u.id_gruppo FROM RichiesteVacanza rv
           JOIN Utenti u ON u.id = rv.id_utente WHERE rv.id=?''', (req_id,)
    ).fetchone()
    if req_row:
        is_owner = req_row['id_utente'] == user['id']
        is_ceo = user['ruolo'] == 'CEO'
        manager_row = conn.execute(
            'SELECT id_responsabile FROM Gruppi WHERE id=?', (req_row['id_gruppo'],)
        ).fetchone()
        is_group_manager = manager_row and manager_row['id_responsabile'] == user['id']
        if not (is_owner or is_ceo or is_group_manager):
            conn.close()
            return jsonify({'error': 'Non autorizzato a commentare questa richiesta'}), 403
    cur = conn.execute(
        'INSERT INTO Commenti (testo, data, id_richiesta, id_utente) VALUES (?,?,?,?)',
        (text, today, req_id, user['id'])
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({
        'id': new_id,
        'testo': text,
        'data': today,
        'utente': {'nome': user['nome'], 'cognome': user['cognome']},
    }), 201


# ── Team ─────────────────────────────────────────────────────────────────────

@app.route('/api/team', methods=['GET'])
def team():
    """
    Restituisce i membri e le richieste del gruppo dell'utente.
    ---
    tags: [Team]
    responses:
      200:
        description: Nome gruppo, membri e richieste del team
      401:
        description: Non autenticato
    """
    user, err = _require_session()
    if err:
        return err
    id_gruppo = user['id_gruppo']
    today = datetime.date.today().isoformat()
    conn = get_db()

    group_row = conn.execute('SELECT nome FROM Gruppi WHERE id=?', (id_gruppo,)).fetchone()
    members = conn.execute(
        '''SELECT u.id, u.nome, u.cognome, r.ruolo,
                  CASE WHEN EXISTS (
                      SELECT 1 FROM RichiesteVacanza rv
                      WHERE rv.id_utente=u.id AND rv.stato IN ('approved','pending')
                        AND rv.data_inizio <= ? AND rv.data_fine >= ?
                  ) THEN 1 ELSE 0 END AS has_active_request
           FROM Utenti u JOIN Ruoli r ON r.id=u.id_ruolo
           WHERE u.id_gruppo=? ORDER BY u.nome''',
        (today, today, id_gruppo)
    ).fetchall()

    requests_rows = conn.execute(
        '''SELECT rv.id, rv.tipo, rv.data_inizio, rv.data_fine, rv.stato,
                  u.nome, u.cognome
           FROM RichiesteVacanza rv JOIN Utenti u ON u.id=rv.id_utente
           WHERE u.id_gruppo=? ORDER BY rv.data_inizio DESC''',
        (id_gruppo,)
    ).fetchall()

    # Conflict count per request (computed while conn is still open)
    def _conflicts(req_id, r_start, r_end):
        row = conn.execute(
            '''SELECT COUNT(*) AS cnt FROM RichiesteVacanza rv
               JOIN Utenti u ON u.id=rv.id_utente
               WHERE u.id_gruppo=? AND rv.id != ?
                 AND rv.stato IN ('approved','pending')
                 AND rv.data_inizio <= ? AND rv.data_fine >= ?''',
            (id_gruppo, req_id, r_end, r_start)
        ).fetchone()
        return row['cnt']

    requests_out = [
        {
            'id': r['id'],
            'tipo': r['tipo'],
            'utente_nome': f"{r['nome']} {r['cognome']}",
            'data_inizio': r['data_inizio'],
            'data_fine': r['data_fine'],
            'stato': r['stato'],
            'giorni': _days_between(r['data_inizio'], r['data_fine']),
            'conflitti': _conflicts(r['id'], r['data_inizio'], r['data_fine']),
        }
        for r in requests_rows
    ]

    conn.close()

    return jsonify({
        'group_name': group_row['nome'] if group_row else '',
        'members': [
            {'id': m['id'], 'nome': m['nome'], 'cognome': m['cognome'],
             'ruolo': m['ruolo'], 'has_active_request': bool(m['has_active_request'])}
            for m in members
        ],
        'requests': requests_out,
    })


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.route('/api/admin/users', methods=['GET'])
def admin_users():
    """
    Elenca tutti gli utenti dell'azienda (solo admin/CEO).
    ---
    tags: [Admin]
    responses:
      200:
        description: Lista utenti con gruppo e ruolo
      401:
        description: Non autenticato
    """
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    rows = conn.execute(
        '''SELECT u.id, u.nome, u.cognome, u.email, r.ruolo, g.nome AS gruppo,
                  CASE WHEN g.id_responsabile=u.id THEN 1 ELSE 0 END AS is_manager
           FROM Utenti u
           JOIN Ruoli r ON r.id=u.id_ruolo
           JOIN Gruppi g ON g.id=u.id_gruppo
           ORDER BY g.nome, u.nome'''
    ).fetchall()
    conn.close()
    return jsonify([
        {'id': r['id'], 'nome': r['nome'], 'cognome': r['cognome'],
         'email': r['email'], 'ruolo': r['ruolo'], 'gruppo': r['gruppo'],
         'is_manager': bool(r['is_manager'])}
        for r in rows
    ])


@app.route('/api/admin/users', methods=['POST'])
def admin_users_create():
    """
    Crea un nuovo utente (ruolo CEO non consentito).
    ---
    tags: [Admin]
    parameters:
      - in: body
        schema:
          properties:
            nome: {type: string, example: 'Luca'}
            cognome: {type: string, example: 'Verdi'}
            email: {type: string, example: 'luca@terranova.it'}
            id_ruolo: {type: integer, example: 1}
            id_gruppo: {type: integer, example: 2}
    responses:
      201:
        description: Utente creato
      400:
        description: Campi mancanti o ruolo CEO non consentito
    """
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    nome    = (data.get('nome') or '').strip()
    cognome = (data.get('cognome') or '').strip()
    email   = (data.get('email') or '').strip()
    id_ruolo  = data.get('id_ruolo')
    id_gruppo = data.get('id_gruppo')
    if not nome or not cognome or not email or not id_ruolo or not id_gruppo:
        return jsonify({'error': 'tutti i campi sono obbligatori'}), 400
    conn = get_db()
    ruolo_row = conn.execute('SELECT ruolo FROM Ruoli WHERE id=?', (id_ruolo,)).fetchone()
    if ruolo_row and ruolo_row['ruolo'] == 'CEO':
        conn.close()
        return jsonify({'error': 'Non è possibile creare un altro utente con ruolo CEO'}), 400
    try:
        cur = conn.execute(
            'INSERT INTO Utenti (nome, cognome, email, id_gruppo, id_ruolo) VALUES (?,?,?,?,?)',
            (nome, cognome, email, id_gruppo, id_ruolo)
        )
        conn.commit()
        new_id = cur.lastrowid
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400
    conn.close()
    return jsonify({'id': new_id}), 201


@app.route('/api/admin/groups', methods=['GET'])
def admin_groups():
    """
    Elenca tutti i gruppi con responsabile e numero di membri.
    ---
    tags: [Admin]
    responses:
      200:
        description: Lista gruppi
    """
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    rows = conn.execute(
        '''SELECT g.id, g.nome, g.descrizione,
                  u.nome || ' ' || u.cognome AS manager,
                  COUNT(m.id) AS num_membri
           FROM Gruppi g
           LEFT JOIN Utenti u ON u.id=g.id_responsabile
           LEFT JOIN Utenti m ON m.id_gruppo=g.id
           GROUP BY g.id ORDER BY g.nome'''
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/groups', methods=['POST'])
def admin_groups_create():
    """
    Crea un nuovo gruppo di lavoro.
    ---
    tags: [Admin]
    parameters:
      - in: body
        schema:
          properties:
            nome: {type: string, example: 'DevOps'}
            descrizione: {type: string, example: 'Team infrastruttura'}
    responses:
      201:
        description: Gruppo creato
      400:
        description: Nome obbligatorio
    """
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    nome = (data.get('nome') or '').strip()
    descrizione = (data.get('descrizione') or '').strip() or None
    if not nome:
        return jsonify({'error': 'nome obbligatorio'}), 400
    conn = get_db()
    try:
        cur = conn.execute('INSERT INTO Gruppi (nome, descrizione, id_responsabile) VALUES (?,?,NULL)', (nome, descrizione))
        conn.commit()
        new_id = cur.lastrowid
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400
    conn.close()
    return jsonify({'id': new_id}), 201


@app.route('/api/admin/roles', methods=['GET'])
def admin_roles():
    """
    Elenca tutti i ruoli disponibili.
    ---
    tags: [Admin]
    responses:
      200:
        description: Lista ruoli
    """
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    rows = conn.execute('SELECT id, ruolo FROM Ruoli ORDER BY ruolo').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/rules', methods=['GET'])
def admin_rules_list():
    """
    Elenca tutti i vincoli di presenza configurati.
    ---
    tags: [Admin]
    responses:
      200:
        description: Lista vincoli
    """
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    rows = conn.execute(
        '''SELECT vp.id, vp.permanente, vp.min_dipendenti, vp.min_giorni, vp.max_giorni,
                  vp.data_inizio, vp.data_fine, r.ruolo, g.nome AS gruppo
           FROM VincoliPresenza vp
           LEFT JOIN Ruoli r ON r.id=vp.id_ruolo
           LEFT JOIN Gruppi g ON g.id=vp.id_gruppo
           ORDER BY vp.id'''
    ).fetchall()
    conn.close()
    return jsonify([
        {**dict(r), 'permanente': bool(r['permanente'])}
        for r in rows
    ])


@app.route('/api/admin/rules', methods=['POST'])
def admin_rules_create():
    """
    Crea un nuovo vincolo di presenza.
    ---
    tags: [Admin]
    parameters:
      - in: body
        schema:
          properties:
            permanente: {type: boolean, example: true}
            min_dipendenti: {type: integer, example: 2}
            min_giorni: {type: integer, example: 1}
            max_giorni: {type: integer, example: 10}
            data_inizio: {type: string, example: '2026-07-01'}
            data_fine: {type: string, example: '2026-08-31'}
            id_ruolo: {type: integer, example: 1}
            id_gruppo: {type: integer, example: 2}
    responses:
      201:
        description: Vincolo creato
    """
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    conn = get_db()
    cur = conn.execute(
        '''INSERT INTO VincoliPresenza (permanente, min_dipendenti, min_giorni, max_giorni, data_inizio, data_fine, id_ruolo, id_gruppo)
           VALUES (?,?,?,?,?,?,?,?)''',
        (1 if data.get('permanente') else 0,
         data.get('min_dipendenti', 1),
         data.get('min_giorni') or None,
         data.get('max_giorni') or None,
         data.get('data_inizio') or None,
         data.get('data_fine') or None,
         data.get('id_ruolo') or None,
         data.get('id_gruppo') or None)
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id}), 201


@app.route('/api/admin/rules/<int:rule_id>', methods=['PUT'])
def admin_rules_update(rule_id):
    """
    Aggiorna un vincolo di presenza esistente.
    ---
    tags: [Admin]
    parameters:
      - in: path
        name: rule_id
        type: integer
      - in: body
        schema:
          properties:
            permanente: {type: boolean}
            min_dipendenti: {type: integer}
            min_giorni: {type: integer}
            max_giorni: {type: integer}
            data_inizio: {type: string}
            data_fine: {type: string}
            id_ruolo: {type: integer}
            id_gruppo: {type: integer}
    responses:
      200:
        description: Vincolo aggiornato
      404:
        description: Non trovato
    """
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    conn = get_db()
    row = conn.execute('SELECT id FROM VincoliPresenza WHERE id=?', (rule_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    conn.execute(
        '''UPDATE VincoliPresenza SET permanente=?, min_dipendenti=?, min_giorni=?, max_giorni=?,
                  data_inizio=?, data_fine=?, id_ruolo=?, id_gruppo=?
           WHERE id=?''',
        (1 if data.get('permanente') else 0,
         data.get('min_dipendenti', 1),
         data.get('min_giorni') or None,
         data.get('max_giorni') or None,
         data.get('data_inizio') or None,
         data.get('data_fine') or None,
         data.get('id_ruolo') or None,
         data.get('id_gruppo') or None,
         rule_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/rules/<int:rule_id>', methods=['DELETE'])
def admin_rules_delete(rule_id):
    """
    Elimina un vincolo di presenza.
    ---
    tags: [Admin]
    parameters:
      - in: path
        name: rule_id
        type: integer
    responses:
      200:
        description: Vincolo eliminato
    """
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    conn.execute('DELETE FROM VincoliPresenza WHERE id=?', (rule_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/simulation', methods=['GET'])
def admin_simulation():
    """
    Restituisce simulazione di copertura e conflitti per i prossimi 30 giorni.
    ---
    tags: [Admin]
    responses:
      200:
        description: Tasso approvazione, conflitti, copertura per gruppo
      401:
        description: Non autenticato
    """
    user, err = _require_session()
    if err:
        return err
    today = datetime.date.today().isoformat()
    future = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    conn = get_db()

    # Approval rate (last 90 days)
    ninety_ago = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
    rate_row = conn.execute(
        '''SELECT
             SUM(CASE WHEN stato='approved' THEN 1 ELSE 0 END) AS approved,
             SUM(CASE WHEN stato='rejected' THEN 1 ELSE 0 END) AS rejected
           FROM RichiesteVacanza
           WHERE data_creazione >= ? AND stato IN ('approved','rejected')''',
        (ninety_ago,)
    ).fetchone()
    total_decided = (rate_row['approved'] or 0) + (rate_row['rejected'] or 0)
    tasso = round((rate_row['approved'] or 0) / total_decided * 100) if total_decided else 0

    # Conflicts: overlapping approved/pending requests in same group
    conflict_rows = conn.execute(
        '''SELECT r1.id AS id_a, u1.nome||' '||u1.cognome AS dipendente_a,
                  r2.id AS id_b, u2.nome||' '||u2.cognome AS dipendente_b,
                  g.nome AS gruppo,
                  CASE WHEN r1.data_inizio >= r2.data_inizio THEN r1.data_inizio ELSE r2.data_inizio END AS overlap_inizio,
                  CASE WHEN r1.data_fine <= r2.data_fine THEN r1.data_fine ELSE r2.data_fine END AS overlap_fine
           FROM RichiesteVacanza r1
           JOIN RichiesteVacanza r2 ON r1.id < r2.id
           JOIN Utenti u1 ON u1.id = r1.id_utente
           JOIN Utenti u2 ON u2.id = r2.id_utente
           JOIN Gruppi g ON g.id = u1.id_gruppo
           WHERE u1.id_gruppo = u2.id_gruppo
             AND r1.stato IN ('approved','pending')
             AND r2.stato IN ('approved','pending')
             AND r1.data_inizio <= r2.data_fine
             AND r1.data_fine >= r2.data_inizio'''
    ).fetchall()

    # Coverage per group next 30 days
    groups = conn.execute('SELECT id, nome FROM Gruppi').fetchall()
    coverage = []
    for g in groups:
        total = conn.execute('SELECT COUNT(*) FROM Utenti WHERE id_gruppo=?', (g['id'],)).fetchone()[0]
        if total == 0:
            continue
        absent = conn.execute(
            '''SELECT COUNT(DISTINCT id_utente) FROM RichiesteVacanza
               WHERE stato IN ('approved','pending')
                 AND data_inizio <= ? AND data_fine >= ?
                 AND id_utente IN (SELECT id FROM Utenti WHERE id_gruppo=?)''',
            (future, today, g['id'])
        ).fetchone()[0]
        coverage.append({
            'gruppo': g['nome'],
            'copertura_percentuale': round((total - absent) / total * 100),
        })

    avg_coverage = round(sum(c['copertura_percentuale'] for c in coverage) / len(coverage)) if coverage else 0

    conn.close()
    return jsonify({
        'tasso_approvazione': tasso,
        'richieste_in_conflitto': len(conflict_rows),
        'copertura_media': avg_coverage,
        'copertura_per_gruppo': coverage,
        'conflitti': [
            {'richiesta_a': r['id_a'], 'dipendente_a': r['dipendente_a'],
             'richiesta_b': r['id_b'], 'dipendente_b': r['dipendente_b'],
             'gruppo': r['gruppo'],
             'overlap_inizio': r['overlap_inizio'],
             'overlap_fine': r['overlap_fine']}
            for r in conflict_rows
        ],
    })


# ── Periodi Bloccati ─────────────────────────────────────────────────────────

@app.route('/api/admin/blocked-periods', methods=['GET'])
def blocked_periods_list():
    """
    Elenca tutti i periodi non prenotabili.
    ---
    tags: [Admin]
    responses:
      200:
        description: Lista periodi bloccati
    """
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    rows = conn.execute('SELECT id, data_inizio, data_fine, motivo FROM PeriodiBlocchi ORDER BY data_inizio').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/blocked-periods', methods=['POST'])
def blocked_periods_create():
    """
    Crea un nuovo periodo non prenotabile.
    ---
    tags: [Admin]
    parameters:
      - in: body
        schema:
          properties:
            data_inizio: {type: string, example: '2026-12-21'}
            data_fine: {type: string, example: '2026-12-23'}
            motivo: {type: string, example: 'Chiusura aziendale'}
    responses:
      201:
        description: Creato
    """
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    data_inizio = (data.get('data_inizio') or '').strip()
    data_fine = (data.get('data_fine') or '').strip()
    motivo = (data.get('motivo') or '').strip() or None
    if not data_inizio or not data_fine:
        return jsonify({'error': 'data_inizio e data_fine obbligatorie'}), 400
    conn = get_db()
    cur = conn.execute('INSERT INTO PeriodiBlocchi (data_inizio, data_fine, motivo) VALUES (?,?,?)', (data_inizio, data_fine, motivo))
    conn.commit()
    conn.close()
    return jsonify({'id': cur.lastrowid}), 201


@app.route('/api/admin/blocked-periods/<int:bp_id>', methods=['DELETE'])
def blocked_periods_delete(bp_id):
    """
    Elimina un periodo non prenotabile.
    ---
    tags: [Admin]
    parameters:
      - in: path
        name: bp_id
        type: integer
    responses:
      200:
        description: Eliminato
    """
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    conn.execute('DELETE FROM PeriodiBlocchi WHERE id=?', (bp_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ── Profile ───────────────────────────────────────────────────────────────────

@app.route('/api/user/profile', methods=['GET'])
def profile_get():
    """
    Restituisce il profilo dell'utente autenticato.
    ---
    tags: [Profilo]
    responses:
      200:
        description: Profilo utente
      401:
        description: Non autenticato
    """
    user, err = _require_session()
    if err:
        return err
    return jsonify(_user_dict(user))


@app.route('/api/user/profile', methods=['POST'])
def profile_update():
    """
    Aggiorna nome e cognome dell'utente autenticato.
    ---
    tags: [Profilo]
    parameters:
      - in: body
        schema:
          properties:
            nome: {type: string, example: 'Manuel'}
            cognome: {type: string, example: 'Battaglia'}
    responses:
      200:
        description: Profilo aggiornato
      400:
        description: Campi obbligatori mancanti
    """
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    nome = (data.get('nome') or '').strip()
    cognome = (data.get('cognome') or '').strip()
    if not nome or not cognome:
        return jsonify({'error': 'nome and cognome required'}), 400
    conn = get_db()
    conn.execute('UPDATE Utenti SET nome=?, cognome=? WHERE id=?', (nome, cognome, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    seed_if_empty()
    app.run(debug=True, host='0.0.0.0', port=5001)
