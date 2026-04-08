/* ═══════════════════════════════════════════════════
   TERRANOVA GESTIONE FERIE - Application Logic
   ═══════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── STATE ───────────────────────────────────────
  const state = {
    currentScreen: 'login',
    calendarDate: new Date(),
    activeFilters: new Set(['mine']),
    currentUser: null,
    currentRequestId: null,
  };

  let calendarData = { people: {}, bookings: {} };

  const monthNames = [
    'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
    'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'
  ];

  const dayHeaders = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'];

  // ── DOM REFS ────────────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // ── API HELPER ──────────────────────────────────
  async function api(method, path, body) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
    };
    if (body) opts.body = JSON.stringify(body);
    try {
      const res = await fetch(path, opts);
      if (res.status === 401) {
        navigateTo('login');
        return null;
      }
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        console.error('API error', path, e);
        return null;
      }
      return res.json();
    } catch (err) {
      console.error('Fetch error', path, err);
      return null;
    }
  }

  // ── HELPERS ─────────────────────────────────────
  function formatPeriod(start, end) {
    const months = ['Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic'];
    const s = new Date(start + 'T00:00:00');
    const e = new Date(end + 'T00:00:00');
    if (s.getFullYear() === e.getFullYear() && s.getMonth() === e.getMonth()) {
      return `${s.getDate()}-${e.getDate()} ${months[s.getMonth()]} ${s.getFullYear()}`;
    }
    return `${s.getDate()} ${months[s.getMonth()]} - ${e.getDate()} ${months[e.getMonth()]} ${e.getFullYear()}`;
  }

  function statoBadge(s) {
    return { pending: 'badge--warning', approved: 'badge--success', rejected: 'badge--danger' }[s] || '';
  }

  function statoLabel(s) {
    return { pending: 'In attesa', approved: 'Approvata', rejected: 'Rifiutata' }[s] || s;
  }

  function tipoLabel(t) {
    return { ferie: 'Ferie', permesso: 'Permesso', malattia: 'Malattia', altro: 'Altro' }[t] || t;
  }

  function updateNavAvatar(user) {
    const initials = (user.nome[0] + user.cognome[0]).toUpperCase();
    const avatarSpan = $('#nav-avatar > span');
    if (avatarSpan) avatarSpan.textContent = initials;
  }

  // ── NAVIGATION ──────────────────────────────────
  function navigateTo(screenId) {
    if (!screenId) return;

    if (screenId === 'login') {
      $('#screen-login').classList.add('screen--active');
      $('#screen-login').style.display = '';
      $('#app-shell').style.display = 'none';
      state.currentScreen = 'login';
      return;
    }

    $('#screen-login').classList.remove('screen--active');
    $('#screen-login').style.display = 'none';
    $('#app-shell').style.display = '';

    $$('.main-content .screen').forEach(s => s.classList.remove('screen--active'));
    const target = $(`#screen-${screenId}`);
    if (target) target.classList.add('screen--active');

    $$('.nav-link').forEach(link => {
      link.classList.toggle('nav-link--active', link.dataset.screen === screenId);
    });

    closeMobileNav();
    state.currentScreen = screenId;
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Screen init dispatch
    const inits = {
      'dashboard':      () => { initDashboard(); fetchCalendar(); loadHeatmap(); },
      'requests':       initRequests,
      'request-detail': () => initRequestDetail(state.currentRequestId),
      'team':           initTeam,
      'admin':          initAdmin,
      'settings':       initSettings,
    };
    if (inits[screenId]) inits[screenId]();
  }

  // Wire up all navigation links
  document.addEventListener('click', (e) => {
    const navLink = e.target.closest('[data-screen]');
    if (navLink && !navLink.id.startsWith('btn-logout')) {
      e.preventDefault();
      const reqId = navLink.dataset.reqId || (navLink.closest('[data-req-id]') || {}).dataset?.reqId;
      if (reqId) state.currentRequestId = parseInt(reqId);
      navigateTo(navLink.dataset.screen);
      return;
    }

    const row = e.target.closest('.clickable-row');
    if (row && row.dataset.screen) {
      if (row.dataset.reqId) state.currentRequestId = parseInt(row.dataset.reqId);
      navigateTo(row.dataset.screen);
      return;
    }
  });

  // ── LOGIN ───────────────────────────────────────
  async function initLoginForm() {
    const users = await fetch('/api/auth/users').then(r => r.json()).catch(() => []);
    const form = $('.login-form');
    if (!form || $('#user-select')) return;
    const select = document.createElement('select');
    select.id = 'user-select';
    select.className = 'form-select';
    select.style.marginBottom = '1rem';
    select.innerHTML = '<option value="">Seleziona utente...</option>' +
      users.map(u => `<option value="${u.email}">${u.nome} ${u.cognome}</option>`).join('');
    const btn = $('#btn-google-login');
    form.insertBefore(select, btn);
  }

  $('#btn-google-login').addEventListener('click', async () => {
    const select = $('#user-select');
    const email = select ? select.value : '';
    if (!email) {
      alert('Seleziona un utente per continuare.');
      return;
    }
    const user = await api('POST', '/api/auth/login', { email });
    if (user) {
      state.currentUser = user;
      updateNavAvatar(user);
      navigateTo('dashboard');
    }
  });

  // Logout
  const handleLogout = async (e) => {
    e.preventDefault();
    await api('POST', '/api/auth/logout');
    state.currentUser = null;
    navigateTo('login');
  };

  $('#btn-logout').addEventListener('click', handleLogout);
  $('#btn-logout-mobile').addEventListener('click', handleLogout);

  // ── AVATAR DROPDOWN ─────────────────────────────
  $('#nav-avatar').addEventListener('click', (e) => {
    e.stopPropagation();
    $('#avatar-dropdown').classList.toggle('avatar-dropdown--open');
  });

  document.addEventListener('click', () => {
    $('#avatar-dropdown').classList.remove('avatar-dropdown--open');
  });

  // ── MOBILE NAV ──────────────────────────────────
  function closeMobileNav() {
    $('#mobile-nav').classList.remove('mobile-nav--open');
    $('#hamburger').classList.remove('navbar-hamburger--open');
  }

  $('#hamburger').addEventListener('click', () => {
    $('#mobile-nav').classList.toggle('mobile-nav--open');
    $('#hamburger').classList.toggle('navbar-hamburger--open');
  });

  // ── DASHBOARD ───────────────────────────────────
  async function initDashboard() {
    const data = await api('GET', '/api/dashboard');
    if (!data) return;

    const cards = $$('.summary-card-value');
    if (cards[0]) cards[0].textContent = data.ferie_residue;
    if (cards[1]) cards[1].textContent = data.in_approvazione;
    if (cards[2]) cards[2].textContent = data.ferie_passate;

    const trends = $$('.summary-card-trend');
    if (trends[0]) trends[0].textContent = `di ${data.ferie_totali} totali`;
    if (trends[2]) trends[2].textContent = `${data.percent_usate}% del totale`;

    const subtitle = $('.page-subtitle');
    if (subtitle && state.currentUser) {
      subtitle.textContent = `Benvenuto, ${state.currentUser.nome} ${state.currentUser.cognome}`;
    }

    const tbody = $('#screen-dashboard .data-table tbody');
    if (tbody) {
      tbody.innerHTML = data.recent_requests.length
        ? data.recent_requests.map(r => `
            <tr class="clickable-row" data-screen="request-detail" data-req-id="${r.id}">
              <td class="mono">#${r.id}</td>
              <td>${formatPeriod(r.data_inizio, r.data_fine)}</td>
              <td><span class="badge ${statoBadge(r.stato)}">${statoLabel(r.stato)}</span></td>
            </tr>`).join('')
        : '<tr><td colspan="3" style="text-align:center;color:var(--text-muted)">Nessuna richiesta</td></tr>';
    }
  }

  // ── CALENDAR ────────────────────────────────────
  function getBookingsForDay(day, month, year) {
    const result = [];
    for (const [key, ranges] of Object.entries(calendarData.bookings || {})) {
      for (const [start, end] of ranges) {
        if (day >= start && day <= end) {
          const person = (calendarData.people || {})[key];
          if (person) result.push({ key, ...person });
          break;
        }
      }
    }
    return result;
  }

  async function fetchCalendar() {
    const year = state.calendarDate.getFullYear();
    const month = state.calendarDate.getMonth() + 1;
    const data = await api('GET', `/api/calendar/${year}/${month}`);
    if (data) calendarData = data;
    renderCalendar();
    renderLegend();
  }

  function renderCalendar() {
    const grid = $('#calendar-grid');
    if (!grid) return;
    const year = state.calendarDate.getFullYear();
    const month = state.calendarDate.getMonth();

    $('#cal-month').textContent = `${monthNames[month]} ${year}`;
    grid.innerHTML = '';

    dayHeaders.forEach(d => {
      const header = document.createElement('div');
      header.className = 'cal-header';
      header.textContent = d;
      grid.appendChild(header);
    });

    const firstDay = new Date(year, month, 1).getDay();
    const startOffset = firstDay === 0 ? 6 : firstDay - 1;
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();
    const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;

    for (let i = 0; i < startOffset; i++) {
      const empty = document.createElement('div');
      empty.className = 'cal-day cal-day--empty';
      grid.appendChild(empty);
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const cell = document.createElement('div');
      cell.className = 'cal-day';

      const dayOfWeek = new Date(year, month, d).getDay();
      const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

      const numSpan = document.createElement('span');
      numSpan.className = 'cal-day-number';
      numSpan.textContent = d;
      cell.appendChild(numSpan);

      if (isWeekend) {
        cell.classList.add('cal-day--weekend');
        cell.classList.add('cal-day--blocked');
      }

      if (isCurrentMonth && d === today.getDate()) {
        cell.classList.add('cal-day--today');
      }

      const dayBookings = getBookingsForDay(d, month, year);
      let hasMyBooking = false;

      dayBookings.forEach(booking => {
        if (!state.activeFilters.has(booking.filter)) return;
        if (booking.filter === 'mine') hasMyBooking = true;

        const tag = document.createElement('div');
        tag.className = 'cal-booking';
        tag.style.backgroundColor = booking.color + '18';
        tag.style.color = booking.color;

        const dot = document.createElement('span');
        dot.className = 'cal-booking-dot';
        dot.style.backgroundColor = booking.color;
        tag.appendChild(dot);
        tag.appendChild(document.createTextNode(booking.name));
        cell.appendChild(tag);
      });

      if (hasMyBooking) cell.classList.add('cal-day--booked');
      grid.appendChild(cell);
    }
  }

  function renderLegend() {
    const legend = $('#calendar-legend');
    if (!legend) return;
    legend.innerHTML = '';
    for (const [, person] of Object.entries(calendarData.people || {})) {
      const item = document.createElement('span');
      item.className = 'legend-item';
      const dot = document.createElement('span');
      dot.className = 'legend-dot';
      dot.style.backgroundColor = person.color;
      item.appendChild(dot);
      item.appendChild(document.createTextNode(` ${person.name}`));
      legend.appendChild(item);
    }
  }

  $('#cal-prev').addEventListener('click', () => {
    state.calendarDate.setMonth(state.calendarDate.getMonth() - 1);
    fetchCalendar();
  });

  $('#cal-next').addEventListener('click', () => {
    state.calendarDate.setMonth(state.calendarDate.getMonth() + 1);
    fetchCalendar();
  });

  $$('.filter-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const filter = btn.dataset.filter;
      btn.classList.toggle('filter-toggle--active');
      if (state.activeFilters.has(filter)) {
        state.activeFilters.delete(filter);
      } else {
        state.activeFilters.add(filter);
      }
      renderCalendar();
    });
  });

  // ── HEATMAP ─────────────────────────────────────
  async function loadHeatmap() {
    const year = state.calendarDate.getFullYear();
    const month = state.calendarDate.getMonth() + 1;
    const data = await api('GET', `/api/heatmap/${year}/${month}`);
    if (data) renderHeatmap(data.members);
  }

  function renderHeatmap(members) {
    const heatmap = $('#heatmap');
    if (!heatmap) return;
    heatmap.innerHTML = '';

    const weeks = ['Sett. 1', 'Sett. 2', 'Sett. 3', 'Sett. 4'];

    const emptyHeader = document.createElement('div');
    emptyHeader.className = 'heatmap-header';
    heatmap.appendChild(emptyHeader);

    weeks.forEach(w => {
      const header = document.createElement('div');
      header.className = 'heatmap-header';
      header.textContent = w;
      heatmap.appendChild(header);
    });

    const labels = { high: '100%', med: '60%', low: '40%' };

    (members || []).forEach(member => {
      const nameCell = document.createElement('div');
      nameCell.className = 'heatmap-name';
      nameCell.textContent = member.name;
      heatmap.appendChild(nameCell);

      member.data.forEach(level => {
        const cell = document.createElement('div');
        cell.className = `heatmap-cell heatmap-cell--${level}`;
        cell.textContent = labels[level] || level;
        heatmap.appendChild(cell);
      });
    });
  }

  // ── MY REQUESTS ─────────────────────────────────
  async function initRequests() {
    const data = await api('GET', '/api/requests');
    if (!data) return;
    const tbody = $('#screen-requests .data-table tbody');
    if (!tbody) return;
    tbody.innerHTML = data.length
      ? data.map(r => `
          <tr class="clickable-row" data-screen="request-detail" data-req-id="${r.id}">
            <td class="mono">#REQ-${r.id}</td>
            <td>${tipoLabel(r.tipo)}</td>
            <td>${formatPeriod(r.data_inizio, r.data_fine)}</td>
            <td>${r.data_creazione}</td>
            <td>${r.giorni} giorni</td>
            <td><span class="badge ${statoBadge(r.stato)}">${statoLabel(r.stato)}</span></td>
            <td><button class="btn-icon btn-icon--sm">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button></td>
          </tr>`).join('')
      : '<tr><td colspan="7" style="text-align:center;color:var(--text-muted)">Nessuna richiesta</td></tr>';
  }

  // ── REQUEST DETAIL ──────────────────────────────
  async function initRequestDetail(id) {
    if (!id) return;
    const data = await api('GET', `/api/requests/${id}`);
    if (!data) return;

    // Update page ID
    const pageId = $('.page-id');
    if (pageId) pageId.textContent = `#REQ-${data.id}`;

    // Populate detail-meta
    const metaRows = $$('#screen-request-detail .meta-row .meta-value');
    if (metaRows.length >= 6) {
      metaRows[0].textContent = tipoLabel(data.tipo);
      metaRows[1].textContent = formatPeriod(data.data_inizio, data.data_fine);
      metaRows[2].textContent = `${data.giorni} giorni`;
      metaRows[3].innerHTML = `<span class="badge ${statoBadge(data.stato)}">${statoLabel(data.stato)}</span>`;
      metaRows[4].textContent = data.data_creazione;
      metaRows[5].textContent = `${data.utente.nome} ${data.utente.cognome}`;
    }

    // Comments
    _renderComments(data.comments);

    // Timeline (vertical)
    const timeline = $('#screen-request-detail .approval-timeline--vertical');
    if (timeline) {
      timeline.innerHTML = data.timeline.map(step => `
        <div class="timeline-step ${step.done ? 'timeline-step--done' : step.active ? 'timeline-step--active' : ''}">
          <div class="timeline-dot"></div>
          <div class="timeline-content">
            <span class="timeline-label">${step.label}</span>
            <span class="timeline-date">${step.date}</span>
          </div>
        </div>`).join('');
    }

    // Manager actions visibility
    const managerCard = $('.manager-actions');
    if (managerCard) {
      const isManager = state.currentUser && state.currentUser.is_manager;
      const isOwn = data.is_own;
      managerCard.style.display = (isManager && !isOwn) ? '' : 'none';

      if (isManager && !isOwn) {
        const btns = managerCard.querySelectorAll('button');
        const approveBtn = Array.from(btns).find(b => b.textContent.includes('Approva'));
        const rejectBtn  = Array.from(btns).find(b => b.textContent.includes('Rifiuta'));
        const motivArea  = managerCard.querySelector('textarea');

        if (approveBtn) {
          approveBtn.onclick = async () => {
            const motivation = motivArea ? motivArea.value : '';
            const res = await api('POST', `/api/requests/${id}/approve`, { motivation });
            if (res) initRequestDetail(id);
          };
        }
        if (rejectBtn) {
          rejectBtn.onclick = async () => {
            const motivation = motivArea ? motivArea.value.trim() : '';
            if (!motivation) { alert('Inserisci una motivazione per il rifiuto.'); return; }
            const res = await api('POST', `/api/requests/${id}/reject`, { motivation });
            if (res) initRequestDetail(id);
          };
        }
      }
    }

    // Comment submit
    const commentArea = $('#screen-request-detail .comment-input-area');
    if (commentArea) {
      const submitBtn = commentArea.querySelector('button');
      const textarea  = commentArea.querySelector('textarea');
      if (submitBtn) {
        submitBtn.onclick = async () => {
          const text = textarea ? textarea.value.trim() : '';
          if (!text) return;
          const res = await api('POST', `/api/requests/${id}/comments`, { text });
          if (res) {
            if (textarea) textarea.value = '';
            const fresh = await api('GET', `/api/requests/${id}`);
            if (fresh) _renderComments(fresh.comments);
          }
        };
      }
    }
  }

  function _renderComments(comments) {
    const thread = $('#screen-request-detail .discussion-thread');
    if (!thread) return;
    thread.innerHTML = (comments || []).map(c => {
      const initials = (c.utente.nome[0] + c.utente.cognome[0]).toUpperCase();
      return `
        <div class="comment">
          <div class="comment-header">
            <div class="comment-avatar">${initials}</div>
            <div class="comment-meta">
              <span class="comment-name">${c.utente.nome} ${c.utente.cognome}</span>
              <span class="comment-time">${c.data}</span>
            </div>
          </div>
          <p class="comment-body">${_escapeHtml(c.testo)}</p>
        </div>`;
    }).join('') || '<p style="color:var(--text-muted);font-size:.875rem">Nessun commento ancora.</p>';
  }

  function _escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  // ── TEAM ────────────────────────────────────────
  async function initTeam() {
    const data = await api('GET', '/api/team');
    if (!data) return;

    // Update title
    const title = $('#screen-team .card-title');
    if (title) title.textContent = `Copertura team - ${data.group_name}`;

    // Render heatmap (reuse the same heatmap element #heatmap is on dashboard,
    // team has its own — but in the single HTML they share the same id.
    // Use the parent context to find the right one.)
    const teamScreen = $('#screen-team');
    if (teamScreen) {
      const hm = teamScreen.querySelector('#heatmap');
      if (hm) {
        // temporarily swap the global reference
        const orig = document.getElementById('heatmap');
        renderHeatmap(data.heatmap || []);
      }
    }

    // Team requests table
    const tbody = teamScreen ? teamScreen.querySelector('.data-table tbody') : null;
    if (tbody) {
      tbody.innerHTML = data.requests.length
        ? data.requests.map(r => `
            <tr class="clickable-row" data-screen="request-detail" data-req-id="${r.id}">
              <td>
                <div class="member-cell">
                  <span class="member-avatar">${r.utente_nome.split(' ').map(n=>n[0]).join('').toUpperCase()}</span>
                  <span>${r.utente_nome}</span>
                </div>
              </td>
              <td class="mono">#${r.id}</td>
              <td>${formatPeriod(r.data_inizio, r.data_fine)}</td>
              <td>${r.giorni} gg</td>
              <td><span class="badge ${statoBadge(r.stato)}">${statoLabel(r.stato)}</span></td>
              <td>${r.conflitti > 0
                ? `<span class="conflict-indicator conflict-indicator--warn">${r.conflitti} sovrapposiz.</span>`
                : '<span style="color:var(--accent)">Nessuno</span>'}</td>
              <td><button class="btn btn--sm btn--ghost" data-screen="request-detail" data-req-id="${r.id}">Rivedi</button></td>
            </tr>`).join('')
        : '<tr><td colspan="7" style="text-align:center;color:var(--text-muted)">Nessuna richiesta nel team</td></tr>';
    }
  }

  // ── ADMIN ────────────────────────────────────────
  async function initAdmin() {
    const [users, groups, rules, simulation] = await Promise.all([
      api('GET', '/api/admin/users'),
      api('GET', '/api/admin/groups'),
      api('GET', '/api/admin/rules'),
      api('GET', '/api/admin/simulation'),
    ]);

    // Users tab
    const usersPanel = $('#admin-users');
    if (usersPanel && users) {
      const tbody = usersPanel.querySelector('tbody');
      if (tbody) {
        tbody.innerHTML = users.map(u => `
          <tr>
            <td>${u.nome} ${u.cognome}</td>
            <td>${u.email}</td>
            <td>${u.ruolo}</td>
            <td>${u.gruppo}${u.is_manager ? ' <span class="badge badge--success" style="font-size:.7rem">Manager</span>' : ''}</td>
          </tr>`).join('');
      }
    }

    // Groups tab
    const groupsPanel = $('#admin-groups');
    if (groupsPanel && groups) {
      const tbody = groupsPanel.querySelector('tbody');
      if (tbody) {
        tbody.innerHTML = groups.map(g => `
          <tr>
            <td>${g.nome}</td>
            <td>${g.descrizione || '--'}</td>
            <td>${g.manager || '--'}</td>
            <td>${g.num_membri}</td>
          </tr>`).join('');
      }
    }

    // Rules tab
    const rulesPanel = $('#admin-rules');
    if (rulesPanel && rules) {
      const tbody = rulesPanel.querySelector('tbody');
      if (tbody) {
        tbody.innerHTML = rules.map(r => `
          <tr>
            <td>${r.permanente ? 'Permanente' : 'Temporanea'}</td>
            <td>${r.min_dipendenti}</td>
            <td>${r.ruolo || '--'}</td>
            <td>${r.gruppo || '--'}</td>
            <td>${r.data_inizio || '--'}</td>
            <td>${r.data_fine || '--'}</td>
          </tr>`).join('');
      }
    }

    // Simulation tab
    if (simulation) {
      _renderSimulation(simulation);
    }
  }

  function _renderSimulation(sim) {
    const panel = $('#admin-simulation');
    if (!panel) return;

    // Update stat numbers if they exist as text nodes / spans
    const statValues = panel.querySelectorAll('.simulation-stat-value, .analytics-value');
    if (statValues.length >= 3) {
      statValues[0].textContent = `${sim.tasso_approvazione}%`;
      statValues[1].textContent = sim.richieste_in_conflitto;
      statValues[2].textContent = `${sim.copertura_media}%`;
    }

    // Coverage bars
    const coverageList = panel.querySelector('.coverage-list, .simulation-coverage');
    if (coverageList) {
      coverageList.innerHTML = sim.copertura_per_gruppo.map(g => `
        <div class="coverage-item">
          <span class="coverage-label">${g.gruppo}</span>
          <div class="coverage-bar">
            <div class="coverage-fill" style="width:${g.copertura_percentuale}%"></div>
          </div>
          <span class="coverage-pct">${g.copertura_percentuale}%</span>
        </div>`).join('');
    }

    // Conflict list
    const conflictList = panel.querySelector('.conflict-list');
    if (conflictList) {
      conflictList.innerHTML = sim.conflitti.length
        ? sim.conflitti.map(c => `
            <div class="conflict-row">
              <span class="conflict-indicator conflict-indicator--warn">
                ${c.dipendente_a} (#${c.richiesta_a}) ↔ ${c.dipendente_b} (#${c.richiesta_b})
                — ${c.gruppo} — ${c.overlap_inizio} / ${c.overlap_fine}
              </span>
            </div>`).join('')
        : '<p style="color:var(--accent)">Nessun conflitto rilevato.</p>';
    }
  }

  // Admin tabs (unchanged logic, just re-wire)
  $$('.admin-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      $$('.admin-tab').forEach(t => t.classList.remove('admin-tab--active'));
      tab.classList.add('admin-tab--active');
      $$('.admin-panel').forEach(p => p.classList.remove('admin-panel--active'));
      const panel = $(`#admin-${tab.dataset.adminTab}`);
      if (panel) panel.classList.add('admin-panel--active');
    });
  });

  // ── SETTINGS ────────────────────────────────────
  async function initSettings() {
    const data = await api('GET', '/api/user/profile');
    if (!data) return;

    const screen = $('#screen-settings');
    if (!screen) return;

    const inputs = screen.querySelectorAll('input[type=text], input[type=email]');
    // Map by position: nome, cognome, email (disabled), role (disabled)
    if (inputs[0]) inputs[0].value = data.nome;
    if (inputs[1]) inputs[1].value = data.cognome;
    if (inputs[2]) inputs[2].value = data.email;
    if (inputs[3]) inputs[3].value = data.ruolo;

    const form = screen.querySelector('form');
    if (form) {
      form.onsubmit = async (e) => {
        e.preventDefault();
        const nome = inputs[0] ? inputs[0].value.trim() : '';
        const cognome = inputs[1] ? inputs[1].value.trim() : '';
        const res = await api('POST', '/api/user/profile', { nome, cognome });
        if (res) {
          if (state.currentUser) {
            state.currentUser.nome = nome;
            state.currentUser.cognome = cognome;
            updateNavAvatar(state.currentUser);
          }
          alert('Profilo aggiornato!');
        }
      };
    }
  }

  // ── NEW REQUEST FORM ────────────────────────────
  const newRequestForm = $('#form-new-request');
  if (newRequestForm) {
    newRequestForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const selects = newRequestForm.querySelectorAll('select');
      const dates = newRequestForm.querySelectorAll('input[type=date]');
      const notes = newRequestForm.querySelector('textarea');
      const formData = {
        type:       selects[0] ? selects[0].value : 'ferie',
        start_date: dates[0]   ? dates[0].value   : '',
        end_date:   dates[1]   ? dates[1].value   : '',
        notes:      notes      ? notes.value       : '',
      };
      const result = await api('POST', '/api/requests', formData);
      if (result) {
        newRequestForm.reset();
        navigateTo('requests');
      }
    });
  }

  // ── PREVENT DEFAULT ON REMAINING FORMS ──────────
  $$('form').forEach(form => {
    if (form.id === 'form-new-request') return;
    if (!form.onsubmit) {
      form.addEventListener('submit', (e) => { e.preventDefault(); });
    }
  });

  // ── INIT ────────────────────────────────────────
  (async function init() {
    try {
      const user = await fetch('/api/auth/me', { credentials: 'same-origin' })
        .then(r => r.status === 401 ? null : r.json())
        .catch(() => null);
      if (user) {
        state.currentUser = user;
        updateNavAvatar(user);
        navigateTo('dashboard');
      } else {
        await initLoginForm();
        navigateTo('login');
      }
    } catch (e) {
      await initLoginForm();
      navigateTo('login');
    }
  })();

})();
