from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

FONT_DIR = os.path.dirname(__file__)
REGULAR = os.path.join(FONT_DIR, "NanumGothic.ttf")
BOLD    = os.path.join(FONT_DIR, "NanumGothicBold.ttf")

pdfmetrics.registerFont(TTFont("NanumGothic", REGULAR))
pdfmetrics.registerFont(TTFont("NanumGothicBold", BOLD))

W, H   = A4
BLUE   = colors.HexColor("#1E6FD9")
LBLUE  = colors.HexColor("#EBF2FF")
GRAY   = colors.HexColor("#F5F5F5")
DKGRAY = colors.HexColor("#444444")
GREEN  = colors.HexColor("#1A7A4A")

SS = getSampleStyleSheet()
N  = SS["Normal"]

def sty(name, parent, **kw):
    return ParagraphStyle(name, parent=parent, **kw)

styles = {
    "title":  sty("T",  N, fontName="NanumGothicBold", fontSize=20, textColor=BLUE, spaceAfter=4, leading=26),
    "sub":    sty("S",  N, fontName="NanumGothic",     fontSize=10, textColor=DKGRAY, spaceAfter=12),
    "h1":     sty("H1", N, fontName="NanumGothicBold", fontSize=13, textColor=BLUE, spaceBefore=12, spaceAfter=5, leading=18),
    "h2":     sty("H2", N, fontName="NanumGothicBold", fontSize=10, textColor=GREEN, spaceBefore=8, spaceAfter=3),
    "body":   sty("B",  N, fontName="NanumGothic",     fontSize=9.5, leading=15, spaceAfter=4, textColor=DKGRAY),
    "code":   sty("C",  N, fontName="Courier",         fontSize=8.5, leading=13, backColor=GRAY,
                  leftIndent=8, rightIndent=8, spaceBefore=2, spaceAfter=6),
    "bullet": sty("BU", N, fontName="NanumGothic",     fontSize=9.5, leading=15, leftIndent=14, spaceAfter=3, textColor=DKGRAY),
    "note":   sty("NO", N, fontName="NanumGothic",     fontSize=8.5, leading=13, textColor=colors.HexColor("#888888"), spaceAfter=6),
    "warn":   sty("W",  N, fontName="NanumGothicBold", fontSize=9,   textColor=colors.HexColor("#B22222"), spaceAfter=4),
    "num":    sty("NU", N, fontName="NanumGothicBold", fontSize=16,  textColor=BLUE, leading=20),
}

def p(text, style="body"): return Paragraph(text, styles[style])
def sp(h=4):               return Spacer(1, h)
def hr():                  return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceAfter=6, spaceBefore=6)

def code(text):
    lines = text.strip().split("\n")
    return [Paragraph(ln.replace(" ", "&nbsp;"), styles["code"]) for ln in lines]

def step_box(num, title, items):
    inner = [
        Paragraph(f"<b>STEP {num}</b>&nbsp;&nbsp;{title}", styles["h1"])
    ] + items
    data = [[inner]]
    t = Table(data, colWidths=[W - 40*mm])
    t.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 1.2, BLUE),
        ("LEFTPADDING",  (0,0),(-1,-1), 12),
        ("RIGHTPADDING", (0,0),(-1,-1), 12),
        ("TOPPADDING",   (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("BACKGROUND",   (0,0),(-1,-1), LBLUE),
    ]))
    return t

def note_box(text):
    data = [[Paragraph(f"&#9432;&nbsp;&nbsp;{text}", styles["note"])]]
    t = Table(data, colWidths=[W - 40*mm])
    t.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND",   (0,0),(-1,-1), GRAY),
        ("LEFTPADDING",  (0,0),(-1,-1), 8),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    return t

def warn_box(text):
    data = [[Paragraph(f"&#9888;&nbsp;<b>주의</b>&nbsp;&nbsp;{text}", styles["warn"])]]
    t = Table(data, colWidths=[W - 40*mm])
    t.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 0.5, colors.HexColor("#B22222")),
        ("BACKGROUND",   (0,0),(-1,-1), colors.HexColor("#FFF0F0")),
        ("LEFTPADDING",  (0,0),(-1,-1), 8),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    return t

OUT = os.path.join(FONT_DIR, "google_auth_guide.pdf")
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=20*mm, rightMargin=20*mm,
    topMargin=18*mm, bottomMargin=18*mm,
)

