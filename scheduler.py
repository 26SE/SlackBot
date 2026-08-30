from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config_store import ConfigStore
from weather.fetcher import fetch_weather
from schedule.repository import get_courses_for_date
from slack.message_builder import build_daily_message
from slack.client import post_daily_brief
from google_calendar import fetch_today_events

logger = logging.getLogger(__name__)

DEFAULT_TIMEZONE = "Asia/Seoul"
# ponytail: 프로세스 메모리 기반 중복 방지. 사용자당 1건이라 정리 로직이 필요 없다.
# 다중 인스턴스로 늘리면 DB 로 옮길 것.
_sent_briefs: dict[str, str] = {}


def is_valid_timezone(timezone: str) -> bool:
    try:
        ZoneInfo(timezone)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False


def valid_timezone(timezone: str | None) -> str:
    """알 수 없는 타임존은 기본값으로 대체한다."""
    if not timezone:
        return DEFAULT_TIMEZONE
    if is_valid_timezone(timezone):
        return timezone
    logger.warning("올바르지 않은 타임존, 기본값 사용: %s", timezone)
    return DEFAULT_TIMEZONE


def build_brief(
    api_key: str,
    db_path: str | None,
    city: str,
    timezone: str = DEFAULT_TIMEZONE,
    user_id: str | None = None,
) -> list[dict]:
    """날씨 + 시간표 + 캘린더를 모은 슬랙 블록. user_id 가 없으면 공용 시간표."""
    weather = fetch_weather(city, api_key)
    courses = get_courses_for_date(db_path, datetime.now(ZoneInfo(timezone)).date(), user_id)
    return build_daily_message(
        weather,
        courses,
        timezone=timezone,
        calendar_events=fetch_today_events(timezone=timezone, user_id=user_id),
    )


def run_brief(
    app,
    channel: str,
    api_key: str,
    db_path: str | None,
    city: str,
    timezone: str = DEFAULT_TIMEZONE,
    user_id: str | None = None,
) -> bool:
    """브리프를 만들어 channel 로 전송한다."""
    logger.info("데일리 브리프 실행 시작: channel=%s user=%s", channel, user_id)
    try:
        blocks = build_brief(api_key, db_path, city, timezone, user_id)
    except Exception as e:
        logger.error("브리프 정보 수집 실패: %s user=%s", e, user_id)
        _notify_error(app, channel, f"브리프 정보 수집 실패: {e}")
        return False

    try:
        post_daily_brief(app, channel, blocks)
        return True
    except Exception as e:
        logger.error("메시지 전송 최종 실패: %s user=%s", e, user_id)
        return False


def _run_due_user_briefs(app, config_store: ConfigStore, api_key: str, db_path: str | None) -> None:
    try:
        configs = config_store.list_all()
    except Exception as e:
        logger.error("유저 설정 목록 조회 실패: %s", e)
        return

    for config in configs:
        user_id = config["slack_user_id"]
        key = _due_key(config)
        if key is None or _sent_briefs.get(user_id) == key:
            continue
        logger.info("유저 브리프 발송 시도: %s %s", user_id, key)
        try:
            sent = run_brief(
                app,
                user_id,
                api_key,
                db_path,
                config.get("city") or "Seoul",
                valid_timezone(config.get("timezone")),
                user_id,
            )
        except Exception as e:
            logger.error("유저 브리프 발송 실패: %s user=%s", e, user_id)
            continue
        if sent:
            _sent_briefs[user_id] = key


def _due_key(config: dict) -> str | None:
    """지금이 이 유저의 알림 시각이면 '날짜 시각' 키를, 아니면 None 을 반환."""
    notify_time = str(config.get("notify_time", ""))[:5]
    now = datetime.now(ZoneInfo(valid_timezone(config.get("timezone"))))
    return f"{now:%Y-%m-%d} {notify_time}" if notify_time == f"{now:%H:%M}" else None


def _notify_error(app, channel_id: str, message: str) -> None:
    try:
        app.client.chat_postMessage(channel=channel_id, text=f":rotating_light: [오류] {message}")
    except Exception:
        pass


def create_scheduler(
    app,
    channel_id: str,
    api_key: str,
    db_path: str | None,
    city: str,
    notify_time: str,
    config_store: ConfigStore | None = None,
) -> BackgroundScheduler:
    hour, minute = (int(part) for part in notify_time.split(":"))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("notify_time must be HH:MM")

    scheduler = BackgroundScheduler(timezone=DEFAULT_TIMEZONE)
    scheduler.add_job(
        run_brief,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=DEFAULT_TIMEZONE),
        args=[app, channel_id, api_key, db_path, city],
        id="daily_brief",
        replace_existing=True,
        misfire_grace_time=300,
        max_instances=1,
    )
    logger.info("스케줄러 등록: 매일 %02d:%02d", hour, minute)

    if config_store is not None:
        scheduler.add_job(
            _run_due_user_briefs,
            trigger=CronTrigger(second=0, timezone=DEFAULT_TIMEZONE),
            args=[app, config_store, api_key, db_path],
            id="user_daily_briefs",
            replace_existing=True,
            misfire_grace_time=30,
            max_instances=1,
        )
        logger.info("사용자별 데일리 브리프 스케줄러 등록 완료")
    return scheduler
