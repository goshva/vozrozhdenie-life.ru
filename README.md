# vozrozhdenie-life.ru

Лендинг жилого района «Возрождение» (Липецкая область, с. Преображеновка) для публикации через GitHub Pages.

## Структура

- `index.html` — вся страница
- `assets/css/style.css` — стили
- `assets/img/` — фотографии и логотип
- `assets/video/` — два видео с площадки
- `assets/docs/` — ПЗЗ и кадастровая карта (PDF, скачиваемые ссылки)
- `CNAME` — домен для GitHub Pages (vozrozhdenie-life.ru)

## Публикация на GitHub Pages

1. В репозитории: **Settings → Pages → Build and deployment → Source: Deploy from a branch**.
2. Branch: `main`, папка `/ (root)`.
3. Сохранить — через 1–2 минуты сайт будет доступен на `https://<user>.github.io/vozrozhdenie-life.ru/`.
4. Для кастомного домена `vozrozhdenie-life.ru` (уже задан в `CNAME`): в настройках DNS-регистратора добавить записи, указанные GitHub в том же разделе Settings → Pages (обычно `A`-записи на IP GitHub Pages или `CNAME` на `<user>.github.io`), затем в том же разделе включить **Enforce HTTPS**.

## Локальный просмотр

Открыть `index.html` в браузере, либо `python -m http.server` из этой папки.

## Источники контента

Текст и часть изображений — из презентаций и материалов проекта, изображения увеличены/сжаты для веба. Логотип — исходный `logo.jpg` владельца, автоматически обрезан по контенту и убран в прозрачность.
