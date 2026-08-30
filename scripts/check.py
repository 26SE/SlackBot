import sqlite3
import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
db = os.path.join(ROOT_DIR, "data", "bot.db")
conn = sqlite3.connect(db)

rows = conn.execute("SELECT slack_user_id, city, notify_time, timezone FROM user_config").fetchall()
print(f"user_config 레코드 수: {len(rows)}")
for r in rows:
    print(f"  user={r[0]} city={r[1]} time={r[2]} tz={r[3]}")

if not rows:
    print("  → 저장된 설정 없음. /설정1 명령어가 DB에 저장 안 된 상태.")
