/* Возрождение — сайт: мобильное меню, учёт визитов и форма обратной связи через Telegram-бота.
 *
 * ВНИМАНИЕ: токен бота ниже виден в исходном коде страницы всем посетителям сайта
 * (это открытый git-репозиторий на GitHub Pages). Это осознанный компромисс для теста
 * без бэкенда — GitHub Pages отдаёт только статику, серверного кода для скрытия токена нет.
 * Перед реальным использованием: смените токен через @BotFather (/revoke) и для продакшена
 * перенесите отправку сообщений на сервер/облачную функцию, где токен не виден клиенту.
 */
(function () {
  'use strict';

  var TELEGRAM_BOT_TOKEN = '8431645174:AAGTV2Xg4mpOKiqaKHR73pVBBKUDHm0D_yo';
  var TELEGRAM_CHAT_ID = '190404167'; // Erop (@goshva13) — из /start боту @aivintesting1986bot

  function sendToTelegram(text) {
    if (!TELEGRAM_CHAT_ID || TELEGRAM_CHAT_ID === 'REPLACE_WITH_CHAT_ID') {
      console.warn('[Возрождение] TELEGRAM_CHAT_ID не настроен — сообщение не отправлено:', text);
      return Promise.resolve(false);
    }
    var url = 'https://api.telegram.org/bot' + TELEGRAM_BOT_TOKEN + '/sendMessage'
      + '?chat_id=' + encodeURIComponent(TELEGRAM_CHAT_ID)
      + '&text=' + encodeURIComponent(text);
    // no-cors: нам не нужен ответ, только факт отправки GET-запроса (без ограничений CORS)
    return fetch(url, { method: 'GET', mode: 'no-cors' })
      .then(function () { return true; })
      .catch(function (err) { console.warn('[Возрождение] Telegram send failed', err); return false; });
  }

  /* ---------------- Мобильное меню ---------------- */
  function initNav() {
    var toggle = document.getElementById('navToggle');
    var menu = document.getElementById('navMobile');
    if (!toggle || !menu) return;
    toggle.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        menu.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ---------------- Учёт визитов (не чаще 1 раза в 3 минуты с одного устройства) ---------------- */
  function trackVisit() {
    var KEY = 'vozrozhdenie_last_visit_ping';
    var THROTTLE_MS = 3 * 60 * 1000;
    var now = Date.now();
    var last = 0;
    try { last = parseInt(localStorage.getItem(KEY) || '0', 10); } catch (e) {}
    if (now - last < THROTTLE_MS) return;
    try { localStorage.setItem(KEY, String(now)); } catch (e) {}

    var page = location.pathname + location.hash;
    var ref = document.referrer ? document.referrer : 'прямой заход';
    var text = 'Визит на сайт\nСтраница: ' + page + '\nИсточник: ' + ref
      + '\nВремя: ' + new Date().toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' }) + ' (МСК)';
    sendToTelegram(text);
  }

  /* ---------------- Форма обратной связи ---------------- */
  function initCallbackForm() {
    var form = document.getElementById('callbackForm');
    if (!form) return;
    var statusEl = document.getElementById('cfStatus');
    var submitBtn = document.getElementById('cfSubmit');

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = form.elements.name.value.trim();
      var contact = form.elements.contact.value.trim();

      if (!contact) {
        statusEl.textContent = 'Укажите телефон или мессенджер.';
        statusEl.className = 'cf-status err';
        form.elements.contact.focus();
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Отправляем…';

      var text = 'Заявка с сайта — просят перезвонить\n'
        + 'Имя: ' + (name || 'не указано') + '\n'
        + 'Контакт: ' + contact + '\n'
        + 'Страница: ' + location.pathname + location.hash + '\n'
        + 'Время: ' + new Date().toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' }) + ' (МСК)';

      sendToTelegram(text).then(function (ok) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Заказать звонок';
        if (ok) {
          statusEl.textContent = 'Спасибо! Мы перезвоним в ближайшее время.';
          statusEl.className = 'cf-status';
          form.reset();
        } else {
          statusEl.textContent = 'Форма пока не настроена — позвоните нам напрямую по телефону ниже.';
          statusEl.className = 'cf-status err';
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initNav();
    initCallbackForm();
    trackVisit();
  });
})();
