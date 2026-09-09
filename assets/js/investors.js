/* Возрождение — трекер инвесторов: статус и заметки сохраняются в localStorage браузера. */
(function () {
  'use strict';

  var STATUSES = [
    { v: 'none', l: 'Не начато' },
    { v: 'contacted', l: 'Написали' },
    { v: 'replied', l: 'Ответили' },
    { v: 'meeting', l: 'Встреча/звонок' },
    { v: 'declined', l: 'Отказ' }
  ];
  var KEY = 'vozrozhdenie_investors_v1';

  function loadState() {
    try {
      var raw = localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) { return {}; }
  }
  function saveState(state) {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }

  document.addEventListener('DOMContentLoaded', function () {
    var state = loadState();
    var selects = document.querySelectorAll('select.inv-status');
    var notes = document.querySelectorAll('textarea.inv-note');

    selects.forEach(function (sel) {
      STATUSES.forEach(function (s) {
        var opt = document.createElement('option');
        opt.value = s.v; opt.textContent = s.l;
        sel.appendChild(opt);
      });
      var id = sel.getAttribute('data-id');
      var val = (state[id] && state[id].status) || 'none';
      sel.value = val;
      sel.setAttribute('data-s', val);
      sel.addEventListener('change', function () {
        state[id] = state[id] || {};
        state[id].status = sel.value;
        sel.setAttribute('data-s', sel.value);
        saveState(state);
        updateProgress();
      });
    });

    notes.forEach(function (ta) {
      var id = ta.getAttribute('data-id');
      ta.value = (state[id] && state[id].note) || '';
      ta.addEventListener('input', function () {
        state[id] = state[id] || {};
        state[id].note = ta.value;
        saveState(state);
      });
    });

    function updateProgress() {
      var total = selects.length;
      var active = 0;
      selects.forEach(function (sel) { if (sel.value !== 'none') active++; });
      var pct = total ? Math.round(active / total * 100) : 0;
      var fill = document.getElementById('invProgressFill');
      var lbl = document.getElementById('invProgressLbl');
      if (fill) fill.style.width = pct + '%';
      if (lbl) lbl.textContent = active + ' / ' + total + ' в работе';
    }
    updateProgress();

    var resetBtn = document.getElementById('invResetBtn');
    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        if (!confirm('Сбросить все отметки и заметки по инвесторам?')) return;
        state = {};
        saveState(state);
        selects.forEach(function (sel) { sel.value = 'none'; sel.setAttribute('data-s', 'none'); });
        notes.forEach(function (ta) { ta.value = ''; });
        updateProgress();
      });
    }
  });
})();
