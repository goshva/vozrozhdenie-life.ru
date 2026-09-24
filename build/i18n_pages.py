# -*- coding: utf-8 -*-
"""Сборка языковых версий сайта: index.html, teaser.html → ko/, zh/, vi/.

Запуск из корня репозитория:
    python build/i18n_pages.py

Русские страницы — единственный источник вёрстки. Скрипт:
  1. подставляет переводы из build/i18n_strings.py;
  2. правит пути (assets/ → ../assets/), lang, canonical, og:locale, ссылку на PDF;
  3. добавляет национальные настройки шрифтов и типографики;
  4. вставляет блок «для иностранного инвестора»;
  5. проверяет, что в видимом тексте не осталось кириллицы (иначе — ошибка).
После правки русских страниц: добавить новые фразы в i18n_strings.py и перезапустить.
"""
import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_strings import ROWS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://vozrozhdenie-life.ru/"
LANGS = ["ko", "zh", "vi"]
PAGES = ["index.html", "teaser.html"]
CYR = re.compile(r"[А-Яа-яЁё]")

LOCALE = {"ko": "ko_KR", "zh": "zh_CN", "vi": "vi_VN"}

# Шрифты и типографика по языкам.
#  ko — Noto Sans/Serif KR, word-break:keep-all (перенос по словам-эоджолям, как принято в корейском наборе);
#  zh — без Google Fonts (в КНР они блокируются и тормозят загрузку) — системные PingFang / YaHei;
#  vi — исходные шрифты сайта поддерживают вьетнамскую диакритику, нужна только увеличенная интерлиньяж.
SERIF_SEL = ("h1,h2,h3,.brand .name,.brandrow .name,.statcell .n,.htype .n,.pc-price,.urgencybox h3,"
             ".stat .num,.scard .n,.price,.dealband h2,td:first-child")
FONT_CSS = {
    "ko": ("<link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700"
           "&family=Noto+Serif+KR:wght@500;600&display=swap\">\n"
           "<style>\n"
           "  body{ font-family:'Public Sans','Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic',sans-serif; word-break:keep-all; }\n"
           f"  {SERIF_SEL}{{ font-family:'Fraunces','Noto Serif KR','Nanum Myeongjo',serif; }}\n"
           "  em,.hero h1 em{ font-style:normal; }\n"
           "  .kicker,.eyebrow,th{ letter-spacing:.02em; }\n"
           "</style>"),
    "zh": ("<style>\n"
           "  body{ font-family:system-ui,-apple-system,'PingFang SC','Hiragino Sans GB','Microsoft YaHei','Noto Sans SC',sans-serif; line-break:strict; }\n"
           f"  {SERIF_SEL}{{ font-family:'Songti SC','Noto Serif SC','SimSun',serif; font-weight:700; }}\n"
           "  .mono,td.num,.pricecut-new,.surl{ font-family:ui-monospace,'SFMono-Regular',Consolas,monospace; }\n"
           "  em,.hero h1 em{ font-style:normal; }\n"
           "  .kicker,.eyebrow,th{ letter-spacing:.04em; }\n"
           "</style>"),
    "vi": ("<style>\n"
           "  body{ line-height:1.65; }\n"
           "  h1,h2,h3{ line-height:1.2; }\n"
           "</style>"),
}

# Блок «для иностранного инвестора» — с учётом правил вывода капитала в стране покупателя.
FOREIGN_NOTE = {
    "ko": ("해외 투자자 안내",
           "외국인 및 외국 법인의 러시아 토지 취득은 러시아 연방 법령에 따르며, 러시아 현지 법인(SPV)을 통한 인수 구조를 협의할 수 있습니다. "
           "필요한 인허가 절차, 결제 통화 및 결제 방식은 개별 협의합니다. 한국 거주자의 해외 부동산 취득은 외국환거래법상 신고 대상일 수 있으므로 "
           "외국환은행 및 전문가와 사전 확인을 권장합니다. 모든 자료의 원본은 러시아어이며, 한국어·영어로 설명해 드릴 수 있습니다."),
    "zh": ("境外投资者须知",
           "外国自然人及法人在俄罗斯取得土地须遵守俄罗斯联邦法律，可协商通过俄罗斯本地公司（SPV）进行收购。"
           "所需审批程序、结算币种（包括人民币）及支付方式一事一议。中国境内企业开展境外投资须依法办理发改委、商务部备案及外汇登记，"
           "建议事先咨询专业顾问。全部原始文件为俄文，可提供中文及英文说明。"),
    "vi": ("Lưu ý dành cho nhà đầu tư nước ngoài",
           "Việc cá nhân và pháp nhân nước ngoài nhận quyền sở hữu đất tại Nga tuân theo pháp luật Liên bang Nga; có thể thỏa thuận cấu trúc mua thông qua pháp nhân tại Nga (SPV). "
           "Thủ tục phê duyệt, đồng tiền và phương thức thanh toán được thỏa thuận riêng. Doanh nghiệp Việt Nam đầu tư ra nước ngoài cần có Giấy chứng nhận đăng ký đầu tư ra nước ngoài "
           "và đăng ký giao dịch ngoại hối theo quy định — khuyến nghị tham vấn chuyên gia trước. Hồ sơ gốc bằng tiếng Nga; chúng tôi có thể giải thích bằng tiếng Việt và tiếng Anh."),
}

