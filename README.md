# Slack Weather & Schedule Bot

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Slack](https://img.shields.io/badge/Slack-Bolt-4A154B?logo=slack&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-ICS_API-009688?logo=fastapi&logoColor=white)

날씨, 강의 시간표, Google Calendar 일정을 한 번에 모아 Slack으로 전달하는 개인 일정 봇입니다. 사용자는 Slack 명령어로 시간표와 알림 설정을 관리하고, 저장한 시간표를 ICS 캘린더로 구독할 수 있습니다.

## 핵심 기능

- 매일 지정 시각에 날씨·강의·Google Calendar 일정을 채널 또는 개인 DM으로 전송
- 사용자별 도시, 알림 시각, 타임존, 개인 시간표 저장
- Slack에서 날씨 조회와 시간표 추가·수정·삭제
- 개인 시간표를 반복 일정이 포함된 ICS 파일로 제공
- SQLite와 PostgreSQL 지원
- 날씨 캐시 폴백과 Slack 메시지 재시도

## 주요 명령어

| 명령어 | 설명 |
|---|---|
| `/weather [도시]` | 현재 날씨와 강수확률 조회 |
| `/schedule [오늘\|내일\|YYYY-MM-DD]` | 날짜별 시간표 조회 |
| `/schedule 추가 <요일> <시작> <종료> <과목> [장소] [교수] [메모]` | 개인 일정 추가 |
| `/schedule 수정 <ID> <field=value>...` | 개인 일정 수정 |
| `/schedule 삭제 <ID>` | 개인 일정 삭제 |
| `/config [도시] [HH:MM] [timezone]` | 개인 알림 설정 조회 또는 변경 |
| `/brief` | 현재 날씨·시간표·캘린더 일정 즉시 조회 |
| `/bot-help` | 도움말 표시 |

`/날씨`, `/시간표`, `/설정`, `/브리핑`, `/도움말` 한글 별칭도 지원합니다. `/날씨1`, `/시간표1`, `/설정1`, `/브리핑1`도 등록할 수 있습니다.

```text
/시간표 추가 월 09:00 10:30 알고리즘 공학관401호 박교수
/시간표 수정 12 room="공학관 301호" start=10:00 end=11:30
/설정 Seoul 07:00 Asia/Seoul
/브리핑
```

## 빠른 시작

Python 3.11 이상이 필요합니다.

```bash
cd SlackBot
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

`.env`에 필수 값을 설정합니다.

```dotenv
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
OPENWEATHER_API_KEY=...
SLACK_CHANNEL_ID=C0XXXXXXXXX
CALENDAR_ACCESS_TOKEN=충분히-긴-임의의-값
```

Slack App에는 `chat:write`, `commands`, `im:write` Bot Token Scope와 사용할 Slash Command를 등록합니다. HTTP 모드의 Request URL은 `https://<도메인>/slack/events`입니다.

```bash
python main.py
```

`SLACK_APP_TOKEN`이 있으면 Socket Mode로, 없으면 HTTP 모드로 실행됩니다. 스케줄러와 ICS API도 같은 프로세스에서 함께 시작됩니다.

## 환경 변수

| 변수 | 필수 | 기본값 / 용도 |
|---|---|---|
| `SLACK_BOT_TOKEN` | 예 | Slack Bot Token |
| `SLACK_SIGNING_SECRET` | 예 | Slack 요청 서명 검증 |
| `OPENWEATHER_API_KEY` | 예 | OpenWeatherMap API 키 |
| `SLACK_CHANNEL_ID` | 예 | 공용 데일리 브리프 채널 |
| `SLACK_APP_TOKEN` | 아니요 | 설정 시 Socket Mode 사용 |
| `NOTIFY_TIME` | 아니요 | 공용 브리프 시각, `07:00` |
| `DEFAULT_CITY` | 아니요 | 공용 브리프 도시, `Seoul` |
| `DATABASE_URL` | 아니요 | 설정 시 PostgreSQL 사용 |
| `DB_PATH` | 아니요 | SQLite 경로, `./data/bot.db` |
| `CALENDAR_ACCESS_TOKEN` | 아니요 | ICS 접근 토큰. 없으면 다운로드 요청에 `503` 반환 |
| `GOOGLE_TOKEN_DIR` | 아니요 | OAuth 토큰 경로, `./data/google_tokens` |
| `PORT` | 아니요 | Slack HTTP 포트, `3001` |
| `API_PORT` | 아니요 | ICS API 포트, `3000` |
| `DEBUG` | 아니요 | 설정 시 DEBUG 로그 활성화 |

`DATABASE_URL`이 설정되어 있으면 `DB_PATH`보다 우선합니다.

## Google Calendar 연동

Google OAuth 클라이언트 파일 `credentials.json`을 프로젝트 루트에 둔 뒤 사용자 인증을 실행합니다.

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from google_calendar import authorize_user; authorize_user('SLACK_USER_ID')"
```

SQLite 환경에서는 토큰을 파일로 저장합니다. PostgreSQL 환경으로 토큰을 옮기려면 다음 스크립트를 사용합니다.

```bash
python scripts/upload_google_token.py <slack_user_id>
```

Google Calendar가 연결되지 않았거나 조회에 실패해도 날씨와 시간표 브리프는 계속 전송됩니다.

## ICS 캘린더

```text
GET /calendar/{slack_user_id}.ics?token={CALENDAR_ACCESS_TOKEN}
GET /health
```

ICS에는 사용자가 직접 저장한 시간표가 매주 반복 일정으로 포함됩니다. `CALENDAR_ACCESS_TOKEN`이 없으면 캘린더 API는 `503`, 토큰이 다르면 `403`을 반환합니다.

## 프로젝트 구조

```text
SlackBot/
├── main.py                 # 애플리케이션 진입점
├── scheduler.py            # 채널·사용자별 브리프 스케줄러
├── api.py                  # ICS API
├── database.py             # SQLite/PostgreSQL 연결
├── config_store.py         # 사용자 설정 저장소
├── google_calendar.py      # Google Calendar 연동
├── slack/                  # 명령어, 메시지, 전송 클라이언트
├── schedule/               # 시간표 저장소와 포맷터
├── weather/                # 날씨 조회와 포맷터
├── tests/                  # 자동 테스트
├── scripts/                # 운영·문서 생성 스크립트
├── docs/                   # 설계·배포 문서와 가이드
└── assets/fonts/           # PDF 생성용 폰트
```

## 테스트

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

GitHub Actions는 Python 3.11, 3.12, 3.13에서 전체 테스트를 실행합니다.

## 배포 및 문서

- Railway: [railway.toml](railway.toml), [Procfile](Procfile)
- Oracle Cloud: [배포 가이드](docs/oracle-cloud-setup.md)
- 상세 설계: [DESIGN_SPEC.md](docs/DESIGN_SPEC.md)

`.env`, `credentials.json`, `data/`, Google OAuth 토큰은 Git에 커밋하지 않습니다.
