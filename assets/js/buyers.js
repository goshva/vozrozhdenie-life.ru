/* Возрождение — рассылка покупателям: рендер карточек, генерация писем/ссылок,
   чекбоксы "отправлено"/"прозвонили" с датой в localStorage, напоминание на
   следующий рабочий день. */
(function () {
  'use strict';

  var KEY = 'vozrozhdenie_buyers_mailer_v1';
  var SITE = 'https://goshva.github.io/vozrozhdenie-life.ru';

  /* Тот же способ отправки в Telegram, что используется для визитов и формы
     обратной связи на главной странице (assets/js/main.js) — GET-запрос с
     токеном бота прямо из браузера (без бэкенда на GitHub Pages). */
  var TELEGRAM_BOT_TOKEN = '8431645174:AAGTV2Xg4mpOKiqaKHR73pVBBKUDHm0D_yo';
  var TELEGRAM_CHAT_ID = '190404167'; // Erop (@goshva13)

  function sendToTelegram(text) {
    var url = 'https://api.telegram.org/bot' + TELEGRAM_BOT_TOKEN + '/sendMessage'
      + '?chat_id=' + encodeURIComponent(TELEGRAM_CHAT_ID)
      + '&text=' + encodeURIComponent(text);
    return fetch(url, { method: 'GET', mode: 'no-cors' })
      .then(function () { return true; })
      .catch(function (err) { console.warn('[Возрождение] Telegram send failed', err); return false; });
  }

  var APP_LABELS = {
    telegram: 'Telegram', whatsapp: 'WhatsApp', max: 'MAX', viber: 'Viber', sms: 'SMS', email: 'Email', other: 'Другое'
  };

  function loadState() {
    try {
      var raw = localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) { return {}; }
  }
  function saveState(state) {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }

  /* ---------------- Резервная копия отметок: скачивание JSON-файла,
     отправка копии на почту через mailto: (без бэкенда) и загрузка файла
     обратно с объединением по каждой записи, чтобы не терять то, что уже
     отмечено в этом браузере. */
  var BACKUP_EMAIL = 'sha.egor@gmail.ru';

  function pad2(n) { return (n < 10 ? '0' : '') + n; }

  function backupFileName() {
    var d = new Date();
    return 'vozrozhdenie-buyers-backup-' + d.getFullYear() + pad2(d.getMonth() + 1) + pad2(d.getDate())
      + '-' + pad2(d.getHours()) + pad2(d.getMinutes()) + '.json';
  }

  function buildBackupPayload() {
    return { exportedAt: new Date().toISOString(), source: SITE, state: loadState() };
  }

  function triggerFileDownload(text, filename) {
    var blob = new Blob([text], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function showBackupStatus(text, isError) {
    var el = document.getElementById('byBackupStatus');
    if (!el) return;
    el.textContent = text;
    el.hidden = false;
    el.classList.toggle('is-error', !!isError);
  }

  function exportBackup() {
    triggerFileDownload(JSON.stringify(buildBackupPayload(), null, 2), backupFileName());
    showBackupStatus('Файл резервной копии скачан.', false);
  }

  function emailBackup() {
    var payload = buildBackupPayload();
    var compactJson = JSON.stringify(payload);
    var subject = 'Возрождение — резервная копия отметок покупателей';
    var body;
    if (compactJson.length > 1800) {
      // Слишком длинный текст письма многие почтовые клиенты обрезают —
      // в этом случае скачиваем файл и просим приложить его вручную.
      var filename = backupFileName();
      triggerFileDownload(JSON.stringify(payload, null, 2), filename);
      body = 'Копия отметок слишком большая, чтобы поместиться в тело письма — она только что скачалась '
        + 'файлом "' + filename + '". Прикрепите этот файл к письму вручную перед отправкой.';
    } else {
      body = 'Резервная копия отметок покупателей (JSON). Чтобы восстановить на другом устройстве — '
        + 'сохраните текст ниже в .json-файл и загрузите его кнопкой "Загрузить копию" на странице рассылки:\n\n'
        + compactJson;
    }
    window.location.href = 'mailto:' + encodeURIComponent(BACKUP_EMAIL)
      + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    showBackupStatus('Открываю почтовый клиент со сформированным письмом на ' + BACKUP_EMAIL + '…', false);
  }

  function mergeStates(current, incoming) {
    var merged = {};
    var ranks = {};
    Object.keys(current || {}).forEach(function (k) { ranks[k] = true; });
    Object.keys(incoming || {}).forEach(function (k) { ranks[k] = true; });
    Object.keys(ranks).forEach(function (rank) {
      var a = (current && current[rank]) || {};
      var b = (incoming && incoming[rank]) || {};
      var m = {};
      ['sentAt', 'corrAt', 'calledAt'].forEach(function (f) {
        if (a[f] && b[f]) m[f] = Math.max(a[f], b[f]);
        else if (a[f] || b[f]) m[f] = a[f] || b[f];
      });
      if (a.corrApp || b.corrApp) m.corrApp = a.corrApp || b.corrApp;
      if (a.meeting || b.meeting) {
        m.meeting = (b.meeting && (!a.meeting || (b.meeting.setAt || 0) > (a.meeting.setAt || 0))) ? b.meeting : a.meeting;
      }
      merged[rank] = m;
    });
    return merged;
  }

  function importBackupFile(file) {
    var reader = new FileReader();
    reader.onload = function () {
      var parsed;
      try {
        parsed = JSON.parse(reader.result);
      } catch (e) {
        showBackupStatus('Не удалось прочитать файл — это не корректный JSON.', true);
        return;
      }
      var incomingState = parsed && typeof parsed === 'object' && parsed.state ? parsed.state : parsed;
      if (!incomingState || typeof incomingState !== 'object') {
        showBackupStatus('В файле не найдены отметки для загрузки.', true);
        return;
      }
      var merged = mergeStates(loadState(), incomingState);
      saveState(merged);

      var list = document.getElementById('byList');
      list.innerHTML = '';
      var frag = document.createDocumentFragment();
      allBuyers.forEach(function (b) { frag.appendChild(renderCard(b, merged)); });
      list.appendChild(frag);
      updateStats();
      applyFilters();

      showBackupStatus('Загружено и объединено с текущими отметками: ' + Object.keys(incomingState).length + ' записей из файла.', false);
    };
    reader.onerror = function () {
      showBackupStatus('Не удалось прочитать файл.', true);
    };
    reader.readAsText(file);
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

  function buildMessageBody(b) {
    var greetName = b.contactName ? b.contactName.split(' ')[1] || b.contactName : '';
    var greeting = greetName ? ('Добрый день, ' + greetName + '!') : 'Добрый день!';
    return [
      greeting,
      '',
      'Меня зовут Максим Игоревич, ООО «Экспострой» — собственник проекта «Возрождение» в Липецкой области.',
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
  }

  function buildMailto(b) {
    var subject = 'Возрождение — коттеджный посёлок у реки Воронеж, Липецкая область';
    return 'mailto:' + encodeURIComponent(b.email) + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(buildMessageBody(b));
  }

  function copyToClipboard(text, cb) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { if (cb) cb(); }, function () { if (cb) cb(); });
    } else if (cb) {
      cb();
    }
  }

  /* Запоминаем, какие кнопки контактов (письмо/телефон/мессенджеры) уже
     нажимали по этой карточке, и подсвечиваем их галочкой при следующих
     открытиях страницы — чтобы не писать/звонить дважды по забывчивости. */
  function markChannelClick(rank, channel, chipEl) {
    var s = loadState();
    s[rank] = s[rank] || {};
    s[rank].clicks = s[rank].clicks || {};
    if (!s[rank].clicks[channel]) {
      s[rank].clicks[channel] = Date.now();
      saveState(s);
    }
    if (chipEl && !chipEl.classList.contains('is-clicked')) {
      chipEl.classList.add('is-clicked');
      chipEl.innerHTML = '&#10003; ' + chipEl.innerHTML;
    }
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

    var clicks = st.clicks || {};
    function clickedClass(channel) { return clicks[channel] ? ' is-clicked' : ''; }
    function clickedMark(channel) { return clicks[channel] ? '&#10003; ' : ''; }

    var contactsHtml = '';
    if (b.email) {
      contactsHtml += '<a class="by-chip mail js-channel-chip' + clickedClass('mail') + '" data-channel="mail" href="' + buildMailto(b) + '">'
        + clickedMark('mail') + '&#9993; Написать письмо</a>';
    } else {
      contactsHtml += '<span class="by-chip missing">email не найден</span>';
    }
    var digits = digitsOnly(b.phone);
    var isMobileLike = digits.length === 11 && digits.slice(1, 4) !== '800'; // 8-800 toll-free lines aren't personal messenger contacts
    if (b.phone) {
      contactsHtml += '<a class="by-chip js-channel-chip' + clickedClass('tel') + '" data-channel="tel" href="tel:+' + digits + '">'
        + clickedMark('tel') + '&#9742; ' + b.phone + '</a>';
      if (isMobileLike) {
        contactsHtml += '<a class="by-chip tg js-msg-chip js-channel-chip' + clickedClass('tg') + '" data-channel="tg"'
          + ' href="https://t.me/+' + digits + '" target="_blank" rel="noopener"'
          + ' title="Скопирует текст сообщения в буфер обмена и откроет чат в Telegram">' + clickedMark('tg') + 'Telegram</a>';
        contactsHtml += '<a class="by-chip wa js-msg-chip js-channel-chip' + clickedClass('wa') + '" data-channel="wa"'
          + ' href="https://wa.me/' + digits + '" target="_blank" rel="noopener"'
          + ' title="Скопирует текст сообщения в буфер обмена и откроет чат в WhatsApp">' + clickedMark('wa') + 'WhatsApp</a>';
        // У MAX нет прямых ссылок на контакт по номеру (в отличие от t.me/wa.me) —
        // копируем текст сообщения и открываем max.ru, чтобы найти контакт вручную.
        contactsHtml += '<button type="button" class="by-chip max js-max-chip js-channel-chip' + clickedClass('max') + '" data-channel="max"'
          + ' title="В MAX нет прямой ссылки на контакт по номеру — кнопка скопирует текст сообщения и откроет max.ru">' + clickedMark('max') + 'MAX</button>';
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

    var baseAt = Math.max(st.sentAt || 0, st.corrAt || 0);
    var dueBadge = '';
    var isDue = false;
    if (baseAt && !st.calledAt) {
      var due = nextBusinessDay(baseAt);
      if (Date.now() >= due) {
        isDue = true;
        dueBadge = '<span class="by-duebadge">&#128222; Пора позвонить</span>';
      }
    }
    if (st.sentAt) card.classList.add('is-sent');
    if (isDue) card.classList.add('is-due');

    var infoBits = [];
    if (st.sentAt) infoBits.push('письмо ' + fmtDateTime(st.sentAt));
    if (st.corrAt) infoBits.push('переписка (' + (APP_LABELS[st.corrApp] || 'приложение не выбрано') + ') ' + fmtDateTime(st.corrAt));
    if (st.calledAt) infoBits.push('прозвонили ' + fmtDate(st.calledAt));
    var sentInfo = infoBits.length ? '<span class="by-sentinfo">' + infoBits.join(' &middot; ') + '</span>' : '';

    var showCalled = !!(st.sentAt || st.corrAt);
    var showAppSelect = !!(st.corrAt || false);

    var hasContactHistory = !!(st.sentAt || st.corrAt || st.calledAt);
    var meetingRow;
    if (!hasContactHistory) {
      meetingRow = '';
    } else if (st.meeting) {
      meetingRow = '<div class="by-meeting-row">' +
        '<span class="by-meeting-badge">&#128197; Встреча: ' + st.meeting.date + ' ' + st.meeting.time + ' &middot; ' + st.meeting.place +
        ' <button type="button" class="by-meeting-edit js-meeting-edit">изменить</button></span>' +
        '<div class="by-meeting-form" id="mf-' + b.rank + '" hidden>' +
          '<input type="date" class="jm-date" value="' + st.meeting.date + '">' +
          '<input type="time" class="jm-time" value="' + st.meeting.time + '">' +
          '<input type="text" class="jm-place" placeholder="Место встречи" value="' + st.meeting.place + '">' +
          '<button type="button" class="jm-save">Сохранить</button>' +
          '<button type="button" class="jm-cancel">Отмена</button>' +
        '</div>' +
      '</div>';
    } else {
      meetingRow = '<div class="by-meeting-row">' +
        '<button type="button" class="by-meeting-btn js-meeting-open">&#128197; Назначить встречу</button>' +
        '<div class="by-meeting-form" id="mf-' + b.rank + '" hidden>' +
          '<input type="date" class="jm-date">' +
          '<input type="time" class="jm-time">' +
          '<input type="text" class="jm-place" placeholder="Место встречи">' +
          '<button type="button" class="jm-save">Сохранить</button>' +
          '<button type="button" class="jm-cancel">Отмена</button>' +
        '</div>' +
      '</div>';
    }

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
          '<label class="by-check"><input type="checkbox" class="js-corr" ' + (st.corrAt ? 'checked' : '') + '> Переписка с менеджером</label>' +
          (showAppSelect ? (
            '<select class="by-app-select js-app">' +
              '<option value="">Приложение…</option>' +
              Object.keys(APP_LABELS).map(function (k) {
                return '<option value="' + k + '"' + (st.corrApp === k ? ' selected' : '') + '>' + APP_LABELS[k] + '</option>';
              }).join('') +
            '</select>'
          ) : '') +
          (showCalled ? '<label class="by-check"><input type="checkbox" class="js-called" ' + (st.calledAt ? 'checked' : '') + '> Прозвонили</label>' : '') +
        '</div>' +
        (dueBadge || sentInfo) +
      '</div>' +
      meetingRow;

    card.querySelectorAll('.js-channel-chip').forEach(function (chip) {
      var channel = chip.dataset.channel;
      if (channel === 'max') return; // у MAX своя обработка ниже (копирование + временный текст)
      chip.addEventListener('click', function () {
        markChannelClick(b.rank, channel, chip);
        if (chip.classList.contains('js-msg-chip')) copyToClipboard(buildMessageBody(b));
      });
    });

    var maxChip = card.querySelector('.js-max-chip');
    if (maxChip) {
      maxChip.addEventListener('click', function () {
        markChannelClick(b.rank, 'max', maxChip);
        var originalLabel = maxChip.textContent;
        copyToClipboard(buildMessageBody(b), function () {
          window.open('https://max.ru/', '_blank', 'noopener');
          maxChip.textContent = 'Скопировано!';
          setTimeout(function () { maxChip.textContent = originalLabel; }, 1800);
        });
      });
    }

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

    var corrCb = card.querySelector('.js-corr');
    corrCb.addEventListener('change', function () {
      state = loadState();
      state[b.rank] = state[b.rank] || {};
      if (corrCb.checked) {
        state[b.rank].corrAt = Date.now();
      } else {
        delete state[b.rank].corrAt;
        delete state[b.rank].corrApp;
      }
      saveState(state);
      rerenderCard(b, state);
    });

    var appSelect = card.querySelector('.js-app');
    if (appSelect) {
      appSelect.addEventListener('change', function () {
        state = loadState();
        state[b.rank] = state[b.rank] || {};
        state[b.rank].corrApp = appSelect.value || undefined;
        saveState(state);
      });
    }

    var meetingForm = card.querySelector('.by-meeting-form');
    var openBtn = card.querySelector('.js-meeting-open');
    var editBtn = card.querySelector('.js-meeting-edit');
    if (openBtn) openBtn.addEventListener('click', function () { meetingForm.hidden = false; });
    if (editBtn) editBtn.addEventListener('click', function () { meetingForm.hidden = false; });
    var cancelBtn = card.querySelector('.jm-cancel');
    if (cancelBtn) cancelBtn.addEventListener('click', function () { meetingForm.hidden = true; });
    var saveBtn = card.querySelector('.jm-save');
    if (saveBtn) {
      saveBtn.addEventListener('click', function () {
        var date = card.querySelector('.jm-date').value;
        var time = card.querySelector('.jm-time').value;
        var place = card.querySelector('.jm-place').value.trim();
        if (!date || !time || !place) {
          alert('Укажите дату, время и место встречи.');
          return;
        }
        state = loadState();
        state[b.rank] = state[b.rank] || {};
        state[b.rank].meeting = { date: date, time: time, place: place, setAt: Date.now() };
        saveState(state);

        var text = 'Назначена встреча — ' + b.company + ' (#' + b.rank + ')\n'
          + 'Дата: ' + date + '\n'
          + 'Время: ' + time + '\n'
          + 'Место: ' + place
          + (b.contactName ? '\nКонтакт: ' + b.contactName : '');
        sendToTelegram(text);

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

    var exportBtn = document.getElementById('byExportBtn');
    if (exportBtn) exportBtn.addEventListener('click', exportBackup);

    var emailBtn = document.getElementById('byEmailBtn');
    if (emailBtn) emailBtn.addEventListener('click', emailBackup);

    var importInput = document.getElementById('byImportInput');
    if (importInput) {
      importInput.addEventListener('change', function () {
        var file = importInput.files && importInput.files[0];
        if (file) importBackupFile(file);
        importInput.value = '';
      });
    }

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
