import os
import datetime
from flask import Flask, session, request, jsonify, send_from_directory
from db import get_db, init_db
from seed import seed_if_empty

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'terranova-dev-secret-2026')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

init_db()
seed_if_empty()


# ── Helpers ──────────────────────────────────────────────────────────────────

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
    conn = get_db()
    rows = conn.execute('SELECT id, nome, cognome, email FROM Utenti ORDER BY nome, cognome').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json(force=True) or {}
    email = (data.get('email') or '').strip()
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
    session.clear()
    return jsonify({})


@app.route('/api/auth/me', methods=['GET'])
def auth_me():
    user, err = _require_session()
    if err:
        return err
    return jsonify(_user_dict(user))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    user, err = _require_session()
    if err:
        return err
    uid = user['id']
    today = datetime.date.today().isoformat()
    conn = get_db()

    pending_count = conn.execute(
        "SELECT COUNT(*) FROM RichiesteVacanza WHERE id_utente=? AND stato='pending'", (uid,)
    ).fetchone()[0]

    days_rows = conn.execute(
        "SELECT data_inizio, data_fine FROM RichiesteVacanza WHERE id_utente=? AND stato='approved'", (uid,)
    ).fetchall()
    days_used = sum(_days_between(r['data_inizio'], r['data_fine']) for r in days_rows if r['data_fine'] < today)

    recent = conn.execute(
        'SELECT id, tipo, data_inizio, data_fine, stato FROM RichiesteVacanza WHERE id_utente=? ORDER BY data_creazione DESC LIMIT 4',
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
    user, err = _require_session()
    if err:
        return err
    uid = user['id']
    id_gruppo = user['id_gruppo']

    # Calcola primo e ultimo giorno del mese
    first = datetime.date(year, month, 1)
    if month == 12:
        last = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    last_day = last.day
    month_start = first.isoformat()
    month_end = last.isoformat()

    conn = get_db()
    rows = conn.execute(
        '''SELECT rv.id_utente, rv.data_inizio, rv.data_fine, u.nome, u.cognome, u.id_gruppo
           FROM RichiesteVacanza rv
           JOIN Utenti u ON u.id = rv.id_utente
           WHERE rv.stato = 'approved'
             AND rv.data_inizio <= ? AND rv.data_fine >= ?''',
        (month_end, month_start)
    ).fetchall()

    blocked_rows = conn.execute(
        'SELECT data_inizio, data_fine FROM PeriodiBlocchi WHERE data_inizio <= ? AND data_fine >= ?',
        (month_end, month_start)
    ).fetchall()
    conn.close()

    blocked_days = set()
    for br in blocked_rows:
        bs = datetime.date.fromisoformat(br['data_inizio'])
        be = datetime.date.fromisoformat(br['data_fine'])
        for day_num in range(1, last_day + 1):
            d = datetime.date(year, month, day_num)
            if bs <= d <= be:
                blocked_days.add(day_num)

    PALETTE = ['#2ECC71', '#8e44ad', '#2980b9', '#e67e22', '#1abc9c', '#e74c3c', '#f39c12', '#16a085']
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
        start = datetime.date.fromisoformat(row['data_inizio'])
        end = datetime.date.fromisoformat(row['data_fine'])
        start_day = max(start.day, 1) if start.year == year and start.month == month else 1
        end_day = min(end.day, last_day) if end.year == year and end.month == month else last_day
        bookings.setdefault(key, []).append([start_day, end_day])

    return jsonify({'people': people, 'bookings': bookings, 'blocked_days': sorted(blocked_days)})


@app.route('/api/heatmap/<int:year>/<int:month>', methods=['GET'])
def heatmap(year, month):
    user, err = _require_session()
    if err:
        return err
    id_gruppo = user['id_gruppo']

    if month == 12:
        last_day = (datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)).day
    else:
        last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)).day
    month_start = f"{year:04d}-{month:02d}-01"
    month_end = f"{year:04d}-{month:02d}-{last_day:02d}"

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

    absent_days = {}
    for brow in bookings_rows:
        u_id = brow['id_utente']
        start = datetime.date.fromisoformat(brow['data_inizio'])
        end = datetime.date.fromisoformat(brow['data_fine'])
        for day_num in range(1, last_day + 1):
            d = datetime.date(year, month, day_num)
            if start <= d <= end and d.weekday() < 5:
                absent_days.setdefault(u_id, set()).add(day_num)

    buckets = [(1, 7), (8, 14), (15, 21), (22, last_day)]

    def presence_level(u_id, bs, be):
        workdays = sum(1 for d in range(bs, be + 1) if datetime.date(year, month, d).weekday() < 5)
        if workdays == 0:
            return 'high'
        absent = len(absent_days.get(u_id, set()) & set(range(bs, be + 1)))
        ratio = 1 - absent / workdays
        if ratio >= 0.8:
            return 'high'
        elif ratio >= 0.5:
            return 'med'
        return 'low'

    members_out = [
        {
            'name': f"{m['nome'][0]}. {m['cognome']}",
            'data': [presence_level(m['id'], bs, be) for bs, be in buckets],
        }
        for m in members_rows
    ]
    return jsonify({'members': members_out})


