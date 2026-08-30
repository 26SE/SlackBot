from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os, urllib.request

# ── 한글 폰트 다운로드 (NanumGothic) ──────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
FONT_DIR = os.path.join(ROOT_DIR, "assets", "fonts")
REGULAR = os.path.join(FONT_DIR, "NanumGothic.ttf")
BOLD    = os.path.join(FONT_DIR, "NanumGothicBold.ttf")

def dl(url, path):
    if not os.path.exists(path):
        print(f"Downloading {os.path.basename(path)} ...")
        urllib.request.urlretrieve(url, path)

dl("https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf", REGULAR)
dl("https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf", BOLD)

pdfmetrics.registerFont(TTFont("NanumGothic", REGULAR))
pdfmetrics.registerFont(TTFont("NanumGothicBold", BOLD))

# ── 스타일 ────────────────────────────────────────────────────────────────
BASE   = "NanumGothic"
BOLDF  = "NanumGothicBold"
W, H   = A4
BRAND  = colors.HexColor("#A73C3E")
LBRAND = colors.HexColor("#F8EFEF")
GRAY   = colors.HexColor("#F5F5F5")
DKGRAY = colors.HexColor("#444444")

def sty(name, parent, **kw):
    s = ParagraphStyle(name, parent=parent, **kw)
    return s

SS = getSampleStyleSheet()
N  = SS["Normal"]

styles = {
    "title":   sty("T", N, fontName=BOLDF, fontSize=22, textColor=BRAND,
                   spaceAfter=4, leading=28),
    "sub":     sty("S", N, fontName=BASE,  fontSize=11, textColor=DKGRAY,
                   spaceAfter=14),
    "h1":      sty("H1", N, fontName=BOLDF, fontSize=14, textColor=BRAND,
                   spaceBefore=14, spaceAfter=6, leading=20),
    "h2":      sty("H2", N, fontName=BOLDF, fontSize=11, textColor=BRAND,
                   spaceBefore=8, spaceAfter=4),
    "body":    sty("B",  N, fontName=BASE, fontSize=9.5, leading=15,
                   spaceAfter=4, textColor=DKGRAY),
    "code":    sty("C",  N, fontName="Courier", fontSize=8.5, leading=13,
                   backColor=GRAY, leftIndent=8, rightIndent=8,
                   spaceBefore=2, spaceAfter=6),
    "bullet":  sty("BU", N, fontName=BASE, fontSize=9.5, leading=15,
                   leftIndent=14, spaceAfter=3, textColor=DKGRAY),
    "note":    sty("NO", N, fontName=BASE, fontSize=8.5, leading=13,
                   textColor=colors.HexColor("#888888"), spaceAfter=6),
    "warn":    sty("W",  N, fontName=BOLDF, fontSize=9, textColor=colors.HexColor("#B22222"),
                   spaceAfter=4),
    "step_no": sty("SN", N, fontName=BOLDF, fontSize=20, textColor=BRAND,
                   leading=24),
}

def p(text, style="body"): return Paragraph(text, styles[style])
def sp(h=4):               return Spacer(1, h)
def hr():                  return HRFlowable(width="100%", thickness=0.5,
                                             color=colors.HexColor("#CCCCCC"),
                                             spaceAfter=6, spaceBefore=6)
def code(text):
    lines = text.strip().split("\n")
    return [Paragraph(ln.replace(" ", "&nbsp;"), styles["code"]) for ln in lines]