story = []

# 표지
story += [
    sp(10),
    p("Google Calendar 연동 가이드", "title"),
    p("Slack Weather &amp; Schedule Bot — 조원용", "sub"),
    hr(),
    sp(4),
    p("이 가이드를 따라하면 슬랙봇 브리핑에 본인 Google Calendar 일정이 표시됩니다.", "body"),
    p("준서가 서버에 credentials.json을 올린 후 아래 절차를 진행하세요.", "body"),
    sp(16),
]

# STEP 1
story += [
    step_box(1, "코드 및 패키지 준비", [
        sp(4),
        p("&#9654; 레포지토리를 아직 받지 않았다면:", "h2"),
    ] + code(
        "git clone https://github.com/se-slackbot/slackbot.git\n"
        "cd slackbot"
    ) + [
        p("&#9654; 이미 있다면 최신 코드로 업데이트:", "h2"),
    ] + code(
        "git pull"
    ) + [
        p("&#9654; 패키지 설치:", "h2"),
    ] + code(
        "pip install -r requirements.txt"
    ) + [sp(4)]),
    sp(12),
]

# STEP 2
story += [
    step_box(2, "credentials.json 파일 받기", [
        sp(4),
        p("준서에게 <b>credentials.json</b> 파일을 카톡 또는 디스코드로 받으세요.", "body"),
        p("받은 파일을 아래 경로에 넣으세요:", "body"),
    ] + code(
        "slackbot/credentials.json"
    ) + [
        sp(4),
        warn_box("credentials.json은 절대 GitHub에 올리지 마세요."),
    ]),
    sp(12),
]

# STEP 3
story += [
    step_box(3, "본인 Slack User ID 확인", [
        sp(4),
        p("&#9312; Slack에서 본인 프로필 사진 클릭", "bullet"),
        p("&#9313; <b>프로필 보기</b> 클릭", "bullet"),
        p("&#9314; 오른쪽 상단 <b>... (더보기)</b> 클릭", "bullet"),
        p("&#9315; <b>멤버 ID 복사</b> 클릭", "bullet"),
        sp(4),
        p("<b>U</b>로 시작하는 ID가 복사됩니다. (예: U08AB1CD2EF)", "body"),
        note_box("이 ID를 메모해두세요. 다음 단계에서 사용합니다."),
    ]),
    sp(12),
]

# STEP 4
story += [
    step_box(4, "인증 실행", [
        sp(4),
        p("터미널에서 slackbot 폴더 안으로 이동 후 아래 명령어 실행:", "body"),
        p("(U본인SlackID 부분을 STEP 3에서 복사한 ID로 교체)", "body"),
    ] + code(
        'python -c "from google_calendar import authorize_user; authorize_user(\'U본인SlackID\')"'
    ) + [
        sp(4),
        p("&#9654; 브라우저가 자동으로 열리면:", "h2"),
        p("&#9312; 본인 Google 계정 선택", "bullet"),
        p("&#9313; <b>계속</b> 또는 <b>허용</b> 클릭", "bullet"),
        p("&#9314; 브라우저에 <b>The authentication flow has completed</b> 메시지 확인", "bullet"),
        sp(4),
        note_box("브라우저가 자동으로 안 열리면 터미널에 출력된 URL을 복사해서 브라우저 주소창에 붙여넣기"),
    ]),
    sp(12),
]

# STEP 5
story += [
    step_box(5, "토큰 파일을 준서에게 전달", [
        sp(4),
        p("인증 완료 후 아래 경로에 토큰 파일이 생성됩니다:", "body"),
    ] + code(
        "slackbot/data/google_tokens/token_U본인SlackID.json"
    ) + [
        sp(4),
        p("이 파일을 준서에게 카톡 또는 디스코드로 전달하세요.", "body"),
        p("준서가 서버에 올리면 브리핑에 본인 Google Calendar 일정이 표시됩니다.", "body"),
        sp(4),
        warn_box("token 파일도 개인 인증 정보입니다. GitHub에 올리지 마세요."),
    ]),
    sp(16),
]

story += [
    hr(),
    p("문의: 준서 (eyesome25@gmail.com)", "note"),
]

doc.build(story)
print(f"\nPDF 생성 완료: {OUT}")
