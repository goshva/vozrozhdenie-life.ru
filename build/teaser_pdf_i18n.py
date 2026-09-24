# -*- coding: utf-8 -*-
"""PDF-тизер «Возрождение» на корейском, китайском и вьетнамском.

Запуск из корня репозитория (Windows — нужны системные шрифты Malgun Gothic и Microsoft YaHei):
    pip install reportlab pillow
    python build/teaser_pdf_i18n.py          # все языки
    python build/teaser_pdf_i18n.py ko       # один язык
Результат: assets/docs/vozrozhdenie-teaser-{ko,zh,vi}.pdf

Вёрстка и хелперы берутся из build/teaser_pdf.py (русская версия), здесь — только тексты,
шрифты и национальные особенности:
  ko — Malgun Gothic, суммы в 억/만, площадь дублируется в 평, деловой стиль 합쇼체;
  zh — Microsoft YaHei, перенос строк по иероглифам (wordWrap=CJK), суммы в 亿/万, площадь в 亩;
  vi — Roboto (полная вьетнамская диакритика), формат чисел 213.338.000 / 42,7 ha.
Цифры синхронизированы с teaser.html и build/teaser_pdf.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import teaser_pdf as tp  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_RIGHT  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.lib.utils import ImageReader  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    BaseDocTemplate, Frame, KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from PIL import Image as PILImage  # noqa: E402
import io  # noqa: E402

P, CW = tp.P, tp.CW
INK, GRAPHITE, STEEL, RULE, WHITE = tp.INK, tp.GRAPHITE, tp.STEEL, tp.RULE, tp.WHITE
PAGE_W, PAGE_H, M_L, M_R = tp.PAGE_W, tp.PAGE_H, tp.M_L, tp.M_R

FONT_FILES = {
    "ko": {"R": ("malgun.ttf", None), "RM": ("malgunbd.ttf", None), "RB": ("malgunbd.ttf", None), "RI": ("malgun.ttf", None)},
    "zh": {"R": ("msyh.ttc", 0), "RM": ("msyhbd.ttc", 0), "RB": ("msyhbd.ttc", 0), "RI": ("msyh.ttc", 0)},
    "vi": {"R": ("Roboto-Regular.ttf", None), "RM": ("Roboto-Medium.ttf", None),
           "RB": ("Roboto-Bold.ttf", None), "RI": ("Roboto-Italic.ttf", None)},
}

# ----------------------------------------------------------------------------
# Тексты
# ----------------------------------------------------------------------------
L = {}

L["ko"] = dict(
    date="2026년 9월",
    company="EXPOSTROY LLC", offer="자산 매각 제안", conf="대외비(CONFIDENTIAL)",
    kind="투자 개요서 (TEASER)",
    title=["러시아 보로네시강변", "개인주택 건축용지 일괄 매각", "‘Vozrozhdenie’"],
    loc=["러시아 리페츠크주 도브로프스키 관구, 프레오브라제노프카 마을 인근", "지적 구역 48:05:0880401 · 모스크바에서 약 400km"],
    kp_head="매각 핵심 조건",
    kp=[("2억 1,334만 루블", "매각 희망가 (시장가, 매도인 제시)"),
        ("42.67ha", "지적 총면적 (약 12만 9천 평)"),
        ("200필지", "그중 197필지 개인주택 건축용지(IZhS)"),
        ("100%", "단일 매수인 일괄 매각")],
    cover_foot=["본 자료는 잠재 투자자의 사전 검토용이며 청약이 아닙니다. 번역본은 참고용이며 러시아어 원문이 우선합니다.",
                "상세 투자 설명서(IM)는 비밀유지계약(NDA) 체결 후 제공합니다."],
    head_left="VOZROZHDENIE 주거지구 · 투자 개요서", head_conf="대외비",
    foot="본 자료는 정보 제공 목적이며 공개 청약이 아닙니다(러시아 민법 제437조).",
    page="{n} / {t} 페이지",
    sec="제{n}장",
    s1="투자 제안 요약",
    s1_intro=("매각 대상은 지적 등록이 완료된 <b>200개 필지</b>로 구성된 <b>42.67ha(약 12만 9천 평)</b> 규모의 토지이며, "
              "<b>단일 소유자</b>가 보유하고 있습니다. 마스터플랜, 건축 콘셉트, 주택 상품 라인업, 기반시설 계획, 지적 자료와 함께 "
              "단일 매수인에게 일괄 매각합니다. 토지가 한 소유자에게 통합되어 있어, 다수 지주로부터 토지를 단계적으로 매입할 때 발생하는 "
              "위험과 비용이 없습니다."),
    s1_kpi=[("2억 1,334만 루블", "매각 희망가"),
            ("㎡당 500루블", "단위 가격 (평당 약 1,653루블)"),
            ("약 103만 루블", "IZhS 필지당 평균 가격"),
            ("197필지", "주거용, 40.75ha")],
    terms_h="주요 조건",
    terms=[("대상 자산", "개인주택 건축용지 ‘Vozrozhdenie’ 및 부속 기반시설"),
           ("소재지", "러시아 리페츠크주 도브로프스키 관구, 프레오브라제노프카 마을에서 2.5km, 보로네시강변"),
           ("지적 구역", "48:05:0880401"),
           ("자산 구성", "200필지: 개인주택 건축용지(IZhS) 197필지(40.75ha), 기반시설·공공시설 3필지(1.92ha)"),
           ("권리 관계", "전 필지 지적 등록 완료, 단일 소유자. 부동산 등기부(EGRN) 등본은 요청 시 제공"),
           ("매각 희망가", "<b>213,338,000루블</b>(약 2억 1,334만 루블) — 매도인 제시 시장가"),
           ("거래 방식", "자산 100% 단일 매수인 양도. 구조화 거래 또는 단계별 거래 가능"),
           ("거래 범위", "휴양·자연보호 필지(자연보호구역, 연못, 영지, 휴양시설)는 제외되며 매도인이 보유")],
    adv_h="투자 포인트",
    adv=["<b>통합된 토지 뱅크</b> — 전 필지 단일 소유, 지적 등록 완료.",
         "<b>기반시설 준공</b> — 아스팔트 진입로, 보로네시강 교량(2020년 11월 1일 준공), 전력, 가스 공급.",
         "<b>완성된 상품 콘셉트</b> — 통일된 건축 가이드라인, 70–120㎡ 규격형 주택 라인업, 준공된 견본주택.",
         "<b>단순한 거래 범위</b> — 주거용지와 부속 기반시설만 포함되어 진입 가격이 낮고 실사·종결이 빠름.",
         "<b>검증된 생활 환경</b> — 2.5km 거리에 학교, 유치원, 보건진료소, 체육시설, 상점이 운영 중."],
    s2="자산 개요 및 구성",
    s2_intro="자산 구성은 최신 지적 자료 기준입니다. 평가액은 주거용지와 기반시설에 ㎡당 500루블을 일괄 적용한 매도인 제시 시장가입니다.",
    tbl_head=["용도", "필지 수", "면적(ha)", "평가액(루블)", "비중(%)"],
    tbl=[["개인주택 건축용지(IZhS, 주거)", "197", "40.75", "203,717,500", "95.5"],
         ["기반시설 및 공공시설<br/><font size=7.5 color='#6B727B'>체육시설, 업무 구역, 급수탑</font>", "3", "1.92", "9,620,500", "4.5"],
         ["합계", "200", "42.67", "213,338,000", "100.0"]],
    s2_note=("주: 러시아 연방등기청(Rosreestr)의 공시 지적가격은 시장 평가액보다 낮으며, 부동산 등기부(EGRN) 등본은 요청 시 제공합니다. "
             "시장 평가액은 부지의 개발 준비 수준과 콘셉트를 반영한 것으로, 러시아 연방 감정평가법(No. 135-FZ)에 따른 독립 감정을 대체하지 않습니다."),
    zone_cap="승인된 용도지역 계획도 일부: 주거용지, 기반시설.",
    urb_h="도시계획 현황",
    urb=["부지는 해당 농촌 정주지의 토지이용 및 건축 규정(PZZ)에 반영되어 있으며, 용도지역 계획도와 지적도는 매수인에게 인도되는 자료에 포함됩니다.",
         "확장 개발 콘셉트 기준으로 예비 구역의 추가 분할을 반영하면 주거 개발 면적 48ha, 주택 223–227호까지 가능합니다. 상세 내용은 투자 설명서(IM)에 수록되어 있습니다."],
    urb_kv=[("IZhS 필지 수", "197"), ("IZhS 필지 평균 면적", "약 2,070㎡ (약 626평)"), ("콘셉트상 개발 잠재력", "최대 223–227호")],
    s3="입지 및 교통 접근성",
    bridge_cap="부지 진입로의 보로네시강 교량 — 2020년 11월 1일 준공.",
    tr_h="교통 접근성",
    tr=[("입지", "보로네시강변, 숲으로 둘러싸인 부지"), ("진입로", "아스팔트 포장도로"), ("보로네시강 교량", "2020년 11월 1일 준공"),
        ("리페츠크시", "64km"), ("미추린스크시", "50km"), ("탐보프시", "120km"), ("모스크바", "약 400km")],
    soc_h="생활 인프라",
    soc=("2.5km 거리의 프레오브라제노프카 마을에는 학교, 유치원, 수영장, 종합 체육시설, 보건진료소, 상점, 강변 산책로, "
         "정비된 해변이 운영 중입니다. 운영 중인 인프라 바로 옆에서 사업이 추진되므로, 매수인의 사회기반시설 투자 부담이 줄어듭니다."),
    rep_h="지역 평판",
    rep=("프레오브라제노프카 마을은 2011–2020년 러시아 전국 ‘가장 살기 좋은 농촌 마을’ 경연(인구 400명 이하 부문)에서 "
         "여섯 차례 우승했습니다."),
    rep_src="출처: 도브로프스키 관구 행정청(admdobroe.ru) ‘프레오브라제노프카’ 페이지; ru.wikipedia.org ‘프레오브라제노프카(리페츠크주)’; vozrozhdenie-life.ru (모두 러시아어).",
    s4="기반시설 및 상품 콘셉트",
    eng_h="필지별 기반시설",
    eng_head=["구분", "방식 / 사양"],
    eng=[["전력", "필지당 12.5kW"], ["가스", "도시가스 공급 지역"], ["급수", "개별 관정, 심도 30–100m"],
         ["하수", "개별 정화조"], ["난방", "가스 / 전기 보일러, 컨벡터"]],
    prod_h="주택 상품 라인업",
    prod=("통일된 현대적 스타일의 목조주택으로 개발합니다: 팩베르크(Fachwerk), 반하우스(Barn House), 하이테크, 모듈러, "
          "CLT / CLT Thermo(제조사: PromStroyLes, pslcomp.ru). 콘셉트 카탈로그는 연면적 36–180㎡이며, 신속한 분양 개시를 위해 "
          "파트너십 모델로 규격형 라인업을 구성했습니다:"),
    prod_head=["타입", "연면적", "목표 수요층"],
    prod_rows=[["콤팩트", "70㎡ (약 21평)", "세컨드하우스, 부부·소가족"], ["스탠다드", "95㎡ (약 29평)", "주력 가족형 상품"],
               ["컴포트", "120㎡ (약 36평)", "중·고급 수요"]],
    phase="권장 1단계 물량은 <b>20–30필지</b>이며, 분양 실적에 따라 순차 확대합니다.",
    cap_house1="부지에 준공된 견본주택 — 실제 건물.", cap_house2="건축 콘셉트: 통일된 단지 스타일.",
    s5="거래 조건 및 진행 절차",
    s5_intro=("주거용지와 부속 기반시설 100%를 설계 문서, 건축 콘셉트, 주택 상품 라인업, 기반시설 계획, 지적 자료와 함께 "
              "단일 매수인에게 양도합니다. 분할 매각은 하지 않습니다. 거래 구조(일시 지급, 단계별 지급, 지급 유예, SPV 인수 등)는 협상을 통해 정합니다."),
    deal_kv=[("매각 희망가", "<b>213,338,000루블</b> (약 2억 1,334만 루블)"),
             ("산정 기준", "지적 구역 48:05:0880401 내 200필지, ㎡당 500루블"),
             ("인도 자료", "마스터플랜, 건축 가이드라인, 주택 상품 라인업, 기반시설 계획, 지적 자료"),
             ("제외 대상", "자연보호구역, 연못, 영지, 휴양시설"),
             ("결제", "결제 일정, 통화, 담보 방식(신용장, 에스크로 등)은 당사자 간 협의")],
    proc_h="진행 절차",
    steps=["비밀유지계약(NDA) 체결", "투자 설명서, EGRN 등본, PZZ, 지적도 제공", "현장 방문(대표자 동행)",
           "법률·기술·재무 실사(due diligence)", "주요 조건 합의(Term Sheet / LOI)", "본계약 체결 및 소유권 이전 등기"],
    fn_h="해외 투자자 안내",
    fn=("외국인 및 외국 법인의 러시아 토지 취득은 러시아 연방 법령에 따르며, 러시아 현지 법인(SPV)을 통한 인수 구조를 협의할 수 있습니다. "
        "필요한 인허가 절차와 결제 방식은 개별 협의합니다. 한국 거주자의 해외 부동산 취득은 외국환거래법상 신고 대상일 수 있으므로 "
        "외국환은행 및 전문가와 사전 확인을 권장합니다."),
    contact_lbl="담당자", contact_name="Expostroy LLC<br/>막심 이고레비치 (대표 담당자)",
    disc_h="면책 조항",
    disc=("본 자료는 정보 제공 목적으로만 작성된 예비 자료로서, 러시아 민법 제437조에 따른 공개 청약, 계약 체결 제안 또는 투자 권유가 아닙니다. "
          "기재된 정보는 소유자 제공 자료 및 공개 자료에 근거하며 사전 통지 없이 변경될 수 있습니다. 투자 결정 전 부동산 등기부(EGRN), "
          "도시계획 규정, 토지 허용 용도, 이용 제한 구역(ZOUIT), 도로 접근성, 기반시설 연결 조건을 최신 기준으로 확인해야 합니다. "
          "본 번역본은 참고용이며 러시아어 원문이 우선합니다. 소유자의 동의 없이 제3자에게 배포할 수 없습니다."),
)

L["zh"] = dict(
    date="2026年9月",
    company="EXPOSTROY有限责任公司", offer="资产出售要约邀请", conf="保密文件",
    kind="投资简介",
    title=["俄罗斯沃罗涅日河畔", "个人住宅建设用地整体出售", "“Vozrozhdenie（复兴）”"],
    loc=["俄罗斯利佩茨克州Dobrovsky区，普列奥布拉热诺夫卡村附近", "地籍区块48:05:0880401 · 距莫斯科约400公里"],
    kp_head="核心交易要素",
    kp=[("2.13亿卢布", "出售报价（卖方申报市场价）"),
        ("42.67公顷", "地籍总面积（约640亩）"),
        ("200块", "其中197块为个人住宅建设用地"),
        ("100%", "整体出售给单一买方")],
    cover_foot=["本资料供潜在投资方初步了解，不构成公开要约。译文仅供参考，以俄文原文为准。",
                "完整投资备忘录（IM）在签署保密协议（NDA）后提供。"],
    head_left="VOZROZHDENIE住宅区 · 投资简介", head_conf="保密",
    foot="本资料仅供参考，不构成公开要约（《俄罗斯联邦民法典》第437条）。",
    page="第{n}页 / 共{t}页",
    sec="第{n}部分",
    s1="投资要约概要",
    s1_intro=("出售标的为由<b>200块</b>已完成地籍登记的地块组成、面积<b>42.67公顷（约640亩）</b>的整片用地，归<b>单一业主</b>所有。"
              "资产连同总体规划、建筑方案、住宅产品线、市政规划和地籍资料整体出售给单一买方。土地已集中于一个业主名下，"
              "投资方无需承担向众多业主分批收地的风险和成本。"),
    s1_kpi=[("2.13亿卢布", "出售报价"),
            ("500卢布/㎡", "单价（约33.3万卢布/亩）"),
            ("约103万卢布", "每块住宅用地均价"),
            ("197块", "住宅用地，40.75公顷")],
    terms_h="主要条件",
    terms=[("标的", "“Vozrozhdenie”个人住宅建设用地及配套设施"),
           ("位置", "俄罗斯利佩茨克州Dobrovsky区，距普列奥布拉热诺夫卡村2.5公里，沃罗涅日河畔"),
           ("地籍区块", "48:05:0880401"),
           ("资产构成", "200块地：个人住宅建设用地（IZhS）197块（40.75公顷）；基础设施及公共设施3块（1.92公顷）"),
           ("权属状况", "全部地块已完成地籍登记，单一业主；EGRN登记摘录可应要求提供"),
           ("出售报价", "<b>213,338,000卢布</b>（约2.13亿卢布）——卖方申报市场价"),
           ("交易方式", "100%资产转让给单一买方；可采用结构化或分期交易"),
           ("交易范围", "休闲及自然保护地块（自然保护区、池塘、庄园、度假基地）不在范围内，仍归卖方")],
    adv_h="投资亮点",
    adv=["<b>土地已整合</b>——全部地块归单一业主，地籍登记已完成。",
         "<b>基础设施已建成</b>——柏油进场道路、沃罗涅日河大桥（2020年11月1日投入使用）、电力、燃气。",
         "<b>产品规划成熟</b>——统一建筑规范、70–120㎡标准化住宅产品线、已建成样板房。",
         "<b>交易范围简洁</b>——仅含住宅用地及配套设施：门槛更低，尽职调查和交割更快。",
         "<b>成熟社会配套</b>——2.5公里内有正常运营的学校、幼儿园、医疗站、体育馆和商店。"],
    s2="资产概况与构成",
    s2_intro="资产构成依据最新地籍数据。估值为卖方申报的市场价，住宅用地及基础设施统一按每平方米500卢布计算。",
    tbl_head=["用途", "地块数", "面积（公顷）", "估值（卢布）", "占比（%）"],
    tbl=[["个人住宅建设用地（IZhS）", "197", "40.75", "203,717,500", "95.5"],
         ["基础设施及公共设施<br/><font size=7.5 color='#6B727B'>运动场、商务区、水塔</font>", "3", "1.92", "9,620,500", "4.5"],
         ["合计", "200", "42.67", "213,338,000", "100.0"]],
    s2_note=("注：俄罗斯联邦国家登记局（Rosreestr）公布的地籍价值低于市场估值；EGRN登记摘录可应要求提供。市场估值反映用地的开发成熟度和现成规划，"
             "不替代依据俄罗斯联邦第135-FZ号《评估活动法》进行的独立评估。"),
    zone_cap="已批准功能分区图（局部）：住宅用地、基础设施。",
    urb_h="规划背景",
    urb=["该区域已纳入所在农村居民点现行的土地利用与建设规则（PZZ）；功能分区图和地籍图属于移交给买方的文件。",
         "按扩展开发规划，在预留区域进一步分割后，住宅开发面积可达48公顷、223–227户。详见完整投资备忘录。"],
    urb_kv=[("住宅用地地块数", "197"), ("住宅用地平均面积", "约2,070㎡（约3.1亩）"), ("规划开发潜力", "至多223–227户")],
    s3="区位与交通",
    bridge_cap="通往用地的沃罗涅日河大桥，2020年11月1日投入使用。",
    tr_h="交通可达性",
    tr=[("位置", "沃罗涅日河畔，森林环绕"), ("进场道路", "柏油路"), ("沃罗涅日河大桥", "2020年11月1日投入使用"),
        ("利佩茨克市", "64公里"), ("米丘林斯克市", "50公里"), ("坦波夫市", "120公里"), ("莫斯科", "约400公里")],
    soc_h="社会配套",
    soc=("2.5公里外的普列奥布拉热诺夫卡村设有正常运营的学校、幼儿园、游泳馆、体育综合馆、医疗站、商店、滨河步道和整洁的沙滩。"
         "项目紧邻成熟配套，可减少买方在社会配套设施上的资本投入。"),
    rep_h="区域声誉",
    rep="普列奥布拉热诺夫卡村于2011–2020年间六次荣获全俄“最美乡村”评选冠军（人口400人以下组别）。",
    rep_src="资料来源：Dobrovsky区政府网站（admdobroe.ru）“普列奥布拉热诺夫卡”栏目；ru.wikipedia.org“普列奥布拉热诺夫卡（利佩茨克州）”；vozrozhdenie-life.ru（均为俄文）。",
    s4="市政配套与产品规划",
    eng_h="地块市政配套",
    eng_head=["类别", "方案 / 参数"],
    eng=[["电力", "每块地12.5千瓦"], ["燃气", "区域已通燃气"], ["供水", "独立水井，深30–100米"],
         ["排水", "独立化粪池"], ["供暖", "燃气/电锅炉、对流取暖器"]],
    prod_h="住宅产品线",
    prod=("规划为统一现代风格的木结构住宅：德式桁架（Fachwerk）、谷仓风（Barn House）、现代科技风、模块化及CLT / CLT Thermo"
          "（制造商：PromStroyLes，pslcomp.ru）。规划产品目录36–180㎡；为快速开盘，合作模式下已形成标准化产品线："),
    prod_head=["户型", "建筑面积", "目标客群"],
    prod_rows=[["紧凑型", "70㎡", "度假屋、二人世界、小家庭"], ["标准型", "95㎡", "主力家庭型产品"], ["舒适型", "120㎡", "改善型客户"]],
    phase="建议首期开发<b>20–30块地</b>，根据销售情况逐步扩大。",
    cap_house1="地块上已建成的样板房——实景建筑。", cap_house2="建筑方案：统一的社区风格。",
    s5="交易条件与合作流程",
    s5_intro=("转让100%住宅用地及其配套设施，并附带设计文件、建筑方案、住宅产品线、市政规划和地籍资料。资产整体出售给单一买方，不拆分。"
              "交易结构（一次性付款、分期、延期付款、通过SPV收购等）经谈判确定。"),
    deal_kv=[("出售报价", "<b>213,338,000卢布</b>（约2.13亿卢布）"),
             ("计算依据", "地籍区块48:05:0880401内200块地，每平方米500卢布"),
             ("移交资料", "总体规划、建筑规范、住宅产品线、市政规划、地籍资料"),
             ("不含", "自然保护区、池塘、庄园、度假基地"),
             ("结算", "付款进度、币种及担保方式（信用证、托管账户等）由双方协商")],
    proc_h="合作流程",
    steps=["签署保密协议（NDA）", "提供投资备忘录、EGRN摘录、PZZ及地籍图", "实地考察（业主陪同）",
           "法律、技术及财务尽职调查", "商定主要条款（Term Sheet / LOI）", "签署正式合同并办理产权过户登记"],
    fn_h="境外投资者须知",
    fn=("外国自然人及法人在俄罗斯取得土地须遵守俄罗斯联邦法律，可协商通过俄罗斯本地公司（SPV）进行收购。所需审批程序、"
        "结算币种（包括人民币）及支付方式一事一议。中国境内企业开展境外投资须依法办理发改委、商务部备案及外汇登记，建议事先咨询专业顾问。"),
    contact_lbl="联系人", contact_name="Expostroy有限责任公司<br/>马克西姆·伊戈列维奇（项目负责人）",
    disc_h="免责声明",
    disc=("本文件仅供参考，属初步资料，不构成《俄罗斯联邦民法典》第437条意义上的公开要约、合同要约或个别投资建议。"
          "所列信息基于业主提供的资料及公开来源，如有变更恕不另行通知。作出投资决定前，须核实最新的EGRN登记、城市规划规定、"
          "土地许可用途、特殊使用条件区（ZOUIT）、道路通行及市政管网接入技术条件。译文仅供参考，以俄文原文为准。"
          "未经业主同意，不得向第三方传播本文件。"),
)

L["vi"] = dict(
    date="Tháng 9/2026",
    company="CÔNG TY TNHH EXPOSTROY", offer="Đề xuất chuyển nhượng tài sản", conf="TÀI LIỆU MẬT",
    kind="BẢN TÓM TẮT ĐẦU TƯ",
    title=["Khu đất xây dựng nhà ở", "riêng lẻ bên sông Voronezh", "«Vozrozhdenie»"],
    loc=["Tỉnh Lipetsk, huyện Dobrovsky, gần làng Preobrazhenovka, Liên bang Nga", "Khu địa chính 48:05:0880401 · cách Moskva khoảng 400 km"],
    kp_head="THÔNG SỐ CHÍNH CỦA ĐỀ XUẤT",
    kp=[("213,3 triệu rúp", "Giá chào bán (giá thị trường do bên bán công bố)"),
        ("42,67 ha", "Tổng diện tích theo địa chính"),
        ("200 thửa", "trong đó 197 thửa đất xây nhà ở riêng lẻ"),
        ("100%", "Chuyển nhượng trọn gói cho một bên mua")],
    cover_foot=["Tài liệu dành cho nhà đầu tư tiềm năng tham khảo sơ bộ, không phải chào bán công khai. Bản dịch để tham khảo, bản tiếng Nga có giá trị ưu tiên.",
                "Bản ghi nhớ đầu tư (IM) đầy đủ được cung cấp sau khi ký thỏa thuận bảo mật (NDA)."],
    head_left="KHU DÂN CƯ VOZROZHDENIE  ·  TÓM TẮT ĐẦU TƯ", head_conf="Tài liệu mật",
    foot="Tài liệu chỉ mang tính thông tin, không phải chào bán công khai (Điều 437 Bộ luật Dân sự Nga).",
    page="Trang {n}/{t}",
    sec="PHẦN {n}",
    s1="Tóm tắt đề xuất đầu tư",
    s1_intro=("Tài sản chào bán là khu đất <b>42,67 ha</b> gồm <b>200 thửa</b> đã đăng ký địa chính, thuộc <b>một chủ sở hữu duy nhất</b>. "
              "Tài sản được chuyển nhượng trọn gói cho một bên mua cùng quy hoạch tổng thể, ý tưởng kiến trúc, dòng sản phẩm nhà, "
              "phương án hạ tầng và hồ sơ địa chính. Việc đất đã tập trung về một chủ giúp nhà đầu tư tránh rủi ro và chi phí gom đất từ nhiều chủ sở hữu."),
    s1_kpi=[("213,3 triệu rúp", "giá chào bán"),
            ("500 rúp/m²", "đơn giá (5,0 triệu rúp/ha)"),
            ("≈1,03 triệu rúp", "giá trung bình mỗi thửa đất ở"),
            ("197 thửa", "đất ở, 40,75 ha")],
    terms_h="Điều kiện chính",
    terms=[("Tài sản", "Khu đất xây dựng nhà ở riêng lẻ «Vozrozhdenie» cùng hạ tầng phục vụ"),
           ("Vị trí", "Tỉnh Lipetsk, huyện Dobrovsky, cách làng Preobrazhenovka 2,5 km; bờ sông Voronezh"),
           ("Khu địa chính", "48:05:0880401"),
           ("Thành phần", "200 thửa: 197 thửa đất xây nhà ở riêng lẻ – IZhS (40,75 ha); 3 thửa hạ tầng và công trình xã hội (1,92 ha)"),
           ("Tình trạng pháp lý", "Toàn bộ đã đăng ký địa chính; một chủ sở hữu; trích lục EGRN cung cấp theo yêu cầu"),
           ("Giá chào bán", "<b>213.338.000 RUB</b> — giá thị trường do bên bán công bố"),
           ("Hình thức giao dịch", "Chuyển nhượng 100% tài sản cho một bên mua; có thể giao dịch có cấu trúc hoặc theo giai đoạn"),
           ("Phạm vi giao dịch", "Các thửa nghỉ dưỡng và bảo tồn (khu bảo tồn, ao hồ, trang viên, khu nghỉ dưỡng) không thuộc phạm vi, vẫn thuộc bên bán")],
    adv_h="Điểm nổi bật đầu tư",
    adv=["<b>Quỹ đất đã tập trung</b> — toàn bộ các thửa thuộc một chủ sở hữu, đã hoàn tất đăng ký địa chính.",
         "<b>Hạ tầng đã xây dựng</b> — đường vào trải nhựa, cầu qua sông Voronezh (đưa vào sử dụng 01/11/2020), điện, khí đốt.",
         "<b>Ý tưởng sản phẩm hoàn chỉnh</b> — quy chuẩn kiến trúc thống nhất, dòng nhà tiêu chuẩn 70–120 m², nhà mẫu đã xây.",
         "<b>Phạm vi giao dịch gọn</b> — chỉ đất ở và hạ tầng phục vụ: ngưỡng đầu tư thấp hơn, thẩm định và hoàn tất nhanh hơn.",
         "<b>Hạ tầng xã hội sẵn có</b> — trong bán kính 2,5 km có trường học, mẫu giáo, trạm y tế, khu thể thao, cửa hàng."],
    s2="Đặc điểm và cơ cấu tài sản",
    s2_intro="Cơ cấu tài sản theo dữ liệu địa chính mới nhất. Giá trị là giá thị trường do bên bán công bố, theo đơn giá thống nhất 500 rúp/m² cho đất ở và hạ tầng.",
    tbl_head=["Mục đích sử dụng", "Số thửa", "Diện tích, ha", "Định giá, RUB", "Tỷ trọng, %"],
    tbl=[["Đất xây nhà ở riêng lẻ (IZhS)", "197", "40,75", "203.717.500", "95,5"],
         ["Hạ tầng và công trình xã hội<br/><font size=7.5 color='#6B727B'>sân thể thao, khu văn phòng, tháp nước</font>", "3", "1,92", "9.620.500", "4,5"],
         ["Tổng cộng", "200", "42,67", "213.338.000", "100,0"]],
    s2_note=("Ghi chú. Giá trị địa chính chính thức theo Rosreestr thấp hơn định giá thị trường; trích lục EGRN được cung cấp theo yêu cầu. "
             "Định giá thị trường phản ánh mức độ sẵn sàng của khu đất và ý tưởng quy hoạch, không thay thế thẩm định giá độc lập theo Luật Liên bang số 135-FZ."),
    zone_cap="Trích đoạn sơ đồ phân khu đã phê duyệt: đất ở, hạ tầng.",
    urb_h="Bối cảnh quy hoạch",
    urb=["Khu đất nằm trong Quy tắc sử dụng đất và xây dựng (PZZ) hiện hành của khu dân cư nông thôn; sơ đồ phân khu và bản đồ địa chính thuộc bộ hồ sơ bàn giao cho bên mua.",
         "Theo ý tưởng quy hoạch mở rộng, sau khi chia thêm các khu dự trữ, diện tích nhà ở có thể đạt 48 ha với 223–227 hộ. Chi tiết trong bản ghi nhớ đầu tư đầy đủ."],
    urb_kv=[("Số thửa IZhS", "197"), ("Diện tích TB thửa IZhS", "≈2.070 m²"), ("Tiềm năng theo quy hoạch", "tối đa 223–227 hộ")],
    s3="Vị trí và giao thông",
    bridge_cap="Cầu qua sông Voronezh trên đường vào khu đất; đưa vào sử dụng ngày 01/11/2020.",
    tr_h="Khả năng tiếp cận",
    tr=[("Vị trí", "Bờ sông Voronezh, bao quanh là rừng"), ("Đường vào", "Đường trải nhựa"), ("Cầu qua sông Voronezh", "Đưa vào sử dụng 01/11/2020"),
        ("TP Lipetsk", "64 km"), ("TP Michurinsk", "50 km"), ("TP Tambov", "120 km"), ("TP Moskva", "khoảng 400 km")],
    soc_h="Hạ tầng xã hội",
    soc=("Cách 2,5 km là làng Preobrazhenovka với trường học, mẫu giáo, bể bơi, khu liên hợp thể thao, trạm y tế, cửa hàng, "
         "kè sông và bãi tắm đang hoạt động. Dự án nằm ngay cạnh hạ tầng đang vận hành, giúp bên mua giảm vốn đầu tư vào công trình xã hội."),
    rep_h="Uy tín địa phương",
    rep="Trong giai đoạn 2011–2020, làng Preobrazhenovka sáu lần đạt giải nhất cuộc thi toàn Nga về khu dân cư nông thôn tiện nghi nhất (hạng mục dưới 400 dân).",
    rep_src="Nguồn: Chính quyền huyện Dobrovsky (admdobroe.ru), mục «Preobrazhenovka»; ru.wikipedia.org — «Preobrazhenovka (tỉnh Lipetsk)»; vozrozhdenie-life.ru (tiếng Nga).",
    s4="Hạ tầng kỹ thuật và ý tưởng sản phẩm",
    eng_h="Hạ tầng kỹ thuật của các thửa",
    eng_head=["Hạng mục", "Giải pháp / thông số"],
    eng=[["Cấp điện", "12,5 kW mỗi thửa"], ["Khí đốt", "Khu vực đã có mạng khí"], ["Cấp nước", "Giếng khoan riêng, sâu 30–100 m"],
         ["Thoát nước", "Bể tự hoại riêng"], ["Sưởi", "Nồi hơi khí đốt / điện, máy sưởi đối lưu"]],
    prod_h="Dòng sản phẩm nhà",
    prod=("Ý tưởng là nhà gỗ cùng phong cách hiện đại: Fachwerk, Barn House, Hi-Tech, nhà mô-đun và CLT / CLT Thermo "
          "(nhà sản xuất: PromStroyLes, pslcomp.ru). Danh mục 36–180 m²; để nhanh chóng mở bán, mô hình hợp tác đã hình thành dòng sản phẩm tiêu chuẩn:"),
    prod_head=["Loại", "Diện tích nhà", "Khách hàng mục tiêu"],
    prod_rows=[["Nhỏ gọn", "70 m²", "Nhà nghỉ cuối tuần, vợ chồng, gia đình nhỏ"], ["Tiêu chuẩn", "95 m²", "Sản phẩm chủ lực cho gia đình"],
               ["Tiện nghi", "120 m²", "Phân khúc tiện nghi"]],
    phase="Quy mô giai đoạn 1 khuyến nghị: <b>20–30 thửa</b>, mở rộng dần theo kết quả bán hàng.",
    cap_house1="Nhà mẫu đã xây trên đất — công trình thật.", cap_house2="Ý tưởng kiến trúc: phong cách thống nhất.",
    s5="Điều kiện giao dịch và quy trình làm việc",
    s5_intro=("Chuyển nhượng 100% khu đất ở và hạ tầng phục vụ cùng hồ sơ thiết kế, ý tưởng kiến trúc, dòng sản phẩm nhà, phương án hạ tầng "
              "và hồ sơ địa chính cho một bên mua, không chia lô. Cấu trúc giao dịch (thanh toán một lần, theo giai đoạn, trả chậm, mua qua SPV) "
              "được xác định qua đàm phán."),
    deal_kv=[("Giá chào bán", "<b>213.338.000 RUB</b>"),
             ("Cơ sở tính", "200 thửa trong khu địa chính 48:05:0880401; 500 rúp/m²"),
             ("Hồ sơ bàn giao", "Quy hoạch tổng thể, quy chuẩn kiến trúc, dòng sản phẩm nhà, phương án hạ tầng, hồ sơ địa chính"),
             ("Không bao gồm", "Khu bảo tồn, ao hồ, trang viên, khu nghỉ dưỡng"),
             ("Thanh toán", "Tiến độ, đồng tiền và hình thức bảo đảm (thư tín dụng, ký quỹ...) do các bên thỏa thuận")],
    proc_h="Quy trình làm việc",
    steps=["Ký thỏa thuận bảo mật (NDA)", "Cung cấp bản ghi nhớ đầu tư, trích lục EGRN, PZZ và bản đồ địa chính", "Khảo sát thực địa (chủ sở hữu tiếp đón)",
           "Thẩm định pháp lý, kỹ thuật và tài chính (due diligence)", "Thống nhất điều khoản chính (Term Sheet / LOI)", "Ký hợp đồng và đăng ký chuyển quyền sở hữu"],
    fn_h="Lưu ý dành cho nhà đầu tư nước ngoài",
    fn=("Việc cá nhân và pháp nhân nước ngoài nhận quyền sở hữu đất tại Nga tuân theo pháp luật Liên bang Nga; có thể thỏa thuận mua thông qua pháp nhân tại Nga (SPV). "
        "Thủ tục phê duyệt, đồng tiền và phương thức thanh toán được thỏa thuận riêng. Doanh nghiệp Việt Nam đầu tư ra nước ngoài cần có Giấy chứng nhận "
        "đăng ký đầu tư ra nước ngoài và đăng ký giao dịch ngoại hối theo quy định — khuyến nghị tham vấn chuyên gia trước."),
    contact_lbl="NGƯỜI LIÊN HỆ", contact_name="Công ty TNHH Expostroy<br/>Ông Maxim Igorevich (phụ trách dự án)",
    disc_h="Giới hạn trách nhiệm",
    disc=("Tài liệu này được soạn thảo chỉ nhằm mục đích thông tin, mang tính sơ bộ và không phải là chào bán công khai theo Điều 437 Bộ luật Dân sự Nga, "
          "đề nghị giao kết hợp đồng hay khuyến nghị đầu tư cá nhân. Thông tin dựa trên dữ liệu của chủ sở hữu và nguồn công khai, có thể thay đổi mà không cần báo trước. "
          "Trước khi quyết định đầu tư cần cập nhật EGRN, quy chế quy hoạch, mục đích sử dụng đất, vùng hạn chế sử dụng (ZOUIT), điều kiện đường vào và điều kiện kỹ thuật "
          "đấu nối hạ tầng. Bản dịch chỉ để tham khảo, bản tiếng Nga có giá trị ưu tiên. Không được phát tán cho bên thứ ba khi chưa có sự đồng ý của chủ sở hữu."),
)

ROMAN = ["I", "II", "III", "IV", "V"]
ZH_NUM = ["一", "二", "三", "四", "五"]

# ----------------------------------------------------------------------------
T = None      # тексты текущего языка
LANG = None


_ORIG_FONT = {}  # исходные имена шрифтов стилей teaser_pdf (R / RM / RB / RI)


def F(name):
    """Имя шрифта текущего языка: 'RB' → 'ko_RB'. Повторно регистрировать 'R' нельзя —
    reportlab оставляет уже зарегистрированный Roboto, и иероглифы пропадают."""
    return f"{LANG}_{name}"


def setup_fonts(lang):
    for name, (fn, idx) in FONT_FILES[lang].items():
        full = f"{lang}_{name}"
        if full not in pdfmetrics.getRegisteredFontNames():
            path = os.path.join(tp.FONTS, fn)
            f = TTFont(full, path, subfontIndex=idx) if idx is not None else TTFont(full, path)
            pdfmetrics.registerFont(f)
    for base in ("R", "RM", "RB", "RI"):
        pdfmetrics.registerFontFamily(f"{lang}_{base}", normal=f"{lang}_{base}", bold=f"{lang}_RB",
                                      italic=f"{lang}_RI", boldItalic=f"{lang}_RB")
    # Стили модуля teaser_pdf переводим на шрифты языка; для китайского — перенос по иероглифам
    wrap = "CJK" if lang == "zh" else None
    for v in vars(tp).values():
        if isinstance(v, ParagraphStyle):
            orig = _ORIG_FONT.setdefault(id(v), v.fontName)
            v.fontName = f"{lang}_{orig}"
            v.wordWrap = wrap


def st(name, **kw):
    kw["fontName"] = F(kw.get("fontName", "R"))
    kw.setdefault("wordWrap", "CJK" if LANG == "zh" else None)
    return tp.st(name, **kw)


def sec_label(i):
    if LANG == "zh":
        return T["sec"].format(n=ZH_NUM[i])
    return T["sec"].format(n=ROMAN[i])


def section(i, title):
    t = Table([[P(sec_label(i), tp.S_SEC_NUM)], [P(title, tp.S_H1)]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LINEBELOW", (0, -1), (-1, -1), 1.2, GRAPHITE), ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
    ]))
    return [t, Spacer(1, 8)]


class Canvas(tp.NumberedCanvas):
    def _chrome(self, total):
        c = self
        c.saveState()
        c.setFillColor(GRAPHITE)
        c.rect(0, PAGE_H - 4 * mm, PAGE_W, 4 * mm, stroke=0, fill=1)
        c.setFont(F("RM"), 7.5)
        c.setFillColor(INK)
        c.drawString(M_L, PAGE_H - 12 * mm, T["head_left"])
        c.setFont(F("R"), 7.5)
        c.setFillColor(STEEL)
        c.drawRightString(PAGE_W - M_R, PAGE_H - 12 * mm, T["head_conf"] + "  ·  " + T["date"])
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        c.line(M_L, PAGE_H - 14.5 * mm, PAGE_W - M_R, PAGE_H - 14.5 * mm)
        c.line(M_L, 14 * mm, PAGE_W - M_R, 14 * mm)
        c.setFont(F("R"), 7)
        c.drawString(M_L, 10 * mm, T["foot"])
        c.setFont(F("RM"), 7.5)
        c.setFillColor(INK)
        c.drawRightString(PAGE_W - M_R, 10 * mm, T["page"].format(n=self._pageNumber, t=total))
        c.restoreState()


def wrap_lines(c, text, font, size, width):
    """Перенос для canvas: по пробелам, а для китайского — по символам."""
    lines, line = [], ""
    tokens = list(text) if LANG == "zh" else text.split()
    sep = "" if LANG == "zh" else " "
    for tok in tokens:
        test = (line + sep + tok) if line else tok
        if c.stringWidth(test, font, size) > width and line:
            lines.append(line)
            line = tok
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def cover(c, doc):
    c.saveState()
    band_h = 118 * mm
    c.setFillColor(INK)
    c.rect(0, PAGE_H - band_h, PAGE_W, band_h, stroke=0, fill=1)
    c.setFillColor(GRAPHITE)
    c.rect(0, PAGE_H - band_h, 8 * mm, band_h, stroke=0, fill=1)
    c.drawImage(os.path.join(tp.IMG, "logo.png"), M_L, PAGE_H - 34 * mm, 16 * mm, 16 * mm, mask="auto")
    light = colors.HexColor("#AEB4BB")
    c.setFillColor(light)
    c.setFont(F("RM"), 8)
    c.drawString(M_L + 20 * mm, PAGE_H - 24 * mm, T["company"])
    c.setFont(F("R"), 8)
    c.drawString(M_L + 20 * mm, PAGE_H - 28.5 * mm, T["offer"])
    c.drawRightString(PAGE_W - M_R, PAGE_H - 24 * mm, T["conf"])
    c.drawRightString(PAGE_W - M_R, PAGE_H - 28.5 * mm, T["date"])
    c.setFont(F("RM"), 9.5)
    c.drawString(M_L, PAGE_H - 56 * mm, T["kind"])
    c.setFillColor(WHITE)
    size = 23 if LANG != "vi" else 24
    c.setFont(F("RB"), size)
    for i, line in enumerate(T["title"]):
        c.drawString(M_L, PAGE_H - (68 + i * 10.5) * mm, line)
    c.setFillColor(colors.HexColor("#C9CED4"))
    c.setFont(F("R"), 9.5)
    c.drawString(M_L, PAGE_H - 100 * mm, T["loc"][0])
    c.drawString(M_L, PAGE_H - 105.5 * mm, T["loc"][1])

    ph_h = 78 * mm
    ph_y = PAGE_H - band_h - ph_h
    im = PILImage.open(os.path.join(tp.IMG, "land-aerial.jpg")).convert("RGB")
    w, h = im.size
    nh = int(w / (PAGE_W / ph_h))
    im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84)
    buf.seek(0)
    c.drawImage(ImageReader(buf), 0, ph_y, PAGE_W, ph_h)

    y0 = ph_y - 13 * mm
    c.setFillColor(INK)
    c.setFont(F("RM"), 8.5)
    c.drawString(M_L, y0, T["kp_head"])
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(1.2)
    c.line(M_L, y0 - 3 * mm, PAGE_W - M_R, y0 - 3 * mm)
    col_w = CW / 4
    for i, (v, lab) in enumerate(T["kp"]):
        x = M_L + i * col_w
        if i:
            c.setStrokeColor(RULE)
            c.setLineWidth(0.5)
            c.line(x - 2 * mm, y0 - 8 * mm, x - 2 * mm, y0 - 30 * mm)
        vs = 17
        while c.stringWidth(v, F("RB"), vs) > col_w - 5 * mm and vs > 10:
            vs -= 0.5
        c.setFillColor(INK)
        c.setFont(F("RB"), vs)
        c.drawString(x, y0 - 14 * mm, v)
        c.setFillColor(STEEL)
        c.setFont(F("R"), 7.6)
        ly = y0 - 20 * mm
        for line in wrap_lines(c, lab, F("R"), 7.6, col_w - 6 * mm):
            c.drawString(x, ly, line)
            ly -= 3.6 * mm

    c.setStrokeColor(RULE)
    c.setLineWidth(0.5)
    c.line(M_L, 26 * mm, PAGE_W - M_R, 26 * mm)
    c.setFillColor(STEEL)
    c.setFont(F("R"), 7)
    ly = 21.5 * mm
    for para in T["cover_foot"]:
        for line in wrap_lines(c, para, F("R"), 7, CW - 40 * mm):
            c.drawString(M_L, ly, line)
            ly -= 3.4 * mm
    c.setFillColor(INK)
    c.setFont(F("RM"), 7.5)
    c.drawRightString(PAGE_W - M_R, 21.5 * mm, "vozrozhdenie-life.ru")
    c.drawRightString(PAGE_W - M_R, 18 * mm, "+7 910 351-13-33")
    c.restoreState()


def story():
    s = [Spacer(1, 1), NextPageTemplate("body"), PageBreak()]
    left_w = tp.S_BODY_L

    # I
    s += section(0, T["s1"])
    s.append(P(T["s1_intro"]))
    s.append(Spacer(1, 8))
    s.append(tp.kpi_row(T["s1_kpi"]))
    s.append(Spacer(1, 10))
    s.append(P(T["terms_h"], tp.S_H2))
    s.append(tp.kv_table(T["terms"], key_w=40 * mm))
    s.append(Spacer(1, 10))
    s.append(P(T["adv_h"], tp.S_H2))
    s += tp.bullets(T["adv"])

    # II
    s.append(PageBreak())
    s += section(1, T["s2"])
    s.append(P(T["s2_intro"]))
    s.append(Spacer(1, 8))
    s.append(tp.grid_table(T["tbl_head"], T["tbl"],
                           [CW - 22 * mm - 27 * mm - 32 * mm - 20 * mm, 22 * mm, 27 * mm, 32 * mm, 20 * mm],
                           right_cols=(1, 2, 3, 4), total=True))
    s.append(Spacer(1, 5))
    s.append(P(T["s2_note"], tp.S_SMALL_J))
    s.append(Spacer(1, 12))
    zone = [tp.photo("zoning-map.jpg", 72 * mm, 82 * mm), Spacer(1, 3), P(T["zone_cap"], tp.S_CAP)]
    txt = [P(T["urb_h"], tp.S_H2), P(T["urb"][0], left_w), Spacer(1, 6), P(T["urb"][1], left_w), Spacer(1, 10),
           tp.kv_table(T["urb_kv"], key_w=44 * mm, width=CW - 79 * mm)]
    s.append(tp.two_col(zone, txt, left_w=72 * mm))

    # III
    s.append(PageBreak())
    s += section(2, T["s3"])
    s.append(KeepTogether(tp.figure("bridge.jpg", CW, 62 * mm, T["bridge_cap"])))
    s.append(Spacer(1, 10))
    loc = tp.kv_table(T["tr"], key_w=36 * mm, width=(CW - 7 * mm) / 2)
    soc = [P(T["soc_h"], tp.S_H2), P(T["soc"], left_w)]
    s.append(tp.two_col([P(T["tr_h"], tp.S_H2), loc], soc))
    s.append(Spacer(1, 12))
    s.append(tp.note_box([P(T["rep_h"], tp.S_H2), P(T["rep"]), Spacer(1, 4), P(T["rep_src"], tp.S_SMALL)]))

    # IV
    s.append(PageBreak())
    s += section(3, T["s4"])
    s.append(P(T["eng_h"], tp.S_H2))
    s.append(tp.grid_table(T["eng_head"], T["eng"], [50 * mm, CW - 50 * mm]))
    s.append(Spacer(1, 12))
    s.append(P(T["prod_h"], tp.S_H2))
    s.append(P(T["prod"]))
    s.append(Spacer(1, 6))
    s.append(tp.grid_table(T["prod_head"], T["prod_rows"], [36 * mm, 40 * mm, CW - 76 * mm]))
    s.append(Spacer(1, 6))
    s.append(P(T["phase"]))
    s.append(Spacer(1, 10))
    half = (CW - 7 * mm) / 2
    s.append(tp.two_col(tp.figure("house-real.jpg", half, 52 * mm, T["cap_house1"]),
                        tp.figure("house-white.jpg", half, 52 * mm, T["cap_house2"])))

    # V
    s.append(PageBreak())
    s += section(4, T["s5"])
    s.append(P(T["s5_intro"]))
    s.append(Spacer(1, 8))
    s.append(tp.kv_table(T["deal_kv"], key_w=40 * mm))
    s.append(Spacer(1, 10))
    s.append(P(T["proc_h"], tp.S_H2))
    num_st = st("n_i18n", fontName="RB", fontSize=10, textColor=WHITE, alignment=TA_CENTER)
    rows = [[P(str(i + 1), num_st), P(t, tp.S_CELL)] for i, t in enumerate(T["steps"])]
    tbl = Table(rows, colWidths=[9 * mm, CW - 9 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRAPHITE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, WHITE), ("LINEBELOW", (1, 0), (1, -1), 0.5, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (1, 0), (1, -1), 8),
    ]))
    s.append(tbl)
    s.append(Spacer(1, 10))
    s.append(tp.note_box([P(T["fn_h"], tp.S_H2), P(T["fn"], tp.S_SMALL_J)]))
    s.append(Spacer(1, 10))
    contact = Table([
        [P(T["contact_lbl"], st("cl_i", fontName="RM", fontSize=8, textColor=colors.HexColor("#AEB4BB"))), ""],
        [P(T["contact_name"], st("cn_i", fontName="RB", fontSize=11.5, leading=16, textColor=WHITE)),
         P("+7 910 351-13-33<br/>expostroy48@mail.ru<br/>vozrozhdenie-life.ru",
           st("cc_i", fontName="RM", fontSize=10, leading=15, textColor=WHITE, alignment=TA_RIGHT))],
    ], colWidths=[CW * 0.6, CW * 0.4])
    contact.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INK), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, 0), 10), ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
    ]))
    s.append(KeepTogether([contact]))
    s.append(Spacer(1, 12))
    s.append(P(T["disc_h"], tp.S_H2))
    s.append(P(T["disc"], tp.S_SMALL_J))
    return s


def build(lang):
    global T, LANG
    T, LANG = L[lang], lang
    setup_fonts(lang)
    out = os.path.join(tp.ROOT, "assets", "docs", f"vozrozhdenie-teaser-{lang}.pdf")
    titles = {"ko": "투자 개요서 — Vozrozhdenie 주거용지", "zh": "投资简介——Vozrozhdenie住宅用地",
              "vi": "Tóm tắt đầu tư — khu đất Vozrozhdenie"}
    doc = BaseDocTemplate(out, pagesize=tp.A4, leftMargin=M_L, rightMargin=M_R, topMargin=tp.M_T,
                          bottomMargin=tp.M_B, title=titles[lang], author="Expostroy LLC",
                          subject="Vozrozhdenie, Lipetsk Oblast, Russia", lang=lang,
                          creator="build/teaser_pdf_i18n.py")
    frame = Frame(M_L, tp.M_B, CW, PAGE_H - tp.M_T - tp.M_B, id="f", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate("cover", frames=[frame], onPage=cover), PageTemplate("body", frames=[frame])])
    doc.build(story(), canvasmaker=Canvas)
    print("OK:", out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    for lg in (sys.argv[1:] or ["ko", "zh", "vi"]):
        build(lg)
