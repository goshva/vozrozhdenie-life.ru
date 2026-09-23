# -*- coding: utf-8 -*-
"""Генератор PDF-тизера «Возрождение» (строгий стиль, серая палитра, A4).

Запуск из корня репозитория:
    pip install reportlab pillow
    python build/teaser_pdf.py
Результат: assets/docs/vozrozhdenie-teaser.pdf
Данные синхронизированы с teaser.html — при изменении цены/состава актива править оба файла.
"""
import io
import os

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")
OUT = os.path.join(ROOT, "assets", "docs", "vozrozhdenie-teaser.pdf")
FONTS = os.environ.get("WINDIR", r"C:\Windows") + r"\Fonts"

pdfmetrics.registerFont(TTFont("R", os.path.join(FONTS, "Roboto-Regular.ttf")))
pdfmetrics.registerFont(TTFont("RM", os.path.join(FONTS, "Roboto-Medium.ttf")))
pdfmetrics.registerFont(TTFont("RB", os.path.join(FONTS, "Roboto-Bold.ttf")))
pdfmetrics.registerFont(TTFont("RI", os.path.join(FONTS, "Roboto-Italic.ttf")))
pdfmetrics.registerFontFamily("R", normal="R", bold="RB", italic="RI", boldItalic="RB")

# ---- Палитра (графит / серый) ----
INK = colors.HexColor("#1F2328")       # основной текст, заголовки
GRAPHITE = colors.HexColor("#3A4048")  # плашки, шапки таблиц
STEEL = colors.HexColor("#6B727B")     # второстепенный текст
RULE = colors.HexColor("#C3C8CE")      # линейки
PANEL = colors.HexColor("#EEF0F2")     # фон блоков
ZEBRA = colors.HexColor("#F6F7F8")
WHITE = colors.white

PAGE_W, PAGE_H = A4
M_L, M_R, M_T, M_B = 20 * mm, 20 * mm, 24 * mm, 22 * mm
CW = PAGE_W - M_L - M_R  # ширина контента

DOC_DATE = "Сентябрь 2026 г."

# ---- Стили ----
def st(name, **kw):
    base = dict(fontName="R", fontSize=9.5, leading=13.5, textColor=INK)
    base.update(kw)
    return ParagraphStyle(name, **base)

S_BODY = st("body", alignment=TA_JUSTIFY)
S_BODY_L = st("bodyl")  # для узких колонок — без выключки по ширине
S_SMALL = st("small", fontSize=8, leading=11, textColor=STEEL)
S_SMALL_J = st("smallj", fontSize=8, leading=11, textColor=STEEL, alignment=TA_JUSTIFY)
S_CAP = st("cap", fontName="RI", fontSize=7.8, leading=10, textColor=STEEL)
S_SEC_NUM = st("secnum", fontName="RM", fontSize=8.5, leading=11, textColor=STEEL)
S_H1 = st("h1", fontName="RB", fontSize=15, leading=19, spaceAfter=2)
S_H2 = st("h2", fontName="RM", fontSize=10.5, leading=14, spaceBefore=4, spaceAfter=4)
S_CELL = st("cell", fontSize=8.8, leading=11.5)
S_CELL_B = st("cellb", fontName="RM", fontSize=8.8, leading=11.5)
S_CELL_R = st("cellr", fontSize=8.8, leading=11.5, alignment=TA_RIGHT)
S_CELL_RB = st("cellrb", fontName="RB", fontSize=8.8, leading=11.5, alignment=TA_RIGHT)
S_CELL_K = st("cellk", fontSize=8.8, leading=11.5, textColor=STEEL)
S_TH = st("th", fontName="RM", fontSize=8, leading=10.5, textColor=WHITE)
S_TH_R = st("thr", fontName="RM", fontSize=8, leading=10.5, textColor=WHITE, alignment=TA_RIGHT)
S_BUL = st("bul", leftIndent=11, bulletIndent=0, alignment=TA_LEFT, spaceAfter=2.5)
S_KPI_V = st("kpiv", fontName="RB", fontSize=15, leading=18, alignment=TA_LEFT)
S_KPI_L = st("kpil", fontSize=7.8, leading=10, textColor=STEEL)


def P(text, style=S_BODY):
    return Paragraph(text, style)


