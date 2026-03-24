/* ═══════════════════════════════════════════════════
   TERRANOVA GESTIONE FERIE - Application Logic
   ═══════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── STATE ───────────────────────────────────────
  const state = {
    currentScreen: 'dashboard',
    calendarDate: new Date(2026, 2, 1), // March 2026
    activeFilters: new Set(['mine']),
  };

  // People with colors and groups
  const people = {
    me:   { name: 'M. Battaglia', color: '#2ECC71', group: 'Engineering', filter: 'mine' },
    anna: { name: 'A. Greco',     color: '#8e44ad', group: 'Engineering', filter: 'colleagues' },
    paolo:{ name: 'P. Verdi',     color: '#2980b9', group: 'Design',      filter: 'colleagues' },
    sara: { name: 'S. Ferrari',   color: '#e67e22', group: 'Engineering', filter: 'group' },
    giulia:{ name: 'G. Bianchi',  color: '#1abc9c', group: 'Marketing',   filter: 'colleagues' },
  };

  // Bookings: person key -> array of [startDay, endDay] for March 2026
  const bookings = {
    me:     [[9, 11]],
    anna:   [[5, 6]],
    paolo:  [[17, 18]],
    sara:   [[24, 25]],
    giulia: [[12, 12]],
  };

  const monthNames = [
    'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
    'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'
  ];

  const dayHeaders = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'];

  // ── DOM REFS ────────────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // ── NAVIGATION ──────────────────────────────────
  function navigateTo(screenId) {
    if (!screenId) return;

    // Handle login screen separately
    if (screenId === 'login') {
      $('#screen-login').classList.add('screen--active');
      $('#screen-login').style.display = '';
      $('#app-shell').style.display = 'none';
      return;
    }

    // Hide login, show app
    $('#screen-login').classList.remove('screen--active');
    $('#screen-login').style.display = 'none';
    $('#app-shell').style.display = '';

    // Switch screens
    $$('.main-content .screen').forEach(s => s.classList.remove('screen--active'));
    const target = $(`#screen-${screenId}`);
    if (target) {
      target.classList.add('screen--active');
    }

    // Update nav active state
    $$('.nav-link').forEach(link => {
      link.classList.toggle('nav-link--active', link.dataset.screen === screenId);
    });

    // Close mobile nav
    closeMobileNav();

    state.currentScreen = screenId;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Wire up all navigation links
  document.addEventListener('click', (e) => {
    // Nav links
    const navLink = e.target.closest('[data-screen]');
    if (navLink) {
      e.preventDefault();
      navigateTo(navLink.dataset.screen);
      return;
    }

    // Clickable rows
    const row = e.target.closest('.clickable-row');
    if (row && row.dataset.screen) {
      navigateTo(row.dataset.screen);
      return;
    }
  });

  // ── LOGIN ───────────────────────────────────────
  $('#form-login').addEventListener('submit', (e) => {
    e.preventDefault();
    navigateTo('dashboard');
  });

  $('#btn-forgot').addEventListener('click', (e) => {
    e.preventDefault();
    $('#form-login').style.display = 'none';
    $('#form-forgot').style.display = '';
  });

  $('#btn-back-login').addEventListener('click', () => {
    $('#form-forgot').style.display = 'none';
    $('#form-login').style.display = '';
  });

  $('#form-forgot').addEventListener('submit', (e) => {
    e.preventDefault();
    alert('Link di reset inviato!');
    $('#form-forgot').style.display = 'none';
    $('#form-login').style.display = '';
  });

  // Logout
  const handleLogout = (e) => {
    e.preventDefault();
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

  // ── CALENDAR ────────────────────────────────────
  function getBookingsForDay(day, month, year) {
    if (month !== 2 || year !== 2026) return [];
    const result = [];
    for (const [personKey, ranges] of Object.entries(bookings)) {
      for (const [start, end] of ranges) {
        if (day >= start && day <= end) {
          result.push({ key: personKey, ...people[personKey] });
          break;
        }
      }
    }
    return result;
  }

  function renderCalendar() {
    const grid = $('#calendar-grid');
    const year = state.calendarDate.getFullYear();
    const month = state.calendarDate.getMonth();

    $('#cal-month').textContent = `${monthNames[month]} ${year}`;
    grid.innerHTML = '';

    // Day headers
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

    // Empty cells
    for (let i = 0; i < startOffset; i++) {
      const empty = document.createElement('div');
      empty.className = 'cal-day cal-day--empty';
      grid.appendChild(empty);
    }

    // Day cells
    for (let d = 1; d <= daysInMonth; d++) {
      const cell = document.createElement('div');
      cell.className = 'cal-day';

      const dayOfWeek = new Date(year, month, d).getDay();
      const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

      // Day number in top-left
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

      // Get bookings for this day and filter by active filters
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

        const label = document.createTextNode(booking.name);
        tag.appendChild(label);

        cell.appendChild(tag);
      });

      if (hasMyBooking) {
        cell.classList.add('cal-day--booked');
      }

      grid.appendChild(cell);
    }
  }

  function renderLegend() {
    const legend = $('#calendar-legend');
    legend.innerHTML = '';
    for (const [key, person] of Object.entries(people)) {
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
    renderCalendar();
  });

  $('#cal-next').addEventListener('click', () => {
    state.calendarDate.setMonth(state.calendarDate.getMonth() + 1);
    renderCalendar();
  });

  // Calendar filters
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
  function renderHeatmap() {
    const heatmap = $('#heatmap');
    heatmap.innerHTML = '';

    const weeks = ['Sett. 1', 'Sett. 2', 'Sett. 3', 'Sett. 4'];
    const members = [
      { name: 'M. Battaglia', data: ['high', 'high', 'med', 'high'] },
      { name: 'A. Greco', data: ['high', 'high', 'high', 'med'] },
      { name: 'P. Verdi', data: ['high', 'med', 'high', 'high'] },
      { name: 'S. Ferrari', data: ['high', 'high', 'high', 'high'] },
      { name: 'G. Bianchi', data: ['med', 'high', 'low', 'high'] },
    ];

    // Headers
    const emptyHeader = document.createElement('div');
    emptyHeader.className = 'heatmap-header';
    heatmap.appendChild(emptyHeader);

    weeks.forEach(w => {
      const header = document.createElement('div');
      header.className = 'heatmap-header';
      header.textContent = w;
      heatmap.appendChild(header);
    });

    // Rows
    members.forEach(member => {
      const nameCell = document.createElement('div');
      nameCell.className = 'heatmap-name';
      nameCell.textContent = member.name;
      heatmap.appendChild(nameCell);

      const labels = { high: '100%', med: '60%', low: '40%' };

      member.data.forEach(level => {
        const cell = document.createElement('div');
        cell.className = `heatmap-cell heatmap-cell--${level}`;
        cell.textContent = labels[level];
        heatmap.appendChild(cell);
      });
    });
  }

  // ── ADMIN TABS ──────────────────────────────────
  $$('.admin-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      $$('.admin-tab').forEach(t => t.classList.remove('admin-tab--active'));
      tab.classList.add('admin-tab--active');

      $$('.admin-panel').forEach(p => p.classList.remove('admin-panel--active'));
      const panel = $(`#admin-${tab.dataset.adminTab}`);
      if (panel) panel.classList.add('admin-panel--active');
    });
  });

  // ── NEW REQUEST FORM ────────────────────────────
  const newRequestForm = $('#form-new-request');
  if (newRequestForm) {
    newRequestForm.addEventListener('submit', (e) => {
      e.preventDefault();
      alert('Richiesta inviata con successo!');
      navigateTo('requests');
    });
  }

  // ── PREVENT DEFAULT ON REMAINING FORMS ──────────
  $$('form').forEach(form => {
    if (form.id === 'form-login' || form.id === 'form-forgot' || form.id === 'form-new-request') return;
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      alert('Salvato!');
    });
  });

  // ── INIT ────────────────────────────────────────
  renderCalendar();
  renderLegend();
  renderHeatmap();

})();
