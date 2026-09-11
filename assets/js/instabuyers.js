/* Возрождение — поиск покупателей в Instagram: рендер карточек аккаунтов,
   копирование текста для директа, чекбоксы "написали"/"переписка"/"созвонились"
   с напоминанием на следующий рабочий день. Логика зеркалит assets/js/buyers.js
   (тот же трекер для email/телефонной базы), адаптированную под Instagram:
   основной канал — директ, а не письмо; вместо "письмо не дошло" — "аккаунт
   недоступен/удалён". Хранится только в этом браузере (свой ключ localStorage,
   отдельный от buyers.js, чтобы отметки не пересекались). */
(function () {
  'use strict';

  var KEY = 'vozrozhdenie_instabuyers_mailer_v1';
  var SITE = 'https://goshva.github.io/vozrozhdenie-life.ru';

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

  var CATEGORY_LABELS = {
    developer: 'Девелопер', izhs: 'Застройщик ИЖС', investor: 'Инвестор'
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

  /* ---------------- Резервная копия отметок (как на странице buyers.html) */
  var BACKUP_EMAIL = 'sha.egor@gmail.ru';

  function pad2(n) { return (n < 10 ? '0' : '') + n; }

  function backupFileName() {
    var d = new Date();
    return 'vozrozhdenie-instabuyers-backup-' + d.getFullYear() + pad2(d.getMonth() + 1) + pad2(d.getDate())
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
    var el = document.getElementById('ibBackupStatus');
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
    var subject = 'Возрождение — резервная копия отметок Instagram-покупателей';
    var body;
    if (compactJson.length > 1800) {
      var filename = backupFileName();
      triggerFileDownload(JSON.stringify(payload, null, 2), filename);
      body = 'Копия отметок слишком большая, чтобы поместиться в тело письма — она только что скачалась '
        + 'файлом "' + filename + '". Прикрепите этот файл к письму вручную перед отправкой.';
    } else {
      body = 'Резервная копия отметок Instagram-покупателей (JSON). Чтобы восстановить на другом устройстве — '
        + 'сохраните текст ниже в .json-файл и загрузите его кнопкой "Загрузить копию" на странице:\n\n'
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
      ['dmAt', 'corrAt', 'calledAt'].forEach(function (f) {
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

      var list = document.getElementById('ibList');
      list.innerHTML = '';
      var frag = document.createDocumentFragment();
      allAccounts.forEach(function (b) { frag.appendChild(renderCard(b, merged)); });
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
    while (d.getDay() === 0 || d.getDay() === 6) {
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
    var name = b.name || ('@' + b.handle);
    return [
      'Здравствуйте! Меня зовут Максим Игоревич, ООО «Экспострой» — собственник проекта «Возрождение» в Липецкой области.',
      '',
      'Увидел ' + name + ' и хочу предложить ознакомиться с готовым девелоперским активом: 208 кадастровых участков (99 га) на берегу реки Воронеж, с оформленной концепцией коттеджного посёлка. Продаётся целиком одному инвестору.',
      '',
      'Инвестиционный тизер: ' + SITE + '/teaser.html',
      'PDF-версия для пересылки: ' + SITE + '/assets/docs/vozrozhdenie-teaser.pdf',
      '',
      'Буду рад обсудить детали по телефону или в мессенджере.',
      '',
      'С уважением, Максим Игоревич',
      '+7 910 351-13-33'
    ].join('\n');
  }

  function copyToClipboard(text, cb) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { if (cb) cb(); }, function () { if (cb) cb(); });
    } else if (cb) {
      cb();
    }
  }

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
    card.className = 'ib-card';
    card.dataset.rank = b.rank;
    card.dataset.search = (b.name + ' ' + b.handle + ' ' + b.region + ' ' + b.profile).toLowerCase();
    card.dataset.priority = b.priority;
    card.dataset.category = b.category || '';

    var clicks = st.clicks || {};
    function clickedClass(channel) { return clicks[channel] ? ' is-clicked' : ''; }
    function clickedMark(channel) { return clicks[channel] ? '&#10003; ' : ''; }

    // Прямых ссылок на "написать в директ конкретному аккаунту" у Instagram
    // нет — открываем профиль и одновременно копируем готовый текст в буфер,
    // чтобы вставить его в чат вручную (как и кнопка MAX на странице buyers.html).
    var contactsHtml = '';
    contactsHtml += '<a class="ib-chip insta js-msg-chip js-channel-chip' + clickedClass('insta') + '" data-channel="insta"'
      + ' href="' + b.profileUrl + '" target="_blank" rel="noopener"'
      + ' title="Скопирует текст сообщения в буфер обмена и откроет профиль в Instagram">'
      + clickedMark('insta') + '&#128247; @' + b.handle + '</a>';

    var digits = digitsOnly(b.phone);
    var isMobileLike = digits.length === 11 && digits.slice(1, 4) !== '800';
    if (b.phone) {
      contactsHtml += '<a class="ib-chip js-channel-chip' + clickedClass('tel') + '" data-channel="tel" href="tel:+' + digits + '">'
        + clickedMark('tel') + '&#9742; ' + b.phone + '</a>';
      if (isMobileLike) {
        contactsHtml += '<a class="ib-chip tg js-msg-chip js-channel-chip' + clickedClass('tg') + '" data-channel="tg"'
          + ' href="https://t.me/+' + digits + '" target="_blank" rel="noopener"'
          + ' title="Скопирует текст сообщения в буфер обмена и откроет чат в Telegram">' + clickedMark('tg') + 'Telegram</a>';
        contactsHtml += '<a class="ib-chip wa js-msg-chip js-channel-chip' + clickedClass('wa') + '" data-channel="wa"'
          + ' href="https://wa.me/' + digits + '" target="_blank" rel="noopener"'
          + ' title="Скопирует текст сообщения в буфер обмена и откроет чат в WhatsApp">' + clickedMark('wa') + 'WhatsApp</a>';
        contactsHtml += '<button type="button" class="ib-chip max js-max-chip js-channel-chip' + clickedClass('max') + '" data-channel="max"'
          + ' title="В MAX нет прямой ссылки на контакт по номеру — кнопка скопирует текст сообщения и откроет max.ru">' + clickedMark('max') + 'MAX</button>';
      }
    }
    if (b.website) {
      var host = b.website.replace(/^https?:\/\//, '').replace(/\/$/, '');
      contactsHtml += '<a class="ib-chip" href="' + b.website + '" target="_blank" rel="noopener">' + host + '</a>';
    }

    var contactPerson = b.contactName
      ? '<div class="ib-meta">' + b.contactName + (b.contactPosition ? ' — ' + b.contactPosition : '') + '</div>'
      : '';
    var catBadge = CATEGORY_LABELS[b.category]
      ? '<span class="ib-catbadge">' + CATEGORY_LABELS[b.category] + '</span>'
      : '';

    // "Аккаунт удалён/не существует" — Instagram-аналог "письмо не дошло":
    // такой контакт не запускает напоминание позвонить и не считается
    // историей контакта для показа блока "Назначить встречу".
    var baseAt = Math.max(st.gone ? 0 : (st.dmAt || 0), st.corrAt || 0);
    var dueBadge = '';
    var isDue = false;
    if (baseAt && !st.calledAt) {
      var due = nextBusinessDay(baseAt);
      if (Date.now() >= due) {
        isDue = true;
        dueBadge = '<span class="ib-duebadge">&#128222; Пора позвонить</span>';
      }
    }
    var goneBadge = st.gone ? '<span class="ib-bouncebadge">&#9888; Аккаунт недоступен</span>' : '';
    if (st.dmAt) card.classList.add('is-sent');
    if (isDue && !st.refused) card.classList.add('is-due');
    if (st.gone) card.classList.add('is-bounced');
    if (st.refused) card.classList.add('is-refused');

    var infoBits = [];
    if (st.dmAt) infoBits.push('директ ' + fmtDateTime(st.dmAt) + (st.gone ? ' — аккаунт удалён/не существует' : ''));
    if (st.corrAt) infoBits.push('переписка (' + (APP_LABELS[st.corrApp] || 'приложение не выбрано') + ') ' + fmtDateTime(st.corrAt));
    if (st.calledAt) infoBits.push('прозвонили ' + fmtDate(st.calledAt));
    var sentInfo = infoBits.length ? '<span class="ib-sentinfo">' + infoBits.join(' &middot; ') + '</span>' : '';

    var showCalled = !!(st.dmAt || st.corrAt);
    var showAppSelect = !!(st.corrAt || false);

    var hasContactHistory = !!((st.dmAt && !st.gone) || st.corrAt || st.calledAt);
    var meetingRow;
    if (!hasContactHistory) {
      meetingRow = '';
    } else if (st.meeting) {
      meetingRow = '<div class="ib-meeting-row">' +
        '<span class="ib-meeting-badge">&#128197; Встреча: ' + st.meeting.date + ' ' + st.meeting.time + ' &middot; ' + st.meeting.place +
        ' <button type="button" class="ib-meeting-edit js-meeting-edit">изменить</button></span>' +
        '<div class="ib-meeting-form" id="mf-' + b.rank + '" hidden>' +
          '<input type="date" class="jm-date" value="' + st.meeting.date + '">' +
          '<input type="time" class="jm-time" value="' + st.meeting.time + '">' +
          '<input type="text" class="jm-place" placeholder="Место встречи" value="' + st.meeting.place + '">' +
          '<button type="button" class="jm-save">Сохранить</button>' +
          '<button type="button" class="jm-cancel">Отмена</button>' +
        '</div>' +
      '</div>';
    } else {
      meetingRow = '<div class="ib-meeting-row">' +
        '<button type="button" class="ib-meeting-btn js-meeting-open">&#128197; Назначить встречу</button>' +
        '<div class="ib-meeting-form" id="mf-' + b.rank + '" hidden>' +
          '<input type="date" class="jm-date">' +
          '<input type="time" class="jm-time">' +
          '<input type="text" class="jm-place" placeholder="Место встречи">' +
          '<button type="button" class="jm-save">Сохранить</button>' +
          '<button type="button" class="jm-cancel">Отмена</button>' +
        '</div>' +
      '</div>';
    }

    var refuseBadge = st.refused
      ? '<span class="ib-refusebadge">&#10006; Прямой отказ' + (st.refusedAt ? ' &middot; ' + fmtDate(st.refusedAt) : '') + '</span>'
      : '';

    card.innerHTML =
      '<div class="ib-top">' +
        '<div>' +
          '<div class="ib-name"><span class="ib-rank">#' + b.rank + '</span> ' + (b.name || '@' + b.handle) + ' <span class="ib-handle">@' + b.handle + '</span></div>' +
          '<div class="ib-meta">' + b.region + ' &middot; ' + b.profile + '</div>' +
          contactPerson +
          catBadge +
        '</div>' +
        '<span class="ib-badge ' + priorityClass(b.priority) + '">' + b.priority + '</span>' +
      '</div>' +
      '<label class="ib-check ib-check-refuse"><input type="checkbox" class="js-refused" ' + (st.refused ? 'checked' : '') + '> Прямой отказ</label>' +
      refuseBadge +
      '<div class="ib-card-body"' + (st.refused ? ' hidden' : '') + '>' +
        '<div class="ib-contacts">' + contactsHtml + '</div>' +
        '<div class="ib-bottom">' +
          '<div class="ib-checks">' +
            '<label class="ib-check"><input type="checkbox" class="js-sent" ' + (st.dmAt ? 'checked' : '') + '> Написали в директ</label>' +
            (st.dmAt ? '<label class="ib-check ib-check-warn"><input type="checkbox" class="js-bounced" ' + (st.gone ? 'checked' : '') + '> Аккаунт удалён/не существует</label>' : '') +
            '<label class="ib-check"><input type="checkbox" class="js-corr" ' + (st.corrAt ? 'checked' : '') + '> Переписка идёт</label>' +
            (showAppSelect ? (
              '<select class="ib-app-select js-app">' +
                '<option value="">Приложение…</option>' +
                Object.keys(APP_LABELS).map(function (k) {
                  return '<option value="' + k + '"' + (st.corrApp === k ? ' selected' : '') + '>' + APP_LABELS[k] + '</option>';
                }).join('') +
              '</select>'
            ) : '') +
            (showCalled ? '<label class="ib-check"><input type="checkbox" class="js-called" ' + (st.calledAt ? 'checked' : '') + '> Прозвонили/созвонились</label>' : '') +
          '</div>' +
          (goneBadge + (dueBadge || sentInfo)) +
        '</div>' +
        meetingRow +
      '</div>';

    card.querySelectorAll('.js-channel-chip').forEach(function (chip) {
      var channel = chip.dataset.channel;
      if (channel === 'max') return;
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

    var refusedCb = card.querySelector('.js-refused');
    refusedCb.addEventListener('change', function () {
      state = loadState();
      state[b.rank] = state[b.rank] || {};
      if (refusedCb.checked) {
        state[b.rank].refused = true;
        state[b.rank].refusedAt = Date.now();
      } else {
        delete state[b.rank].refused;
        delete state[b.rank].refusedAt;
      }
      saveState(state);
      rerenderCard(b, state);
    });

    var sentCb = card.querySelector('.js-sent');
    sentCb.addEventListener('change', function () {
      state = loadState();
      state[b.rank] = state[b.rank] || {};
      if (sentCb.checked) {
        state[b.rank].dmAt = Date.now();
      } else {
        delete state[b.rank].dmAt;
        delete state[b.rank].calledAt;
        delete state[b.rank].gone;
        delete state[b.rank].goneAt;
      }
      saveState(state);
      rerenderCard(b, state);
    });

    var goneCb = card.querySelector('.js-bounced');
    if (goneCb) {
      goneCb.addEventListener('change', function () {
        state = loadState();
        state[b.rank] = state[b.rank] || {};
        if (goneCb.checked) {
          state[b.rank].gone = true;
          state[b.rank].goneAt = Date.now();
        } else {
          delete state[b.rank].gone;
          delete state[b.rank].goneAt;
        }
        saveState(state);
        rerenderCard(b, state);
      });
    }

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

    var meetingForm = card.querySelector('.ib-meeting-form');
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

        var text = 'Назначена встреча (Instagram) — ' + (b.name || '@' + b.handle) + ' (#' + b.rank + ')\n'
          + 'Дата: ' + date + '\n'
          + 'Время: ' + time + '\n'
          + 'Место: ' + place
          + '\nInstagram: ' + b.profileUrl;
        sendToTelegram(text);

        rerenderCard(b, state);
      });
    }

    return card;
  }

  function rerenderCard(b, state) {
    var old = document.querySelector('.ib-card[data-rank="' + b.rank + '"]');
    if (!old) return;
    var fresh = renderCard(b, state);
    old.replaceWith(fresh);
    updateStats();
  }

  var allAccounts = [];

  function updateStats() {
    var state = loadState();
    var total = allAccounts.length;
    var sent = 0, due = 0;
    allAccounts.forEach(function (b) {
      var st = state[b.rank];
      if (st && st.dmAt) {
        sent++;
        if (!st.calledAt && Date.now() >= nextBusinessDay(st.dmAt)) due++;
      }
    });
    ['ibTotal', 'ibTotal2', 'ibTotal3'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.textContent = total;
    });
    var elSent = document.getElementById('ibSent');
    var elDue = document.getElementById('ibDue');
    var elLeft = document.getElementById('ibLeft');
    if (elSent) elSent.textContent = sent;
    if (elDue) elDue.textContent = due;
    if (elLeft) elLeft.textContent = total - sent;
  }

  var FILTER_KEY = 'vozrozhdenie_instabuyers_filters_v1';

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
      q: document.getElementById('ibSearch').value || '',
      prio: document.getElementById('ibPrioFilter').value || '',
      status: document.getElementById('ibStatusFilter').value || '',
      category: document.getElementById('ibCategoryFilter').value || ''
    };
  }

  function updateFilterBadge(vals) {
    var count = (vals.q ? 1 : 0) + (vals.prio ? 1 : 0) + (vals.status ? 1 : 0) + (vals.category ? 1 : 0);
    var badge = document.getElementById('ibFilterBadge');
    var clearBtn = document.getElementById('ibClearFiltersBtn');
    if (badge) { badge.hidden = count === 0; badge.textContent = count; }
    if (clearBtn) clearBtn.hidden = count === 0;
  }

  function applyFilters() {
    var vals = currentFilterValues();
    var q = vals.q.trim().toLowerCase();
    var prio = vals.prio;
    var statusFilter = vals.status;
    var state = loadState();
    var cards = document.querySelectorAll('.ib-card');
    var visible = 0;
    cards.forEach(function (card) {
      var rank = card.dataset.rank;
      var matchesQ = !q || card.dataset.search.indexOf(q) !== -1;
      var matchesPrio = !prio || card.dataset.priority === prio;
      var st = state[rank] || {};
      var isSent = !!st.dmAt;
      var isDue = isSent && !st.calledAt && Date.now() >= nextBusinessDay(st.dmAt);
      var matchesStatus = true;
      if (statusFilter === 'not-sent') matchesStatus = !isSent;
      else if (statusFilter === 'sent') matchesStatus = isSent;
      else if (statusFilter === 'due') matchesStatus = isDue;
      var matchesCategory = !vals.category || card.dataset.category === vals.category;
      var show = matchesQ && matchesPrio && matchesStatus && matchesCategory;
      card.hidden = !show;
      if (show) visible++;
    });
    var empty = document.getElementById('ibEmpty');
    if (empty) empty.hidden = visible !== 0;
    var countEl = document.getElementById('ibVisibleCount');
    if (countEl) countEl.textContent = visible;
    updateFilterBadge(vals);

    var prefs = loadFilterPrefs();
    prefs.q = vals.q; prefs.prio = vals.prio; prefs.status = vals.status; prefs.category = vals.category;
    saveFilterPrefs(prefs);
  }

  function setPanelOpen(open) {
    var panel = document.getElementById('ibFilterPanel');
    var toggle = document.getElementById('ibToggleBtn');
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    var prefs = loadFilterPrefs();
    prefs.open = open;
    saveFilterPrefs(prefs);
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (typeof INSTABUYERS === 'undefined') return;
    allAccounts = INSTABUYERS;
    var state = loadState();
    var list = document.getElementById('ibList');
    var frag = document.createDocumentFragment();
    allAccounts.forEach(function (b) { frag.appendChild(renderCard(b, state)); });
    list.appendChild(frag);
    updateStats();

    var prefs = loadFilterPrefs();
    if (prefs.q) document.getElementById('ibSearch').value = prefs.q;
    if (prefs.prio) document.getElementById('ibPrioFilter').value = prefs.prio;
    if (prefs.status) document.getElementById('ibStatusFilter').value = prefs.status;
    if (prefs.category) document.getElementById('ibCategoryFilter').value = prefs.category;
    var hasActiveFilters = !!(prefs.q || prefs.prio || prefs.status || prefs.category);
    setPanelOpen(prefs.open === true || hasActiveFilters);
    applyFilters();

    document.getElementById('ibSearch').addEventListener('input', applyFilters);
    document.getElementById('ibPrioFilter').addEventListener('change', applyFilters);
    document.getElementById('ibStatusFilter').addEventListener('change', applyFilters);
    document.getElementById('ibCategoryFilter').addEventListener('change', applyFilters);

    document.getElementById('ibToggleBtn').addEventListener('click', function () {
      var panel = document.getElementById('ibFilterPanel');
      setPanelOpen(panel.hidden);
    });

    document.getElementById('ibClearFiltersBtn').addEventListener('click', function () {
      document.getElementById('ibSearch').value = '';
      document.getElementById('ibPrioFilter').value = '';
      document.getElementById('ibStatusFilter').value = '';
      document.getElementById('ibCategoryFilter').value = '';
      applyFilters();
    });

    var exportBtn = document.getElementById('ibExportBtn');
    if (exportBtn) exportBtn.addEventListener('click', exportBackup);

    var emailBtn = document.getElementById('ibEmailBtn');
    if (emailBtn) emailBtn.addEventListener('click', emailBackup);

    var importInput = document.getElementById('ibImportInput');
    if (importInput) {
      importInput.addEventListener('change', function () {
        var file = importInput.files && importInput.files[0];
        if (file) importBackupFile(file);
        importInput.value = '';
      });
    }

    document.getElementById('ibResetBtn').addEventListener('click', function () {
      if (!confirm('Сбросить все отметки по всем ' + allAccounts.length + ' записям? (Фильтры это не затронет.)')) return;
      saveState({});
      list.innerHTML = '';
      var frag2 = document.createDocumentFragment();
      allAccounts.forEach(function (b) { frag2.appendChild(renderCard(b, {})); });
      list.appendChild(frag2);
      updateStats();
      applyFilters();
    });
  });
})();