def bullets(items, style=S_BUL):
    return [Paragraph(t, style, bulletText="—") for t in items]


def section(num, title):
    """Заголовок раздела: номер, название, тонкая линейка."""
    t = Table(
        [[P(f"РАЗДЕЛ {num}", S_SEC_NUM)], [P(title, S_H1)]],
        colWidths=[CW],
        style=TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LINEBELOW", (0, -1), (-1, -1), 1.2, GRAPHITE),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
        ]),
    )
    return [t, Spacer(1, 8)]


def photo(name, width, height=None, grey=False):
    """Изображение, вписанное по ширине (опционально обрезанное по высоте)."""
    im = PILImage.open(os.path.join(IMG, name)).convert("RGB")
    if grey:
        im = im.convert("L").convert("RGB")
    w, h = im.size
    if height:
        target = width / height
        if w / h > target:
            nw = int(h * target)
            im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = int(w / target)
            im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    else:
        height = width * h / w
    im.thumbnail((1400, 1400))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True)
    buf.seek(0)
    return Image(buf, width=width, height=height)


def figure(name, width, height, caption):
    return [photo(name, width, height), Spacer(1, 3), P(caption, S_CAP)]


def kv_table(rows, key_w=58 * mm, width=CW):
    """Таблица «параметр — значение» (стиль банковского term sheet)."""
    data = [[P(k, S_CELL_K), P(v, S_CELL)] for k, v in rows]
    t = Table(data, colWidths=[key_w, width - key_w])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, RULE),
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, GRAPHITE),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def grid_table(header, rows, widths, right_cols=(), total=False):
    hs = [P(h, S_TH_R if i in right_cols else S_TH) for i, h in enumerate(header)]
    body = []
    for r_i, row in enumerate(rows):
        last = total and r_i == len(rows) - 1
        cells = []
        for i, v in enumerate(row):
            if i in right_cols:
                cells.append(P(v, S_CELL_RB if last else S_CELL_R))
            else:
                cells.append(P(v, S_CELL_B if last else S_CELL))
        body.append(cells)
    t = Table([hs] + body, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), GRAPHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, RULE),
    ]
    for i in range(1, len(body) + 1):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    if total:
        style += [("BACKGROUND", (0, -1), (-1, -1), PANEL),
                  ("LINEABOVE", (0, -1), (-1, -1), 0.9, GRAPHITE),
                  ("LINEBELOW", (0, -1), (-1, -1), 0.9, GRAPHITE)]
    t.setStyle(TableStyle(style))
    return t


def kpi_row(items):
    """Ряд ключевых показателей в серых плашках."""
    n = len(items)
    gap = 3 * mm
    w = (CW - gap * (n - 1)) / n
    cells, widths = [], []
    for i, (v, l) in enumerate(items):
        cells.append([P(v, S_KPI_V), Spacer(1, 2), P(l, S_KPI_L)])
        widths.append(w)
        if i < n - 1:
            cells.append("")
            widths.append(gap)
    t = Table([cells], colWidths=widths)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
             ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]
    for i in range(0, len(widths), 2):
        style += [("BACKGROUND", (i, 0), (i, 0), PANEL),
                  ("LINEABOVE", (i, 0), (i, 0), 1.6, GRAPHITE)]
    for i in range(1, len(widths), 2):
        style += [("LEFTPADDING", (i, 0), (i, 0), 0), ("RIGHTPADDING", (i, 0), (i, 0), 0)]
    t.setStyle(TableStyle(style))
    return t