# ── Requests ─────────────────────────────────────────────────────────────────

@app.route('/api/requests', methods=['GET'])
def requests_list():
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    rows = conn.execute(
        'SELECT id, tipo, data_inizio, data_fine, stato, note_dipendente, data_creazione FROM RichiesteVacanza WHERE id_utente=? ORDER BY data_creazione DESC',
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
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    row = conn.execute(
        '''SELECT rv.*, u.nome AS u_nome, u.cognome AS u_cognome,
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
        {'label': 'Inviata',      'done': True,              'active': False},
        {'label': 'Responsabile', 'done': stato != 'pending', 'active': stato == 'pending'},
        {'label': 'Approvata',    'done': stato == 'approved','active': stato == 'rejected'},
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
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    tipo  = data.get('type', 'ferie')
    start = data.get('start_date', '')
    end   = data.get('end_date', '')
    notes = data.get('notes', '')
    if not start or not end:
        return jsonify({'error': 'start_date and end_date required'}), 400

    today = datetime.date.today().isoformat()
    is_manager = bool(user['is_manager'])
    is_ceo = user['ruolo'] == 'CEO'
    stato = 'approved' if (is_manager or is_ceo) else 'pending'
    approvatore = user['id'] if (is_manager or is_ceo) else None

    conn = get_db()
    cur = conn.execute(
        '''INSERT INTO RichiesteVacanza
           (tipo, data_inizio, data_fine, stato, note_dipendente, data_creazione, data_aggiornamento, id_utente, id_approvatore)
           VALUES (?,?,?,?,?,?,?,?,?)''',
        (tipo, start, end, stato, notes or None, today, today, user['id'], approvatore)
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
    user, err = _require_session()
    if err:
        return err
    return _change_stato(req_id, 'approved', user)


@app.route('/api/requests/<int:req_id>/reject', methods=['POST'])
def request_reject(req_id):
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
    manager_check = conn.execute('SELECT id_responsabile FROM Gruppi WHERE id=?', (row['id_gruppo'],)).fetchone()
    if not manager_check or manager_check['id_responsabile'] != user['id']:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403
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
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'text required'}), 400
    today = datetime.date.today().isoformat()
    conn = get_db()
    req_row = conn.execute(
        'SELECT rv.id_utente, u.id_gruppo FROM RichiesteVacanza rv JOIN Utenti u ON u.id=rv.id_utente WHERE rv.id=?',
        (req_id,)
    ).fetchone()
    if req_row:
        is_owner = req_row['id_utente'] == user['id']
        is_ceo = user['ruolo'] == 'CEO'
        manager_row = conn.execute('SELECT id_responsabile FROM Gruppi WHERE id=?', (req_row['id_gruppo'],)).fetchone()
        is_group_manager = manager_row and manager_row['id_responsabile'] == user['id']
        if not (is_owner or is_ceo or is_group_manager):
            conn.close()
            return jsonify({'error': 'Non autorizzato'}), 403
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
        '''SELECT rv.id, rv.tipo, rv.data_inizio, rv.data_fine, rv.stato, u.nome, u.cognome
           FROM RichiesteVacanza rv JOIN Utenti u ON u.id=rv.id_utente
           WHERE u.id_gruppo=? ORDER BY rv.data_inizio DESC''',
        (id_gruppo,)
    ).fetchall()

    def _conflicts(req_id, r_start, r_end):
        return conn.execute(
            '''SELECT COUNT(*) FROM RichiesteVacanza rv JOIN Utenti u ON u.id=rv.id_utente
               WHERE u.id_gruppo=? AND rv.id != ?
                 AND rv.stato IN ('approved','pending')
                 AND rv.data_inizio <= ? AND rv.data_fine >= ?''',
            (id_gruppo, req_id, r_end, r_start)
        ).fetchone()[0]

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
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    nome      = (data.get('nome') or '').strip()
    cognome   = (data.get('cognome') or '').strip()
    email     = (data.get('email') or '').strip()
    id_ruolo  = data.get('id_ruolo')
    id_gruppo = data.get('id_gruppo')
    if not nome or not cognome or not email or not id_ruolo or not id_gruppo:
        return jsonify({'error': 'tutti i campi sono obbligatori'}), 400
    conn = get_db()
    ruolo_row = conn.execute('SELECT ruolo FROM Ruoli WHERE id=?', (id_ruolo,)).fetchone()
    if ruolo_row and ruolo_row['ruolo'] == 'CEO':
        conn.close()
        return jsonify({'error': 'Non è possibile creare un utente con ruolo CEO'}), 400
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
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    rows = conn.execute('SELECT id, ruolo FROM Ruoli ORDER BY ruolo').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/rules', methods=['GET'])
def admin_rules_list():
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
    return jsonify([{**dict(r), 'permanente': bool(r['permanente'])} for r in rows])


@app.route('/api/admin/rules', methods=['POST'])
def admin_rules_create():
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
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    conn = get_db()
    if not conn.execute('SELECT id FROM VincoliPresenza WHERE id=?', (rule_id,)).fetchone():
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    conn.execute(
        '''UPDATE VincoliPresenza SET permanente=?, min_dipendenti=?, min_giorni=?, max_giorni=?,
                  data_inizio=?, data_fine=?, id_ruolo=?, id_gruppo=? WHERE id=?''',
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
    user, err = _require_session()
    if err:
        return err
    today = datetime.date.today().isoformat()
    future = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    ninety_ago = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
    conn = get_db()

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

    conflict_rows = conn.execute(
        '''SELECT r1.id AS id_a, u1.nome||' '||u1.cognome AS dipendente_a,
                  r2.id AS id_b, u2.nome||' '||u2.cognome AS dipendente_b,
                  g.nome AS gruppo,
                  MAX(r1.data_inizio, r2.data_inizio) AS overlap_inizio,
                  MIN(r1.data_fine, r2.data_fine) AS overlap_fine
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


# ── Periodi Bloccati ──────────────────────────────────────────────────────────

@app.route('/api/admin/blocked-periods', methods=['GET'])
def blocked_periods_list():
    user, err = _require_session()
    if err:
        return err
    conn = get_db()
    rows = conn.execute('SELECT id, data_inizio, data_fine, motivo FROM PeriodiBlocchi ORDER BY data_inizio').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/blocked-periods', methods=['POST'])
def blocked_periods_create():
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    data_inizio = (data.get('data_inizio') or '').strip()
    data_fine   = (data.get('data_fine') or '').strip()
    motivo      = (data.get('motivo') or '').strip() or None
    if not data_inizio or not data_fine:
        return jsonify({'error': 'data_inizio e data_fine obbligatorie'}), 400
    conn = get_db()
    cur = conn.execute('INSERT INTO PeriodiBlocchi (data_inizio, data_fine, motivo) VALUES (?,?,?)', (data_inizio, data_fine, motivo))
    conn.commit()
    conn.close()
    return jsonify({'id': cur.lastrowid}), 201


@app.route('/api/admin/blocked-periods/<int:bp_id>', methods=['DELETE'])
def blocked_periods_delete(bp_id):
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
    user, err = _require_session()
    if err:
        return err
    return jsonify(_user_dict(user))


@app.route('/api/user/profile', methods=['POST'])
def profile_update():
    user, err = _require_session()
    if err:
        return err
    data = request.get_json(force=True) or {}
    nome    = (data.get('nome') or '').strip()
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
    app.run(debug=True, host='0.0.0.0', port=5001)