SWITCH_LABEL = {"ru": "RU", "ko": "한국어", "zh": "中文", "vi": "Tiếng Việt"}


def lang_switcher(page, lang):
    links = []
    for l in ["ru"] + LANGS:
        if l == lang:
            href = page
        elif lang == "ru":
            href = f"{l}/{page}"
        elif l == "ru":
            href = f"../{page}"
        else:
            href = f"../{l}/{page}"
        cur = ' aria-current="page"' if l == lang else ""
        links.append(f'<a href="{href}" hreflang="{l}" lang="{l}"{cur}>{SWITCH_LABEL[l]}</a>')
    return '<div class="langsw" role="navigation" aria-label="Language">' + "".join(links) + "</div>"


def apply_translations(html, lang):
    rows = sorted(ROWS, key=lambda r: len(r["ru"]), reverse=True)
    for r in rows:
        ru, tr = r["ru"], r[lang]
        if ru.startswith(("<", '"')) or len(ru) > 30:
            html = html.replace(ru, tr)
        else:
            html = re.sub(r">(\s*)" + re.escape(ru) + r"(\s*)<", lambda m: ">" + m.group(1) + tr + m.group(2) + "<", html)
            html = html.replace(f'"{ru}"', f'"{tr}"')
    return html


def localize(page, lang):
    html = open(os.path.join(ROOT, page), encoding="utf-8").read()

    # Цена без «зачёркнутой» старой цены и бейджа скидки: для азиатских инвесторов подача
    # «было/стало, −36%» читается как вынужденная распродажа (потеря «лица» актива).
    html = re.sub(r'\s*<span class="pricecut-old">.*?</span>\s*<svg.*?</svg>', "", html, flags=re.S)
    html = re.sub(r'\s*<span class="pricecut-badge">.*?</span>', "", html, flags=re.S)

    # Блок для иностранного инвестора
    title, body = FOREIGN_NOTE[lang]
    if page == "teaser.html":
        note = (f'<div class="chartcard" style="margin-top:28px"><div class="kicker">{title}</div>'
                f'<p style="margin:0;font-size:14.5px">{body}</p></div>\n\n    <div class="contact">')
        html = html.replace('<div class="contact">', note, 1)
    else:
        note = (f'<div class="callout" style="margin-top:18px"><b>{title}.</b> {body}</div>\n\n'
                '    <div class="urgencybox reveal">')
        html = html.replace('<div class="urgencybox reveal">', note, 1)

    html = apply_translations(html, lang)

    # Переключатель языка
    html = re.sub(r'<div class="langsw".*?</div>', lambda m: lang_switcher(page, lang), html, count=1, flags=re.S)

    # <head>: язык, канонический адрес, локаль, шрифты
    html = html.replace('<html lang="ru">', f'<html lang="{lang}">', 1)
    path = "" if page == "index.html" else page
    html = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{SITE}{lang}/{path}">', html, count=1)
    html = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{SITE}{lang}/{path}">', html, count=1)
    html = html.replace('"url": "https://vozrozhdenie-life.ru/"', f'"url": "{SITE}{lang}/"')
    if 'og:locale' in html:
        html = html.replace('content="ru_RU"', f'content="{LOCALE[lang]}"')
    else:
        html = html.replace('<meta property="og:type"', f'<meta property="og:locale" content="{LOCALE[lang]}">\n<meta property="og:type"', 1)
    if lang == "zh":
        html = re.sub(r'<link rel="preconnect" href="https://fonts\.g[^>]*>\n?', "", html)
        html = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n?', "", html)
    html = html.replace("</head>", FONT_CSS[lang] + "\n</head>", 1)

    # Пути к ресурсам (страница лежит на уровень глубже)
    html = re.sub(r'(href|src)="assets/', r'\1="../assets/', html)
    html = html.replace("url('assets/", "url('../assets/")
    html = html.replace("../assets/docs/vozrozhdenie-teaser.pdf", f"../assets/docs/vozrozhdenie-teaser-{lang}.pdf")
    return html


class VisibleText(HTMLParser):
    """Собирает видимый текст и значимые атрибуты (alt, content, aria-label, placeholder, title)."""
    ATTRS = {"alt", "content", "aria-label", "placeholder", "title", "data-label"}

    def __init__(self):
        super().__init__()
        self.skip = 0
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        for k, v in attrs:
            if k in self.ATTRS and v:
                self.out.append(v)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.out.append(data.strip())


def leftovers(html):
    p = VisibleText()
    p.feed(html)
    bad = [t for t in p.out if CYR.search(t)]
    # JSON-LD тоже индексируется поисковиками — проверяем отдельно
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, flags=re.S):
        bad += [l.strip() for l in block.splitlines() if CYR.search(l)]
    return bad


def main():
    problems = 0
    for lang in LANGS:
        os.makedirs(os.path.join(ROOT, lang), exist_ok=True)
        for page in PAGES:
            html = localize(page, lang)
            bad = leftovers(html)
            if bad:
                problems += len(bad)
                print(f"[{lang}/{page}] осталась кириллица:")
                for b in bad:
                    print("   ", b[:140])
            with open(os.path.join(ROOT, lang, page), "w", encoding="utf-8", newline="\n") as f:
                f.write(html)
            print(f"OK {lang}/{page}")
    if problems:
        sys.exit(f"Непереведённых фрагментов: {problems}")


if __name__ == "__main__":
    main()
