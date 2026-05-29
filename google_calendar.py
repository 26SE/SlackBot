from __future__ import annotations
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from database import get_google_token, save_google_token, resolve_db_path

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_DIR = os.getenv("GOOGLE_TOKEN_DIR", os.path.join(os.path.dirname(__file__), "data", "google_tokens"))

# DATABASE_URL이 있으면 DB 저장, 없으면 파일 저장 (로컬 개발 호환)
_USE_DB_TOKENS = bool(os.getenv("DATABASE_URL"))


def _token_file(user_id: str | None) -> str:
    os.makedirs(TOKEN_DIR, exist_ok=True)
    if user_id:
        return os.path.join(TOKEN_DIR, f"token_{user_id}.json")
    return os.path.join(TOKEN_DIR, "token.json")


def _load_token_json(user_id: str | None) -> str | None:
    """DB 또는 파일에서 토큰 JSON 문자열 로드."""
    key = user_id or "default"
    if _USE_DB_TOKENS:
        return get_google_token(key)
    token_file = _token_file(user_id)
    if os.path.exists(token_file):
        with open(token_file) as f:
            return f.read()
    return None


def _save_token_json(user_id: str | None, token_json: str) -> None:
    """DB 또는 파일에 토큰 JSON 문자열 저장."""
    key = user_id or "default"
    if _USE_DB_TOKENS:
        save_google_token(key, token_json)
    else:
        with open(_token_file(user_id), "w") as f:
            f.write(token_json)


def _get_credentials(user_id: str | None = None) -> Credentials | None:
    creds = None

    token_json = _load_token_json(user_id)
    if token_json:
        creds = Credentials.from_authorized_user_info(
            __import__("json").loads(token_json), SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_token_json(user_id, creds.to_json())
        else:
            # 토큰 없음 → 해당 사용자는 미인증 상태
            if not os.path.exists(CREDENTIALS_FILE):
                logger.warning("credentials.json 없음 - Google Calendar 연동 비활성화")
            else:
                logger.info("Google Calendar 미인증 사용자: %s", user_id)
            return None

    return creds


def fetch_today_events(timezone: str = "Asia/Seoul", user_id: str | None = None) -> list[dict]:
    """오늘 Google Calendar 일정 가져오기 (사용자별 토큰 사용)"""
    try:
        creds = _get_credentials(user_id)
        if not creds:
            return []

        service = build("calendar", "v3", credentials=creds)
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=0)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = []
        for item in events_result.get("items", []):
            start_val = item["start"].get("dateTime", item["start"].get("date", ""))

            if "T" in start_val:
                dt = datetime.fromisoformat(start_val)
                time_str = dt.strftime("%H:%M")
            else:
                time_str = "종일"

            events.append({
                "summary": item.get("summary", "(제목 없음)"),
                "time": time_str,
                "location": item.get("location", ""),
            })

        logger.info("Google Calendar 일정 %d개 가져옴 (user=%s)", len(events), user_id)
        return events

    except Exception as e:
        logger.error("Google Calendar 조회 실패: %s (user=%s)", e, user_id)
        return []


def authorize_user(user_id: str) -> bool:
    """사용자 Google Calendar OAuth 인증 — 로컬 실행 시 브라우저 열림, 토큰은 DB/파일에 저장"""
    if not os.path.exists(CREDENTIALS_FILE):
        logger.error("credentials.json 없음")
        return False
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        _save_token_json(user_id, creds.to_json())
        logger.info("Google Calendar 인증 완료: %s (DB=%s)", user_id, _USE_DB_TOKENS)
        return True
    except Exception as e:
        logger.error("Google Calendar 인증 실패: %s", e)
        return False
