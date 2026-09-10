/* Возрождение — рассылка покупателям: рендер карточек, генерация писем/ссылок,
   чекбоксы "отправлено"/"прозвонили" с датой в localStorage, напоминание на
   следующий рабочий день. */
(function () {
  'use strict';

  var KEY = 'vozrozhdenie_buyers_mailer_v1';
  var SITE = 'https://goshva.github.io/vozrozhdenie-life.ru';

  function loadState() {
    try {
      var raw = localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) { return {}; }
  }
  function saveState(state) {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }

  function digitsOnly(phone) {
    if (!phone) return '';
    var d = phone.replace(/[^\d]/g, '');
    if (d.length === 11 && d[0] === '8') d = '7' + d.slice(1);
    return d;
  }

  function nextBusinessDay(fromMs) {
    var d = new Date(fromMs);
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() + 1);
    while (d.getDay() === 0 || d.getDay() === 6) { // 0=Sun, 6=Sat
      d.setDate(d.getDate() + 1);
    }
    return d.getTime();
  }

  function fmtDateTime(ms) {
    return new Date(ms).toLocaleString('ru-RU', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }
  function fmtDate(ms) {
    return new Date(ms).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  function buildMailto(b) {
    var greetName = b.contactName ? b.contactName.split(' ')[1] || b.contactName : '';
    var greeting = greetName ? ('Добрый день, ' + greetName + '!') : 'Добрый день!';
    var subject = 'Возрождение — коттеджный посёлок у реки Воронеж, Липецкая область';
    var body = [
      greeting,
      '',
      'Меня зовут Максим, ООО «Экспострой» — застройщик проекта «Возрождение» в Липецкой области.',
      '',
      'Хочу предложить ' + (b.company ? '«' + b.company + '»' : 'вашей компании') + ' ознакомиться с готовым девелоперским активом: 208 кадастровых участков (99 га) на берегу реки Воронеж, с оформленной концепцией коттеджного посёлка. Продаётся целиком одному инвестору.',
      '',
      'Инвестиционный тизер: ' + SITE + '/teaser.html',
      'PDF-версия для пересылки: ' + SITE + '/assets/docs/vozrozhdenie-teaser.pdf',
      '',
      'Буду рад обсудить детали по телефону или в мессенджере.',
      '',
      'С уважением,',
      'Максим Игоревич',
      '+7 910 351-13-33'
    ].join('\n');
    return 'mailto:' + encodeURIComponent(b.email) + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
  }

  function priorityClass(p) {
    if (p === 'A+') return 'p-A_';
    if (p === 'A') return 'p-A';
    if (p === 'B') return 'p-B';
    return 'p-C';
  }

  function renderCard(b, state) {
    var st = state[b.rank] || {};
    var card = document.createElement('div');
    card.className = 'by-card';
    card.dataset.rank = b.rank;
    card.dataset.search = (b.company + ' ' + b.region + ' ' + b.profile).toLowerCase();
    card.dataset.priority = b.priority;
    card.dataset.hasEmail = b.email ? '1' : '0';

    var contactsHtml = '';
    if (b.email) {
      contactsHtml += '<a class="by-chip mail" href="' + buildMailto(b) + '">&#9993; Написать письмо</a>';
    } else {
      contactsHtml += '<span class="by-chip missing">email не найден</span>';
    }
    var digits = digitsOnly(b.phone);
    var isMobileLike = digits.length === 11 && digits.slice(1, 4) !== '800'; // 8-800 toll-free lines aren't personal messenger contacts
    if (b.phone) {
      contactsHtml += '<a class="by-chip" href="tel:+' + digits + '">&#9742; ' + b.phone + '</a>';
      if (isMobileLike) {
        contactsHtml += '<a class="by-chip tg" href="https://t.me/+' + digits + '" target="_blank" rel="noopener">Telegram</a>';
        contactsHtml += '<a class="by-chip wa" href="https://wa.me/' + digits + '" target="_blank" rel="noopener">WhatsApp</a>';
      }
    } else {
      contactsHtml += '<span class="by-chip missing">телефон не найден</span>';
    }
    if (b.website) {
      var host = b.website.replace(/^https?:\/\//, '').replace(/\/$/, '');
      contactsHtml += '<a class="by-chip" href="' + b.website + '" target="_blank" rel="noopener">' + host + '</a>';
    }

    var contactPerson = b.contactName
      ? '<div class="by-meta">' + b.contactName + (b.contactPosition ? ' — ' + b.contactPosition : '') + '</div>'
      : '';

    var dueBadge = '';
    var isDue = false;
    if (st.sentAt && !st.calledAt) {
      var due = nextBusinessDay(st.sentAt);
      if (Date.now() >= due) {
        isDue = true;
        dueBadge = '<span class="by-duebadge">&#128222; Пора позвонить</span>';
      }
    }
    if (st.sentAt) card.classList.add('is-sent');
    if (isDue) card.classList.add('is-due');

    var sentInfo = st.sentAt
      ? '<span class="by-sentinfo">отправлено ' + fmtDateTime(st.sentAt) + (st.calledAt ? ' &middot; прозвонили ' + fmtDate(st.calledAt) : '') + '</span>'
      : '';

    card.innerHTML =
      '<div class="by-top">' +
        '<div>' +
          '<div class="by-name"><span class="by-rank">#' + b.rank + '</span> ' + b.company + '</div>' +
          '<div class="by-meta">' + b.region + ' &middot; ' + b.profile + '</div>' +
          contactPerson +
        '</div>' +
        '<span class="by-badge ' + priorityClass(b.priority) + '">' + b.priority + '</span>' +
      '</div>' +
      '<div class="by-contacts">' + contactsHtml + '</div>' +
      '<div class="by-bottom">' +
        '<div class="by-checks">' +
          '<label class="by-check"><input type="checkbox" class="js-sent" ' + (st.sentAt ? 'checked' : '') + '> Письмо отправлено</label>' +
          (st.sentAt ? '<label class="by-check"><input type="checkbox" class="js-called" ' + (st.calledAt ? 'checked' : '') + '> Прозвонили</label>' : '') +
        '</div>' +
        (dueBadge || sentInfo) +
      '</div>';

    var sentCb = card.querySelector('.js-sent');
    sentCb.addEventListener('change', function () {
      state = loadState();
      state[b.rank] = state[b.rank] || {};
      if (sentCb.checked) {
        state[b.rank].sentAt = Date.now();
      } else {
        delete state[b.rank].sentAt;
        delete state[b.rank].calledAt;
      }
      saveState(state);
      rerenderCard(b, state);
    });

    var calledCb = card.querySelector('.js-called');
    if (calledCb) {
      calledCb.addEventListener('change', function () {
        state = loadState();
        state[b.rank] = state[b.rank] || {};
        if (calledCb.checked) state[b.rank].calledAt = Date.now();
        else delete state[b.rank].calledAt;
        saveState(state);
        rerenderCard(b, state);
      });
    }

    return card;
  }

  function rerenderCard(b, state) {
    var old = document.querySelector('.by-card[data-rank="' + b.rank + '"]');
    if (!old) return;
    var fresh = renderCard(b, state);
    old.replaceWith(fresh);
    updateStats();
  }

  var allBuyers = [];

  function updateStats() {
    var state = loadState();
    var total = allBuyers.length;
    var sent = 0, due = 0;
    allBuyers.forEach(function (b) {
      var st = state[b.rank];
      if (st && st.sentAt) {
        sent++;
        if (!st.calledAt && Date.now() >= nextBusinessDay(st.sentAt)) due++;
      }
    });
    ['byTotal', 'byTotal2', 'byTotal3'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.textContent = total;
    });
    var elSent = document.getElementById('bySent');
    var elDue = document.getElementById('byDue');
    var elLeft = document.getElementById('byLeft');
    if (elSent) elSent.textContent = sent;
    if (elDue) elDue.textContent = due;
    if (elLeft) elLeft.textContent = total - sent;
  }

  /* ---------------- Фильтры: значения и состояние панели сохраняются
     отдельно от отметок "отправлено", чтобы "Сбросить всё" их не задевал. */
  var FILTER_KEY = 'vozrozhdenie_buyers_filters_v1';

  function loadFilterPrefs() {
    try {
      var raw = localStorage.getItem(FILTER_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) { return {}; }
  }
  function saveFilterPrefs(prefs) {
    try { localStorage.setItem(FILTER_KEY, JSON.stringify(prefs)); } catch (e) {}
  }

  function currentFilterValues() {
    return {
      q: document.getElementById('bySearch').value || '',
      prio: document.getElementById('byPrioFilter').value || '',
      status: document.getElementById('byStatusFilter').value || '',
      email: document.getElementById('byEmailFilter').value || ''
    };
  }

  function updateFilterBadge(vals) {
    var count = (vals.q ? 1 : 0) + (vals.prio ? 1 : 0) + (vals.status ? 1 : 0) + (vals.email ? 1 : 0);
    var badge = document.getElementById('byFilterBadge');
    var clearBtn = document.getElementById('byClearFiltersBtn');
    if (badge) { badge.hidden = count === 0; badge.textContent = count; }
    if (clearBtn) clearBtn.hidden = count === 0;
  }

  function applyFilters() {
    var vals = currentFilterValues();
    var q = vals.q.trim().toLowerCase();
    var prio = vals.prio;
    var statusFilter = vals.status;
    var state = loadState();
    var cards = document.querySelectorAll('.by-card');
    var visible = 0;
    cards.forEach(function (card) {
      var rank = card.dataset.rank;
      var matchesQ = !q || card.dataset.search.indexOf(q) !== -1;
      var matchesPrio = !prio || card.dataset.priority === prio;
      var st = state[rank] || {};
      var isSent = !!st.sentAt;
      var isDue = isSent && !st.calledAt && Date.now() >= nextBusinessDay(st.sentAt);
      var matchesStatus = true;
      if (statusFilter === 'not-sent') matchesStatus = !isSent;
      else if (statusFilter === 'sent') matchesStatus = isSent;
      else if (statusFilter === 'due') matchesStatus = isDue;
      var matchesEmail = true;
      if (vals.email === 'has') matchesEmail = card.dataset.hasEmail === '1';
      else if (vals.email === 'missing') matchesEmail = card.dataset.hasEmail === '0';
      var show = matchesQ && matchesPrio && matchesStatus && matchesEmail;
      card.hidden = !show;
      if (show) visible++;
    });
    var empty = document.getElementById('byEmpty');
    if (empty) empty.hidden = visible !== 0;
    var countEl = document.getElementById('byVisibleCount');
    if (countEl) countEl.textContent = visible;
    updateFilterBadge(vals);

    var prefs = loadFilterPrefs();
    prefs.q = vals.q; prefs.prio = vals.prio; prefs.status = vals.status; prefs.email = vals.email;
    saveFilterPrefs(prefs);
  }

  function setPanelOpen(open) {
    var panel = document.getElementById('byFilterPanel');
    var toggle = document.getElementById('byToggleBtn');
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    var prefs = loadFilterPrefs();
    prefs.open = open;
    saveFilterPrefs(prefs);
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (typeof BUYERS === 'undefined') return;
    allBuyers = BUYERS;
    var state = loadState();
    var list = document.getElementById('byList');
    var frag = document.createDocumentFragment();
    allBuyers.forEach(function (b) { frag.appendChild(renderCard(b, state)); });
    list.appendChild(frag);
    updateStats();

    // Восстановить сохранённые фильтры и состояние панели
    var prefs = loadFilterPrefs();
    if (prefs.q) document.getElementById('bySearch').value = prefs.q;
    if (prefs.prio) document.getElementById('byPrioFilter').value = prefs.prio;
    if (prefs.status) document.getElementById('byStatusFilter').value = prefs.status;
    if (prefs.email) document.getElementById('byEmailFilter').value = prefs.email;
    var hasActiveFilters = !!(prefs.q || prefs.prio || prefs.status || prefs.email);
    setPanelOpen(prefs.open === true || hasActiveFilters);
    applyFilters();

    document.getElementById('bySearch').addEventListener('input', applyFilters);
    document.getElementById('byPrioFilter').addEventListener('change', applyFilters);
    document.getElementById('byStatusFilter').addEventListener('change', applyFilters);
    document.getElementById('byEmailFilter').addEventListener('change', applyFilters);

    document.getElementById('byToggleBtn').addEventListener('click', function () {
      var panel = document.getElementById('byFilterPanel');
      setPanelOpen(panel.hidden);
    });

    document.getElementById('byClearFiltersBtn').addEventListener('click', function () {
      document.getElementById('bySearch').value = '';
      document.getElementById('byPrioFilter').value = '';
      document.getElementById('byStatusFilter').value = '';
      document.getElementById('byEmailFilter').value = '';
      applyFilters();
    });

    document.getElementById('byResetBtn').addEventListener('click', function () {
      if (!confirm('Сбросить все отметки "отправлено"/"прозвонили" по всем ' + allBuyers.length + ' записям? (Фильтры это не затронет.)')) return;
      saveState({});
      list.innerHTML = '';
      var frag2 = document.createDocumentFragment();
      allBuyers.forEach(function (b) { frag2.appendChild(renderCard(b, {})); });
      list.appendChild(frag2);
      updateStats();
      applyFilters();
    });
  });
})();