def note_box(flowables, bg=PANEL):
    t = Table([[flowables]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 2, GRAPHITE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def two_col(left, right, left_w=None, gap=7 * mm):
    left_w = left_w or (CW - gap) / 2
    t = Table([[left, "", right]], colWidths=[left_w, gap, CW - gap - left_w])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


# ---- Колонтитулы ----
class NumberedCanvas(rl_canvas.Canvas):
    """Canvas с нумерацией «Стр. N из M»."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            if self._pageNumber > 1:
                self._chrome(total)
            super().showPage()
        super().save()

    def _chrome(self, total):
        c = self
        c.saveState()
        # шапка
        c.setFillColor(GRAPHITE)
        c.rect(0, PAGE_H - 4 * mm, PAGE_W, 4 * mm, stroke=0, fill=1)
        c.setFont("RM", 7.5)
        c.setFillColor(INK)
        c.drawString(M_L, PAGE_H - 12 * mm, "ЖИЛОЙ РАЙОН «ВОЗРОЖДЕНИЕ»  ·  ИНВЕСТИЦИОННЫЙ ТИЗЕР")
        c.setFont("R", 7.5)
        c.setFillColor(STEEL)
        c.drawRightString(PAGE_W - M_R, PAGE_H - 12 * mm, "Конфиденциально  ·  " + DOC_DATE)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        c.line(M_L, PAGE_H - 14.5 * mm, PAGE_W - M_R, PAGE_H - 14.5 * mm)
        # подвал
        c.line(M_L, 14 * mm, PAGE_W - M_R, 14 * mm)
        c.setFont("R", 7)
        c.drawString(M_L, 10 * mm,
                     "Материалы носят информационный характер и не являются публичной офертой (ст. 437 ГК РФ).")
        c.setFont("RM", 7.5)
        c.setFillColor(INK)
        c.drawRightString(PAGE_W - M_R, 10 * mm, f"Стр. {self._pageNumber} из {total}")
        c.restoreState()


def cover(c, doc):
    """Титульный лист."""
    c.saveState()
    # верхний тёмный блок
    band_h = 118 * mm
    c.setFillColor(INK)
    c.rect(0, PAGE_H - band_h, PAGE_W, band_h, stroke=0, fill=1)
    c.setFillColor(GRAPHITE)
    c.rect(0, PAGE_H - band_h, 8 * mm, band_h, stroke=0, fill=1)

    c.drawImage(os.path.join(IMG, "logo.png"), M_L, PAGE_H - 34 * mm, 16 * mm, 16 * mm, mask="auto")
    c.setFillColor(colors.HexColor("#AEB4BB"))
    c.setFont("RM", 8)
    c.drawString(M_L + 20 * mm, PAGE_H - 24 * mm, "ООО «ЭКСПОСТРОЙ»")
    c.setFont("R", 8)
    c.drawString(M_L + 20 * mm, PAGE_H - 28.5 * mm, "Предложение о продаже актива")
    c.drawRightString(PAGE_W - M_R, PAGE_H - 24 * mm, "КОНФИДЕНЦИАЛЬНО")
    c.drawRightString(PAGE_W - M_R, PAGE_H - 28.5 * mm, DOC_DATE)

    c.setFillColor(colors.HexColor("#AEB4BB"))
    c.setFont("RM", 9.5)
    c.drawString(M_L, PAGE_H - 56 * mm, "ИНВЕСТИЦИОННЫЙ ТИЗЕР")
    c.setFillColor(WHITE)
    c.setFont("RB", 25)
    c.drawString(M_L, PAGE_H - 68 * mm, "Земельный массив под")
    c.drawString(M_L, PAGE_H - 78.5 * mm, "индивидуальное жилищное")
    c.drawString(M_L, PAGE_H - 89 * mm, "строительство «Возрождение»")
    c.setFillColor(colors.HexColor("#C9CED4"))
    c.setFont("R", 10)
    c.drawString(M_L, PAGE_H - 100 * mm,
                 "Липецкая область, Добровский муниципальный округ, с. Преображеновка")
    c.drawString(M_L, PAGE_H - 105.5 * mm, "Кадастровый квартал 48:05:0880401")

    # фото
    ph_h = 78 * mm
    ph_y = PAGE_H - band_h - ph_h
    im = PILImage.open(os.path.join(IMG, "land-aerial.jpg")).convert("RGB")
    w, h = im.size
    target = PAGE_W / ph_h
    nh = int(w / target)
    im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84)
    buf.seek(0)
    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(buf), 0, ph_y, PAGE_W, ph_h)

    # ключевые параметры
    y0 = ph_y - 13 * mm
    c.setFillColor(INK)
    c.setFont("RM", 8.5)
    c.drawString(M_L, y0, "КЛЮЧЕВЫЕ ПАРАМЕТРЫ ПРЕДЛОЖЕНИЯ")
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(1.2)
    c.line(M_L, y0 - 3 * mm, PAGE_W - M_R, y0 - 3 * mm)
    kp = [
        ("213 338 000 ₽", "Цена предложения (рыночная, заявленная)"),
        ("42,67 га", "Совокупная площадь по данным кадастра"),
        ("200", "Земельных участков, из них 197 — ИЖС"),
        ("100 %", "Продажа актива целиком одному покупателю"),
    ]
    col_w = CW / 4
    for i, (v, l) in enumerate(kp):
        x = M_L + i * col_w
        if i:
            c.setStrokeColor(RULE)
            c.setLineWidth(0.5)
            c.line(x - 2 * mm, y0 - 8 * mm, x - 2 * mm, y0 - 30 * mm)
        c.setFillColor(INK)
        c.setFont("RB", 15 if i == 0 else 17)
        c.drawString(x, y0 - 14 * mm, v)
        c.setFillColor(STEEL)
        c.setFont("R", 7.6)
        words, line, ly = l.split(), "", y0 - 20 * mm
        for wd in words:
            test = (line + " " + wd).strip()
            if c.stringWidth(test, "R", 7.6) > col_w - 6 * mm:
                c.drawString(x, ly, line)
                ly -= 3.6 * mm
                line = wd
            else:
                line = test
        c.drawString(x, ly, line)

    # нижний колонтитул титула
    c.setStrokeColor(RULE)
    c.setLineWidth(0.5)
    c.line(M_L, 22 * mm, PAGE_W - M_R, 22 * mm)
    c.setFillColor(STEEL)
    c.setFont("R", 7.3)
    c.drawString(M_L, 17 * mm, "Документ подготовлен для предварительного ознакомления потенциальных инвесторов и не является")
    c.drawString(M_L, 13.5 * mm, "публичной офертой. Полный инвестиционный меморандум предоставляется после подписания NDA.")
    c.setFillColor(INK)
    c.setFont("RM", 7.5)
    c.drawRightString(PAGE_W - M_R, 17 * mm, "vozrozhdenie-life.ru")
    c.drawRightString(PAGE_W - M_R, 13.5 * mm, "+7 910 351-13-33")
    c.restoreState()


# ---- Содержание ----
def build_story():
    s = []
    s.append(Spacer(1, 1))
    s.append(NextPageTemplate("body"))
    s.append(PageBreak())

    # I. Резюме
    s += section("I", "Резюме инвестиционного предложения")
    s.append(P(
        "Предметом предложения является земельный массив площадью <b>42,67 га</b>, "
        "сформированный из <b>200 земельных участков</b> с оформленным кадастровым учётом, "
        "принадлежащих <b>единому правообладателю</b>. Актив реализуется целиком одному покупателю "
        "совместно с мастер-планом, архитектурной концепцией, продуктовой линейкой жилых домов, "
        "инженерной концепцией и кадастровыми материалами. Консолидация земли в одних руках "
        "исключает для инвестора риски и издержки поэтапного сбора участков у множества собственников."))
    s.append(Spacer(1, 8))
    s.append(kpi_row([
        ("213,3 млн ₽", "цена предложения"),
        ("5,0 млн ₽/га", "удельная стоимость (500 ₽/м²)"),
        ("≈1,03 млн ₽", "средняя стоимость участка ИЖС"),
        ("197 уч.", "под жилую застройку, 40,75 га"),
    ]))
    s.append(Spacer(1, 10))
    s.append(P("Основные условия", S_H2))
    s.append(kv_table([
        ("Объект", "Земельный массив под индивидуальное жилищное строительство «Возрождение» с объектами обслуживающей инфраструктуры"),
        ("Местоположение", "Липецкая область, Добровский муниципальный округ, в 2,5 км от с. Преображеновка; берег р. Воронеж"),
        ("Кадастровый квартал", "48:05:0880401"),
        ("Состав актива", "200 земельных участков: 197 — ИЖС (40,75 га); 3 — инфраструктура и социальные объекты (1,92 га)"),
        ("Правовой статус", "Участки поставлены на кадастровый учёт; единый собственник; сведения ЕГРН предоставляются по запросу"),
        ("Цена предложения", "<b>213 338 000 ₽</b> — рыночная (заявленная) оценка"),
        ("Форма сделки", "Отчуждение 100 % актива одному покупателю; допускается структурированная или поэтапная сделка"),
        ("Периметр сделки", "Рекреационные и природоохранные участки (заказник, пруды, усадьбы, база отдыха) в периметр не входят и остаются за продавцом"),
    ]))
    s.append(Spacer(1, 10))
    s.append(P("Инвестиционные преимущества", S_H2))
    s += bullets([
        "<b>Консолидированный земельный банк</b> — все участки у одного правообладателя, кадастровый учёт завершён.",
        "<b>Готовая инженерная подготовка</b> — асфальтированный подъезд, действующий мост через р. Воронеж (введён в эксплуатацию 01.11.2020), электроснабжение, газификация территории.",
        "<b>Проработанная продуктовая концепция</b> — единый архитектурный регламент, серийная линейка домов 70–120 м², построенный демонстрационный дом.",
        "<b>Компактный периметр сделки</b> — только жилая застройка и обслуживающая инфраструктура: ниже порог входа, короче due diligence и сроки закрытия.",
        "<b>Сложившаяся социальная среда</b> — в 2,5 км действующие школа, детский сад, ФАП, спортивный комплекс, магазины.",
    ])

    # II. Характеристика объекта
    s.append(PageBreak())
    s += section("II", "Характеристика и структура актива")
    s.append(P(
        "Структура актива приведена по актуальным кадастровым данным. Стоимость определена "
        "как рыночная (заявленная) по единой ставке 500 ₽/м² для участков жилой застройки и инфраструктуры."))
    s.append(Spacer(1, 8))
    s.append(grid_table(
        ["Назначение участков", "Кол-во", "Площадь, га", "Оценка, ₽", "Доля, %"],
        [
            ["Участки ИЖС (жилая застройка)", "197", "40,75", "203 717 500", "95,5"],
            ["Инфраструктура и социальные объекты<br/><font size=7.5 color='#6B727B'>спортплощадка, деловая зона, водонапорная башня</font>",
             "3", "1,92", "9 620 500", "4,5"],
            ["Итого", "200", "42,67", "213 338 000", "100,0"],
        ],
        [CW - 25 * mm - 27 * mm - 32 * mm - 20 * mm, 25 * mm, 27 * mm, 32 * mm, 20 * mm],
        right_cols=(1, 2, 3, 4), total=True,
    ))
    s.append(Spacer(1, 5))
    s.append(P(
        "Примечание. Официальная кадастровая стоимость участков по данным Росреестра ниже рыночной "
        "оценки; выписки ЕГРН предоставляются по запросу. Рыночная оценка отражает степень "
        "подготовленности массива и наличие концепции и не заменяет независимую оценку "
        "в соответствии с Федеральным законом № 135-ФЗ «Об оценочной деятельности».", S_SMALL_J))
    s.append(Spacer(1, 12))
    zone = [
        photo("zoning-map.jpg", 72 * mm, 82 * mm),
        Spacer(1, 3),
        P("Фрагмент утверждённой схемы зонирования: жилая застройка, инфраструктура.", S_CAP),
    ]
    txt = [
        P("Градостроительный контекст", S_H2),
        P("Территория предусмотрена действующими Правилами землепользования и застройки "
          "сельского поселения; схема зонирования и кадастровая карта входят в пакет "
          "документов, передаваемых покупателю.", S_BODY_L),
        Spacer(1, 6),
        P("В расширенной проектной концепции жилая застройка рассчитана на 48 га и до "
          "223–227 домовладений с учётом дальнейшего межевания резервных зон. Детализация "
          "приводится в полном инвестиционном меморандуме.", S_BODY_L),
        Spacer(1, 10),
        kv_table([
            ("Участков ИЖС", "197"),
            ("Средняя площадь участка ИЖС", "≈20,7 сот."),
            ("Потенциал по концепции", "до 223–227 домовладений"),
        ], key_w=48 * mm, width=CW - 79 * mm),
    ]
    s.append(two_col(zone, txt, left_w=72 * mm))

    # III. Местоположение
    s.append(PageBreak())
    s += section("III", "Местоположение и транспортная доступность")
    s.append(KeepTogether(figure("bridge.jpg", CW, 62 * mm,
                    "Мост через р. Воронеж на подъездной дороге к массиву; введён в эксплуатацию 01.11.2020.")))
    s.append(Spacer(1, 10))
    loc = kv_table([
        ("Расположение", "Берег р. Воронеж, лесное окружение"),
        ("Подъезд", "Асфальтированная дорога"),
        ("Мост через р. Воронеж", "Введён в эксплуатацию 01.11.2020"),
        ("г. Липецк", "64 км"),
        ("г. Мичуринск", "50 км"),
        ("г. Тамбов", "120 км"),
        ("г. Москва", "≈400 км"),
    ], key_w=40 * mm, width=(CW - 7 * mm) / 2)
    soc = [
        P("Социальная инфраструктура", S_H2),
        P("В 2,5 км — с. Преображеновка: действующие школа, детский сад, бассейн, "
          "спортивный комплекс, фельдшерско-акушерский пункт, магазины, набережная и "
          "благоустроенный пляж. Проект реализуется в непосредственной близости от "
          "функционирующей инфраструктуры, что снижает потребность покупателя в "
          "капитальных вложениях в социальные объекты.", S_BODY_L),
    ]
    s.append(two_col([P("Транспортная доступность", S_H2), loc], soc))
    s.append(Spacer(1, 12))
    s.append(note_box([
        P("Репутация территории", S_H2),
        P("Село Преображеновка в 2011–2020 гг. шесть раз признавалось победителем всероссийского "
          "конкурса на звание самого благоустроенного сельского поселения России (категория — "
          "населённые пункты с численностью жителей до 400 человек)."),
        Spacer(1, 4),
        P("Источники: администрация Добровского муниципального округа (admdobroe.ru), раздел "
          "«Преображеновка»; ru.wikipedia.org — статья «Преображеновка (Липецкая область)»; "
          "vozrozhdenie-life.ru.", S_SMALL),
    ]))

    # IV. Инженерия и продукт
    s.append(PageBreak())
    s += section("IV", "Инженерная инфраструктура и продуктовая концепция")
    s.append(P("Инженерное обеспечение участков", S_H2))
    s.append(grid_table(
        ["Вид обеспечения", "Решение / параметры"],
        [
            ["Электроснабжение", "12,5 кВт на участок"],
            ["Газоснабжение", "Территория газифицирована"],
            ["Водоснабжение", "Индивидуальные скважины глубиной 30–100 м"],
            ["Водоотведение", "Автономные септики"],
            ["Теплоснабжение", "Газовый / электрический котёл, конвекторы"],
        ],
        [55 * mm, CW - 55 * mm],
    ))
    s.append(Spacer(1, 12))
    s.append(P("Продуктовая линейка", S_H2))
    s.append(P(
        "Концепция предусматривает застройку деревянными домами в едином современном архитектурном "
        "стиле: фахверк, Barn House, Hi-Tech, модульные дома и CLT / CLT Thermo (производитель — "
        "ПромСтройЛес, pslcomp.ru). Каталог концепции охватывает дома площадью 36–180 м²; для "
        "быстрого старта продаж в партнёрской модели сформирована серийная линейка:"))
    s.append(Spacer(1, 6))
    s.append(grid_table(
        ["Формат", "Площадь дома", "Целевой сегмент"],
        [
            ["Компактный", "70 м²", "Дача, семейная пара, небольшая семья"],
            ["Базовый", "95 м²", "Основной семейный продукт"],
            ["Комфорт", "120 м²", "Комфорт-сегмент"],
        ],
        [40 * mm, 35 * mm, CW - 75 * mm],
    ))
    s.append(Spacer(1, 6))
    s.append(P("Рекомендуемый объём первой очереди — <b>20–30 участков</b> с последующим "
               "масштабированием по мере реализации."))
    s.append(Spacer(1, 10))
    s.append(two_col(
        figure("house-real.jpg", (CW - 7 * mm) / 2, 52 * mm,
               "Построенный демонстрационный дом на участке — реальный объект."),
        figure("house-white.jpg", (CW - 7 * mm) / 2, 52 * mm,
               "Архитектурная концепция: единый стиль застройки."),
    ))

    # V. Условия сделки
    s.append(PageBreak())
    s += section("V", "Условия сделки и порядок взаимодействия")
    s.append(P(
        "Предлагается отчуждение 100 % жилого массива и обслуживающей его инфраструктуры "
        "вместе с проектной документацией, архитектурной концепцией, продуктовой линейкой "
        "домов, инженерной концепцией и кадастровыми материалами. Актив реализуется одному "
        "покупателю без дробления на лоты. Структура сделки (единовременная, поэтапная, "
        "с отсрочкой платежа, через SPV) определяется по результатам переговоров."))
    s.append(Spacer(1, 8))
    s.append(kv_table([
        ("Цена предложения", "<b>213 338 000 ₽</b>"),
        ("Основание расчёта", "200 участков в кадастровом квартале 48:05:0880401; ставка 500 ₽/м²"),
        ("Передаваемые материалы", "Мастер-план, архитектурный регламент, продуктовая линейка, инженерная концепция, кадастровые материалы"),
        ("Не входит в сделку", "Заказник, пруды, усадьбы, база отдыха"),
        ("Расчёты", "Порядок и сроки расчётов, форма обеспечения (аккредитив, эскроу, номинальный счёт) — по согласованию сторон"),
    ]))
    s.append(Spacer(1, 12))
    s.append(P("Порядок взаимодействия", S_H2))
    steps = [
        ("1", "Подписание соглашения о конфиденциальности (NDA)"),
        ("2", "Предоставление инвестиционного меморандума, выписок ЕГРН, ПЗЗ и кадастровой карты"),
        ("3", "Осмотр объекта на местности"),
        ("4", "Юридический, технический и финансовый due diligence"),
        ("5", "Согласование основных условий (term sheet / LOI)"),
        ("6", "Подписание договора и государственная регистрация перехода права"),
    ]
    rows = [[P(n, st("n", fontName="RB", fontSize=10, textColor=WHITE, alignment=TA_CENTER)), P(t, S_CELL)] for n, t in steps]
    t = Table(rows, colWidths=[9 * mm, CW - 9 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRAPHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, WHITE),
        ("LINEBELOW", (1, 0), (1, -1), 0.5, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (1, 0), (1, -1), 8),
    ]))
    s.append(t)
    s.append(Spacer(1, 14))
    contact = Table([
        [P("КОНТАКТНОЕ ЛИЦО", st("cl", fontName="RM", fontSize=8, textColor=colors.HexColor("#AEB4BB"))), ""],
        [P("ООО «Экспострой»<br/>Максим Игоревич", st("cn", fontName="RB", fontSize=12, leading=16, textColor=WHITE)),
         P("+7 910 351-13-33<br/>expostroy48@mail.ru<br/>vozrozhdenie-life.ru",
           st("cc", fontName="RM", fontSize=10, leading=15, textColor=WHITE, alignment=TA_RIGHT))],
    ], colWidths=[CW / 2, CW / 2])
    contact.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, 0), 10), ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
    ]))
    s.append(contact)
    s.append(Spacer(1, 14))
    s.append(P("Ограничение ответственности", S_H2))
    s.append(P(
        "Настоящий документ подготовлен исключительно в информационных целях, носит "
        "предварительный характер и не является публичной офертой в смысле ст. 437 ГК РФ, "
        "предложением о заключении договора или индивидуальной инвестиционной рекомендацией. "
        "Приведённые сведения основаны на данных правообладателя и публичных источниках и "
        "могут быть изменены без предварительного уведомления. Перед принятием инвестиционного "
        "решения необходима актуализация сведений ЕГРН, градостроительного регламента, видов "
        "разрешённого использования, зон с особыми условиями использования территорий (ЗОУИТ), "
        "условий дорожного доступа и технических условий подключения к инженерным сетям. "
        "Распространение документа третьим лицам без согласия правообладателя не допускается.",
        S_SMALL_J))
    return s


def main():
    doc = BaseDocTemplate(
        OUT, pagesize=A4, leftMargin=M_L, rightMargin=M_R, topMargin=M_T, bottomMargin=M_B,
        title="Инвестиционный тизер — земельный массив «Возрождение»",
        author="ООО «Экспострой»",
        subject="Продажа земельного массива ИЖС, Липецкая область, с. Преображеновка",
        keywords="Возрождение, ИЖС, земельный массив, инвестиции, Липецкая область",
        creator="build/teaser_pdf.py",
    )
    frame = Frame(M_L, M_B, CW, PAGE_H - M_T - M_B, id="f", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate("cover", frames=[frame], onPage=cover),
        PageTemplate("body", frames=[frame]),
    ])
    doc.build(build_story(), canvasmaker=NumberedCanvas)
    print("OK:", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
