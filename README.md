# vozrozhdenie-life.ru

Лендинг жилого района «Возрождение» (Липецкая область, с. Преображеновка) для публикации через GitHub Pages.

## Структура

- `index.html` — главная страница
- `teaser.html` — инвестиционный тизер (самостоятельная страница, не Claude-артефакт)
- `investors.html` — внутренний список инвесторов/партнёров с CRM-трекером на localStorage (`noindex`)
- `assets/css/` — стили (`style.css` общий, `investors.css` только для страницы инвесторов)
- `assets/js/` — `main.js` (мобильное меню, визиты и форма обратной связи через Telegram), `investors.js` (трекер статусов)
- `assets/img/` — фотографии и логотип
- `assets/video/` — два видео с площадки
- `assets/docs/` — ПЗЗ и кадастровая карта (PDF, скачиваемые ссылки)
- `robots.txt`, `sitemap.xml` — для индексации на `https://goshva.github.io/vozrozhdenie-life.ru/`

Кастомный домен не используется — канонический адрес сайта: `https://goshva.github.io/vozrozhdenie-life.ru/` (файл `CNAME` удалён).

## Публикация на GitHub Pages

1. В репозитории: **Settings → Pages → Build and deployment → Source: Deploy from a branch**.
2. Branch: `main`, папка `/ (root)`.
3. Сохранить — через 1–2 минуты сайт будет доступен на `https://goshva.github.io/vozrozhdenie-life.ru/`.

## Локальный просмотр

Открыть `index.html` в браузере, либо `python -m http.server` из этой папки.

## Источники контента

Текст и часть изображений — из презентаций и материалов проекта, изображения увеличены/сжаты для веба. Логотип — исходный `logo.jpg` владельца, автоматически обрезан по контенту и убран в прозрачность.