def section_box(title_text, content_items):
    """파란 테두리 섹션 박스"""
    inner = [p(title_text, "h1")] + content_items
    data = [[inner]]
    t = Table(data, colWidths=[W - 40*mm])
    t.setStyle(TableStyle([
        ("BOX",        (0,0), (-1,-1), 1,   BRAND),
        ("LEFTPADDING",(0,0), (-1,-1), 10),
        ("RIGHTPADDING",(0,0),(-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("BACKGROUND", (0,0), (-1,-1), LBRAND),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[LBRAND]),
    ]))
    return t

def note_box(text):
    data = [[Paragraph(f"<b>&#9432;</b>&nbsp;{text}", styles["note"])]]
    t = Table(data, colWidths=[W - 40*mm])
    t.setStyle(TableStyle([
        ("BOX",        (0,0),(-1,-1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND", (0,0),(-1,-1), GRAY),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING", (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    return t

def warn_box(text):
    data = [[Paragraph(f"<b>&#9888; 주의</b>&nbsp;&nbsp;{text}", styles["warn"])]]
    t = Table(data, colWidths=[W - 40*mm])
    t.setStyle(TableStyle([
        ("BOX",        (0,0),(-1,-1), 0.5, colors.HexColor("#B22222")),
        ("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#FFF0F0")),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING", (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    return t

def cmd_table(rows):
    """명령어 표"""
    header = [Paragraph("<b>명령어</b>", styles["body"]),
              Paragraph("<b>설명</b>", styles["body"])]
    data = [header] + [
        [Paragraph(f"<font name='Courier'>{cmd}</font>", styles["body"]),
         Paragraph(desc, styles["body"])]
        for cmd, desc in rows
    ]
    t = Table(data, colWidths=[60*mm, W - 40*mm - 60*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0),  BRAND),
        ("TEXTCOLOR",    (0,0),(-1,0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRAY]),
        ("BOX",          (0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID",    (0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
    ]))
    return t

# ── 문서 구성 ─────────────────────────────────────────────────────────────
OUT = os.path.join(ROOT_DIR, "docs", "slackbot_setup_guide.pdf")
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=20*mm, rightMargin=20*mm,
    topMargin=18*mm, bottomMargin=18*mm,
)

story = []

# ── 표지 ──────────────────────────────────────────────────────────────────
story += [
    sp(20),
    p("Slack Weather &amp; Schedule Bot", "title"),
    p("팀원 셋업 가이드 v1.0", "sub"),
    hr(),
    sp(4),
    p("이 문서는 Slackbot을 본인 PC에서 실행하기 위한 전체 설정 절차를 담고 있습니다.", "body"),
    p("순서대로 따라하면 약 15분 내에 완료할 수 있습니다.", "body"),
    sp(10),
]

# 목차 테이블
toc_data = [
    [Paragraph("<b>단계</b>", styles["body"]), Paragraph("<b>내용</b>", styles["body"])],
    [Paragraph("STEP 1", styles["body"]), Paragraph("사전 준비 (Python, Git)", styles["body"])],
    [Paragraph("STEP 2", styles["body"]), Paragraph("코드 받기 &amp; 패키지 설치", styles["body"])],
    [Paragraph("STEP 3", styles["body"]), Paragraph(".env 파일 설정", styles["body"])],
    [Paragraph("STEP 4", styles["body"]), Paragraph("Slack 앱 생성 및 설정", styles["body"])],
    [Paragraph("STEP 5", styles["body"]), Paragraph("Google Calendar 연동", styles["body"])],
    [Paragraph("STEP 6", styles["body"]), Paragraph("봇 실행 및 명령어 확인", styles["body"])],
]
toc = Table(toc_data, colWidths=[30*mm, W - 40*mm - 30*mm])
toc.setStyle(TableStyle([
    ("BACKGROUND",   (0,0),(-1,0), BRAND),
    ("TEXTCOLOR",    (0,0),(-1,0), colors.white),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LBRAND]),
    ("BOX",          (0,0),(-1,-1), 0.5, BRAND),
    ("INNERGRID",    (0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
    ("LEFTPADDING",  (0,0),(-1,-1), 8),
    ("TOPPADDING",   (0,0),(-1,-1), 5),
    ("BOTTOMPADDING",(0,0),(-1,-1), 5),
]))
story += [toc, sp(10), hr()]

# ── STEP 1 ────────────────────────────────────────────────────────────────
story += [
    p("STEP 1 &nbsp;&nbsp; 사전 준비", "h1"),
    p("아래 항목이 PC에 설치되어 있는지 확인하세요.", "body"),
    sp(4),
    p("&#9654; <b>Python 3.11 이상</b>", "bullet"),
    p("터미널(CMD/PowerShell)에서 아래 명령어로 버전 확인:", "body"),
] + code("python --version") + [
    p("3.11 미만이면 <b>https://python.org</b> 에서 최신 버전을 설치하세요.", "note", ),
    sp(4),
    p("&#9654; <b>Git</b>", "bullet"),
] + code("git --version") + [
    note_box("Git이 없으면 https://git-scm.com 에서 설치"),
    sp(8), hr(),
]

# ── STEP 2 ────────────────────────────────────────────────────────────────
story += [
    p("STEP 2 &nbsp;&nbsp; 코드 받기 &amp; 패키지 설치", "h1"),
    p("&#9654; 레포지토리 클론 (최초 1회)", "h2"),
] + code(
    "git clone https://github.com/se-slackbot/slackbot.git\n"
    "cd slackbot/slackbot"
) + [
    p("&#9654; 이미 받았다면 최신 코드 반영", "h2"),
] + code(
    "git pull origin junseo"
) + [
    p("&#9654; 패키지 설치", "h2"),
] + code(
    "pip install -r requirements.txt"
) + [
    note_box("설치 중 오류가 나면 pip install --upgrade pip 후 재시도"),
    sp(8), hr(),
]

# ── STEP 3 ────────────────────────────────────────────────────────────────
story += [
    p("STEP 3 &nbsp;&nbsp; .env 파일 설정", "h1"),
    p(
        "<b>slackbot/slackbot/</b> 폴더 안에 <b>.env</b> 파일을 만드세요. "
        "(메모장, VSCode 등 아무 텍스트 편집기로 생성 가능)", "body"
    ),
    sp(4),
] + code(
    "SLACK_BOT_TOKEN=xoxb-...          # 본인 Slack 앱 Bot Token\n"
    "SLACK_APP_TOKEN=xapp-...          # 본인 Slack 앱 App-Level Token\n"
    "OPENWEATHER_API_KEY=...           # 날씨 API 키 (팀장에게 받기)\n"
    "DATABASE_URL=postgresql://...     # Supabase URL (팀장에게 받기)\n"
    "CHANNEL_ID=C...                   # 알림 보낼 채널 ID\n"
    "CITY=Seoul                        # 기본 도시\n"
    "NOTIFY_TIME=08:00                 # 데일리 브리프 전송 시각"
) + [
    sp(6),
    warn_box(".env 파일은 절대 GitHub에 올리지 마세요. gitignore에 등록되어 있습니다."),
    sp(6),
    p("<b>CHANNEL_ID 확인 방법</b>", "h2"),
    p("Slack에서 알림 받을 채널 우클릭 → 채널 세부정보 보기 → 맨 아래 채널 ID 복사 (C로 시작)", "body"),
    sp(8), hr(),
]

# ── STEP 4 ────────────────────────────────────────────────────────────────
story += [
    PageBreak(),
    p("STEP 4 &nbsp;&nbsp; Slack 앱 생성 및 설정", "h1"),
    p("각자 본인만의 Slack 앱을 만들어야 합니다. <b>https://api.slack.com/apps</b> 접속", "body"),
    sp(6),

    p("4-1. 앱 생성", "h2"),
    p("&#9312; Create New App 클릭", "bullet"),
    p("&#9313; From scratch 선택", "bullet"),
    p("&#9314; App Name 입력 (예: MyWeatherBot) → 워크스페이스 선택 → Create App", "bullet"),
    sp(6),

    p("4-2. Socket Mode 활성화", "h2"),
    p("좌측 메뉴 Socket Mode → Enable Socket Mode 켜기", "bullet"),
    p("App-Level Token 생성 창이 뜨면:", "bullet"),
    p("&nbsp;&nbsp;&nbsp;Token Name: 아무거나 입력 → connections:write 스코프 추가 → Generate", "bullet"),
    p("&nbsp;&nbsp;&nbsp;생성된 xapp-... 토큰을 복사 → .env의 SLACK_APP_TOKEN에 붙여넣기", "bullet"),
    sp(6),

    p("4-3. Bot Token 설정", "h2"),
    p("좌측 메뉴 OAuth &amp; Permissions → Bot Token Scopes에서 아래 스코프 추가:", "bullet"),
    sp(3),
]

scope_data = [
    [Paragraph("<b>스코프</b>", styles["body"]), Paragraph("<b>용도</b>", styles["body"])],
    [Paragraph("chat:write", styles["body"]),  Paragraph("메시지 전송", styles["body"])],
    [Paragraph("commands",   styles["body"]),  Paragraph("슬래시 커맨드 수신", styles["body"])],
    [Paragraph("im:write",   styles["body"]),  Paragraph("DM 전송 (개인 알림)", styles["body"])],
]
scope_t = Table(scope_data, colWidths=[50*mm, W - 40*mm - 50*mm])
scope_t.setStyle(TableStyle([
    ("BACKGROUND",   (0,0),(-1,0), BRAND),
    ("TEXTCOLOR",    (0,0),(-1,0), colors.white),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LBRAND]),
    ("BOX",          (0,0),(-1,-1), 0.5, BRAND),
    ("INNERGRID",    (0,0),(-1,-1), 0.3, colors.HexColor("#CCDDCC")),
    ("LEFTPADDING",  (0,0),(-1,-1), 6),
    ("TOPPADDING",   (0,0),(-1,-1), 4),
    ("BOTTOMPADDING",(0,0),(-1,-1), 4),
]))
story += [scope_t, sp(6)]

story += [
    p("스코프 추가 후 맨 위로 스크롤 → <b>Install to Workspace</b> 클릭 → 허용", "bullet"),
    p("설치 완료 후 Bot User OAuth Token (xoxb-...) 복사 → .env의 SLACK_BOT_TOKEN에 붙여넣기", "bullet"),
    sp(6),

    p("4-4. Slash Commands 등록", "h2"),
    p("좌측 메뉴 Slash Commands → Create New Command 에서 아래 3개를 각각 등록:", "bullet"),
    sp(3),
    cmd_table([
        ("/날씨1",  "실시간 날씨 조회 (도시명 입력 가능)"),
        ("/시간표1","강의 시간표 조회 / 추가 / 수정 / 삭제"),
        ("/브리핑1","날씨 + 시간표 + 캘린더 즉시 조회"),
        ("/설정",   "도시 / 알림시각 / 타임존 설정"),
        ("/도움말", "전체 명령어 안내"),
    ]),
    sp(4),
    note_box("Socket Mode 사용 시 Request URL은 입력하지 않아도 됩니다."),
    sp(8), hr(),
]

# ── STEP 5 ────────────────────────────────────────────────────────────────
story += [
    PageBreak(),
    p("STEP 5 &nbsp;&nbsp; Google Calendar 연동", "h1"),
    p(
        "Google Calendar 일정을 브리핑에 포함하려면 본인 계정으로 인증이 필요합니다. "
        "인증하지 않아도 봇은 정상 작동하며, 캘린더 섹션만 표시되지 않습니다.", "body"
    ),
    sp(6),

    p("5-1. credentials.json 받기", "h2"),
    p("팀장(준서)에게 <b>credentials.json</b> 파일을 카톡/디스코드로 받아서", "bullet"),
    p("<b>slackbot/slackbot/</b> 폴더 안에 넣으세요.", "bullet"),
    warn_box("credentials.json은 절대 GitHub에 올리지 마세요. 이미 gitignore 처리되어 있습니다."),
    sp(6),

    p("5-2. 테스트 사용자 추가 요청", "h2"),
    p("팀장에게 <b>본인 Gmail 주소</b>를 알려주고 Google Cloud Console 테스트 사용자로 추가 요청", "bullet"),
    p("(추가되기 전에 인증 시도하면 액세스 차단 오류가 납니다)", "bullet"),
    sp(6),

    p("5-3. 본인 Slack User ID 확인", "h2"),
    p("Slack에서 본인 프로필 클릭 → ... (더 보기) → Copy member ID", "bullet"),
    p("U로 시작하는 ID (예: U08XXXXXXXX)", "bullet"),
    sp(6),

    p("5-4. 인증 실행", "h2"),
    p("터미널에서 아래 명령어 실행 (U... 부분에 본인 ID 입력):", "body"),
] + code(
    'python -c "from google_calendar import authorize_user; authorize_user(\'U본인SlackID\')"'
) + [
    p("브라우저가 열리면 Google 계정으로 로그인 → 허용 클릭", "bullet"),
    p("완료되면 <b>token_U본인SlackID.json</b> 파일이 생성되며 인증 완료", "bullet"),
    note_box("브라우저가 자동으로 안 열리면 터미널에 출력된 URL을 복사해 브라우저 주소창에 붙여넣기"),
    sp(8), hr(),
]

# ── STEP 6 ────────────────────────────────────────────────────────────────
story += [
    p("STEP 6 &nbsp;&nbsp; 봇 실행 및 명령어 확인", "h1"),
    p("&#9654; 봇 실행", "h2"),
] + code(
    "cd slackbot/slackbot\n"
    "python main.py"
) + [
    p("아래와 같은 로그가 나오면 정상 실행:", "body"),
] + code(
    "Bolt app is running!"
) + [
    sp(6),
    p("&#9654; 전체 명령어 목록", "h2"),
    sp(3),
    cmd_table([
        ("/날씨1",                   "현재 날씨 조회 (기본: 설정된 도시)"),
        ("/날씨1 [도시명]",           "특정 도시 날씨 조회 (예: /날씨1 Busan)"),
        ("/시간표1",                  "오늘 강의 목록 조회"),
        ("/시간표1 내일",             "내일 강의 목록 조회"),
        ("/시간표1 추가 [요일] [시작] [종료] [과목명]", "시간표 추가"),
        ("/시간표1 수정 [ID] [항목=값]","시간표 수정"),
        ("/시간표1 삭제 [ID]",        "시간표 삭제"),
        ("/브리핑1",                  "날씨 + 시간표 + 캘린더 즉시 조회"),
        ("/설정 [도시] [HH:MM] [timezone]", "개인 설정 변경"),
        ("/도움말",                   "전체 명령어 안내"),
    ]),
    sp(8),

    p("&#9654; 시간표 추가 예시", "h2"),
] + code(
    "/시간표1 추가 월 09:00 10:30 운영체제 공학관301호 김교수\n"
    "/시간표1 추가 수 13:00 14:30 \"소프트웨어공학\" E동201호"
) + [
    sp(6),
    p("&#9654; 개인 설정 예시", "h2"),
] + code(
    "/설정 Seoul 08:30 Asia/Seoul"
) + [
    sp(8), hr(),
    sp(6),
    p("문의: 준서 (eyesome25@gmail.com)", "note"),
]

# ── 빌드 ─────────────────────────────────────────────────────────────────
doc.build(story)
print(f"\nPDF 생성 완료: {OUT}")
