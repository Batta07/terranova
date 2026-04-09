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

  let calendarData = { people: {}, bookings: {}, blocked_days: [] };

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
    _updateNavVisibility(user);
  }

  function _updateNavVisibility(user) {
    // Team: solo per responsabili (is_manager) e CEO
    $$('[data-screen="team"]').forEach(el => {
      el.style.display = (user.is_manager || user.is_ceo) ? '' : 'none';
    });
    // Admin: solo per CEO
    $$('[data-screen="admin"]').forEach(el => {
      el.style.display = user.is_ceo ? '' : 'none';
    });
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
    const existingSelect = $('#user-select');
    if (existingSelect) existingSelect.value = '';
    await initLoginForm();
    navigateTo('login');
  };

  $('#btn-logout').addEventListener('click', handleLogout);
  $('#btn-logout-mobile').addEventListener('click', handleLogout);

  // ── AVATAR DROPDOWN ─────────────────────────────
  $('#nav-avatar').addEventListener('click', (e) => {
    // Non bloccare i click sui link del dropdown (navigazione e logout)
    if (e.target.closest('.dropdown-item')) return;
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
    if (cards[0]) cards[0].textContent = data.in_approvazione;
    if (cards[1]) cards[1].textContent = data.ferie_passate;

    const subtitle = $('#dashboard-subtitle');
    if (subtitle && state.currentUser) {
      subtitle.textContent = `Benvenuto, ${state.currentUser.nome} ${state.currentUser.cognome}`;
    }

    const tbody = $('#dashboard-recent-tbody');
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

    // Activity feed from recent requests
    const feed = $('#activity-feed');
    if (feed) {
      const dotClass = { approved: 'success', pending: 'warning', rejected: 'danger' };
      feed.innerHTML = data.recent_requests.length
        ? data.recent_requests.map(r => `
            <div class="activity-item">
              <div class="activity-dot activity-dot--${dotClass[r.stato] || 'info'}"></div>
              <div class="activity-body">
                <p class="activity-text"><strong>#${r.id}</strong> — ${tipoLabel(r.tipo)} ${statoLabel(r.stato).toLowerCase()}</p>
                <span class="activity-time">${formatPeriod(r.data_inizio, r.data_fine)}</span>
              </div>
            </div>`).join('')
        : '<p style="color:var(--text-muted);font-size:.9rem">Nessuna attività recente.</p>';
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

      const isBlocked = (calendarData.blocked_days || []).includes(d);

      if (isWeekend) {
        cell.classList.add('cal-day--weekend');
        cell.classList.add('cal-day--blocked');
      } else if (isBlocked) {
        cell.classList.add('cal-day--nonbookable');
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

      if (!isWeekend && !isBlocked) {
        cell.classList.add('cal-day--clickable');
        cell.addEventListener('click', () => {
          const pad = n => String(n).padStart(2, '0');
          const dateStr = `${year}-${pad(month + 1)}-${pad(d)}`;
          openNewRequest(dateStr);
        });
      }

      grid.appendChild(cell);
    }
  }

  function openNewRequest(dateStr) {
    navigateTo('new-request');
    const startInput = $('#new-request-start');
    const endInput   = $('#new-request-end');
    if (startInput) startInput.value = dateStr;
    if (endInput)   endInput.value   = dateStr;
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
    // Apply initial active state based on state.activeFilters
    if (state.activeFilters.has(btn.dataset.filter)) {
      btn.classList.add('filter-toggle--active');
    }
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
    const detailMeta = $('#detail-meta');
    if (detailMeta) {
      detailMeta.innerHTML = [
        ['Tipo',       tipoLabel(data.tipo)],
        ['Periodo',    formatPeriod(data.data_inizio, data.data_fine)],
        ['Durata',     `${data.giorni} giorni`],
        ['Stato',      `<span class="badge ${statoBadge(data.stato)}">${statoLabel(data.stato)}</span>`],
        ['Data invio', data.data_creazione],
        ['Richiedente',`${data.utente.nome} ${data.utente.cognome}`],
      ].map(([label, val]) => `
        <div class="meta-row">
          <span class="meta-label">${label}</span>
          <span class="meta-value">${val}</span>
        </div>`).join('');
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
      const isPending = data.stato === 'pending';
      managerCard.style.display = (isManager && !isOwn && isPending) ? '' : 'none';

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
    const year  = state.calendarDate.getFullYear();
    const month = state.calendarDate.getMonth() + 1;
    const [data, heatmapData] = await Promise.all([
      api('GET', '/api/team'),
      api('GET', `/api/heatmap/${year}/${month}`),
    ]);
    if (!data) return;

    // Update group name
    const groupNameEl = $('#team-group-name');
    if (groupNameEl) groupNameEl.textContent = data.group_name || '';
    const title = $('#screen-team .card-title');
    if (title) title.textContent = `Copertura team - ${data.group_name}`;

    // Render heatmap with real data
    if (heatmapData) renderHeatmap(heatmapData.members || []);

    const teamScreen = $('#screen-team');
    if (!teamScreen) return;

    // Team requests table
    const tbody = $('#team-requests-tbody');
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
    if (users) _renderAdminUsers(users);

    // Groups tab
    const groupsTbody = $('#admin-groups-tbody');
    if (groupsTbody && groups) {
      groupsTbody.innerHTML = groups.map(g => `
        <tr>
          <td>${g.nome}</td>
          <td>${g.descrizione || '--'}</td>
          <td>${g.manager || '--'}</td>
          <td>${g.num_membri}</td>
        </tr>`).join('');
    }

    // Rules tab
    if (rules) _renderRules(rules);

    // Simulation tab
    if (simulation) _renderSimulation(simulation);
  }

  // ── USERS CRUD ───────────────────────────────────
  function _renderAdminUsers(users) {
    const tbody = $('#admin-users-tbody');
    if (!tbody) return;
    tbody.innerHTML = users.map(u => `
      <tr>
        <td>${u.nome} ${u.cognome}</td>
        <td class="mono">${u.email}</td>
        <td>${u.ruolo}${u.is_manager ? ' <span class="badge badge--success" style="font-size:.7rem">Manager</span>' : ''}</td>
        <td>${u.gruppo}</td>
      </tr>`).join('');
  }

  async function _openAddUserForm() {
    // Load dropdowns if needed
    await _loadRulesDropdowns();
    const ruoloSel = $('#new-user-ruolo');
    const gruppoSel = $('#new-user-gruppo');
    if (ruoloSel) {
      ruoloSel.innerHTML = _rulesDropdownData.roles
        .filter(r => r.ruolo !== 'CEO')
        .map(r => `<option value="${r.id}">${r.ruolo}</option>`).join('');
    }
    if (gruppoSel) {
      gruppoSel.innerHTML = _rulesDropdownData.groups
        .map(g => `<option value="${g.id}">${g.nome}</option>`).join('');
    }
    $('#add-user-card').style.display = '';
    $('#add-user-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  document.addEventListener('click', async (e) => {
    if (e.target.id === 'btn-add-user') { _openAddUserForm(); return; }
    if (e.target.id === 'btn-add-user-cancel') {
      $('#add-user-card').style.display = 'none';
      $('#form-add-user').reset();
      return;
    }
    if (e.target.id === 'btn-add-group') {
      $('#add-group-card').style.display = '';
      $('#add-group-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    if (e.target.id === 'btn-add-group-cancel') {
      $('#add-group-card').style.display = 'none';
      $('#form-add-group').reset();
      return;
    }
  });

  $('#form-add-group').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      nome:        $('#new-group-nome').value.trim(),
      descrizione: $('#new-group-descrizione').value.trim(),
    };
    const res = await api('POST', '/api/admin/groups', payload);
    if (res) {
      $('#add-group-card').style.display = 'none';
      $('#form-add-group').reset();
      const groups = await api('GET', '/api/admin/groups');
      if (groups) {
        const tbody = $('#admin-groups-tbody');
        if (tbody) tbody.innerHTML = groups.map(g => `
          <tr>
            <td>${g.nome}</td>
            <td>${g.descrizione || '--'}</td>
            <td>${g.manager || '--'}</td>
            <td>${g.num_membri}</td>
          </tr>`).join('');
      }
    }
  });

  $('#form-add-user').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      nome:      $('#new-user-nome').value.trim(),
      cognome:   $('#new-user-cognome').value.trim(),
      email:     $('#new-user-email').value.trim(),
      id_ruolo:  parseInt($('#new-user-ruolo').value),
      id_gruppo: parseInt($('#new-user-gruppo').value),
    };
    // Check CEO role client-side
    const selectedRuolo = $('#new-user-ruolo');
    if (selectedRuolo) {
      const selectedText = selectedRuolo.options[selectedRuolo.selectedIndex]?.text || '';
      if (selectedText === 'CEO') { alert('Non è possibile creare un altro utente con ruolo CEO.'); return; }
    }
    const res = await api('POST', '/api/admin/users', payload);
    if (res) {
      $('#add-user-card').style.display = 'none';
      $('#form-add-user').reset();
      const users = await api('GET', '/api/admin/users');
      if (users) _renderAdminUsers(users);
    }
  });

  // ── RULES CRUD ───────────────────────────────────
  let _rulesDropdownData = { roles: [], groups: [] };

  async function _loadRulesDropdowns() {
    if (_rulesDropdownData.roles.length) return;
    const [roles, groups] = await Promise.all([
      api('GET', '/api/admin/roles'),
      api('GET', '/api/admin/groups'),
    ]);
    _rulesDropdownData = { roles: roles || [], groups: groups || [] };

    const ruoloSel = $('#rule-ruolo');
    const gruppoSel = $('#rule-gruppo');
    if (ruoloSel) {
      ruoloSel.innerHTML = '<option value="">— Tutti i ruoli —</option>' +
        _rulesDropdownData.roles.map(r => `<option value="${r.id}">${r.ruolo}</option>`).join('');
    }
    if (gruppoSel) {
      gruppoSel.innerHTML = '<option value="">— Tutti i gruppi —</option>' +
        _rulesDropdownData.groups.map(g => `<option value="${g.id}">${g.nome}</option>`).join('');
    }
  }

  function _renderRules(rules) {
    const list = $('#rules-list');
    if (!list) return;
    if (!rules.length) {
      list.innerHTML = '<p style="color:var(--text-muted);font-size:.875rem">Nessun vincolo configurato.</p>';
      return;
    }
    list.innerHTML = rules.map(r => `
      <div class="rule-card" style="margin-bottom:.75rem;padding:1rem;border:1px solid var(--border-color);border-radius:var(--radius);">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:1rem;">
          <div style="display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;flex:1;">
            <span><strong>${r.permanente ? 'Permanente' : 'Temporaneo'}</strong></span>
            <span>Min. presenti: <strong>${r.min_dipendenti}</strong></span>
            ${r.min_giorni ? `<span>Min. giorni: <strong>${r.min_giorni}</strong></span>` : ''}
            ${r.max_giorni ? `<span>Max. giorni: <strong>${r.max_giorni}</strong></span>` : ''}
            ${r.ruolo  ? `<span>Ruolo: <strong>${r.ruolo}</strong></span>` : ''}
            ${r.gruppo ? `<span>Gruppo: <strong>${r.gruppo}</strong></span>` : ''}
            ${!r.permanente && r.data_inizio ? `<span>Dal <strong>${r.data_inizio}</strong> al <strong>${r.data_fine || '--'}</strong></span>` : ''}
          </div>
          <div style="display:flex;gap:.5rem;flex-shrink:0;">
            <button class="btn btn--sm btn--ghost" data-rule-edit="${r.id}">Modifica</button>
            <button class="btn btn--sm btn--danger" data-rule-delete="${r.id}">Elimina</button>
          </div>
        </div>
      </div>`).join('');
  }

  function _openRuleForm(rule) {
    $('#rule-form-title').textContent = rule ? 'Modifica vincolo' : 'Nuovo vincolo';
    $('#rule-edit-id').value = rule ? rule.id : '';
    $('#rule-permanente').value = rule ? (rule.permanente ? '1' : '0') : '1';
    $('#rule-min').value = rule ? rule.min_dipendenti : 1;
    $('#rule-min-giorni').value = rule ? (rule.min_giorni || '') : '';
    $('#rule-max-giorni').value = rule ? (rule.max_giorni || '') : '';
    $('#rule-data-inizio').value = rule ? (rule.data_inizio || '') : '';
    $('#rule-data-fine').value = rule ? (rule.data_fine || '') : '';

    _loadRulesDropdowns().then(() => {
      const ruoloSel = $('#rule-ruolo');
      const gruppoSel = $('#rule-gruppo');
      if (ruoloSel && rule) {
        const matchingOption = Array.from(ruoloSel.options).find(o => o.textContent === rule.ruolo);
        ruoloSel.value = matchingOption ? matchingOption.value : '';
      } else if (ruoloSel) {
        ruoloSel.value = '';
      }
      if (gruppoSel && rule) {
        const matchingOption = Array.from(gruppoSel.options).find(o => o.textContent === rule.gruppo);
        gruppoSel.value = matchingOption ? matchingOption.value : '';
      } else if (gruppoSel) {
        gruppoSel.value = '';
      }
    });

    $('#rule-form-card').style.display = '';
    $('#rule-form-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function _closeRuleForm() {
    $('#rule-form-card').style.display = 'none';
    $('#form-rule').reset();
    $('#rule-edit-id').value = '';
  }

  // Wire rule form buttons
  document.addEventListener('click', async (e) => {
    if (e.target.id === 'btn-new-rule') {
      await _loadRulesDropdowns();
      _openRuleForm(null);
      return;
    }
    if (e.target.id === 'btn-rule-cancel') {
      _closeRuleForm();
      return;
    }
    if (e.target.dataset.ruleEdit) {
      const ruleId = parseInt(e.target.dataset.ruleEdit);
      const rules = await api('GET', '/api/admin/rules');
      const rule = (rules || []).find(r => r.id === ruleId);
      if (rule) _openRuleForm(rule);
      return;
    }
    if (e.target.dataset.ruleDelete) {
      if (!confirm('Eliminare questo vincolo?')) return;
      const res = await api('DELETE', `/api/admin/rules/${e.target.dataset.ruleDelete}`);
      if (res) {
        const rules = await api('GET', '/api/admin/rules');
        _renderRules(rules || []);
      }
      return;
    }
  });

  $('#form-rule').addEventListener('submit', async (e) => {
    e.preventDefault();
    const editId = $('#rule-edit-id').value;
    const permanente = $('#rule-permanente').value === '1';
    const payload = {
      permanente,
      min_dipendenti: parseInt($('#rule-min').value) || 1,
      min_giorni:  parseInt($('#rule-min-giorni').value) || null,
      max_giorni:  parseInt($('#rule-max-giorni').value) || null,
      data_inizio: !permanente ? ($('#rule-data-inizio').value || null) : null,
      data_fine:   !permanente ? ($('#rule-data-fine').value || null)   : null,
      id_ruolo:    parseInt($('#rule-ruolo').value)  || null,
      id_gruppo:   parseInt($('#rule-gruppo').value) || null,
    };
    const res = editId
      ? await api('PUT',  `/api/admin/rules/${editId}`, payload)
      : await api('POST', '/api/admin/rules', payload);
    if (res) {
      _closeRuleForm();
      const rules = await api('GET', '/api/admin/rules');
      _renderRules(rules || []);
    }
  });

  function _renderSimulation(sim) {
    // Stats cards
    const statsEl = $('#simulation-stats');
    if (statsEl) {
      const stats = [
        { value: `${sim.tasso_approvazione}%`, label: 'Tasso approvazione', desc: 'Basato sui vincoli attivi', cls: 'success' },
        { value: sim.richieste_in_conflitto,   label: 'Richieste in conflitto', desc: 'Sovrapposizioni rilevate', cls: sim.richieste_in_conflitto > 0 ? 'warning' : 'success' },
        { value: `${sim.copertura_media}%`,    label: 'Copertura media team', desc: 'Prossimi 30 giorni', cls: 'info' },
      ];
      statsEl.innerHTML = stats.map(s => `
        <div class="glass-card simulation-stat">
          <div class="simulation-stat-value simulation-stat-value--${s.cls}">${s.value}</div>
          <div class="simulation-stat-label">${s.label}</div>
          <p class="simulation-stat-desc">${s.desc}</p>
        </div>`).join('');
    }

    // Coverage bars
    const barsEl = $('#simulation-bars');
    if (barsEl) {
      barsEl.innerHTML = sim.copertura_per_gruppo.map(g => {
        const pct = g.copertura_percentuale;
        const cls = pct >= 80 ? 'success' : pct >= 50 ? 'warning' : 'danger';
        return `
          <div class="sim-bar-group">
            <div class="sim-bar-label">${g.gruppo}</div>
            <div class="sim-bar-track">
              <div class="sim-bar-fill sim-bar-fill--${cls}" style="width:${pct}%"></div>
            </div>
            <span class="sim-bar-value">${pct}%</span>
          </div>`;
      }).join('');
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
      // Client-side: check for weekends in range
      if (formData.start_date && formData.end_date) {
        const s = new Date(formData.start_date + 'T00:00:00');
        const e = new Date(formData.end_date + 'T00:00:00');
        let cur = new Date(s);
        let hasWeekend = false;
        while (cur <= e) { if (cur.getDay() === 0 || cur.getDay() === 6) { hasWeekend = true; break; } cur.setDate(cur.getDate() + 1); }
        if (hasWeekend) { alert('Il periodo selezionato include giorni di weekend.'); return; }
      }
      const res = await fetch('/api/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(formData),
      });
      if (res.status === 400) {
        const err = await res.json().catch(() => ({}));
        alert(err.error || 'Errore nella richiesta.');
        return;
      }
      const result = res.ok ? await res.json() : null;
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
