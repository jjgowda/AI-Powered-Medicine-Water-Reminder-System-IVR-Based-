import time
from datetime import datetime, timedelta
from utils.json_db import read_json, append_json, write_json
from call_handler import make_call

CALL_LOG_FILE = "call_history.json"
GRACE_MINUTES = 2          # for medicine reminders
SLEEP_SECONDS = 20         # scheduler tick interval

def parse_time(hhmm: str):
    return datetime.strptime(hhmm, "%H:%M").time()

def already_called_today(call_history, reminder_id, date_str):
    return any(
        h["reminder_id"] == reminder_id and h["date"] == date_str
        for h in call_history
    )

def run_scheduler():
    print("⏰ Scheduler started (medicine + water mode)")

    while True:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        reminders = read_json("reminders.json")
        users = read_json("users.json")
        call_history = read_json(CALL_LOG_FILE)

        user_map = {u["id"]: u for u in users}

        print(f"\n🕒 Tick {now.strftime('%H:%M:%S')} | Reminders: {len(reminders)}")

        calls_to_make = []

        # ---------------- PHASE 1: DECIDE CALLS ----------------
        for rem in reminders:
            if not rem.get("active", True):
                continue

            if rem["user_id"] not in user_map:
                print(f"❌ Missing user for reminder {rem['id']}")
                continue

            # ---------- MEDICINE ----------
            if rem["type"] == "medicine":
                if already_called_today(call_history, rem["id"], today):
                    print(f"✅ Medicine already called today: {rem['id']}")
                    continue

                med_time = parse_time(rem["schedule_time"])
                med_dt = datetime.combine(now.date(), med_time)

                delta_min = abs((now - med_dt).total_seconds()) / 60

                print(
                    f"🔎 MED | {rem['id']} | "
                    f"Sched={rem['schedule_time']} | Δmin={round(delta_min, 2)}"
                )

                if delta_min <= GRACE_MINUTES:
                    calls_to_make.append(rem)

            # ---------- WATER (EVERY N MINUTES) ----------
            elif rem["type"] == "water":
                interval = rem.get("interval_minutes", 120)
                last = rem.get("last_triggered")

                if last:
                    last_dt = datetime.fromisoformat(last)
                    elapsed_min = (now - last_dt).total_seconds() / 60
                else:
                    elapsed_min = interval + 1  # trigger immediately first time

                print(
                    f"🔎 WATER | {rem['id']} | "
                    f"Elapsed={round(elapsed_min, 1)}min / {interval}min"
                )

                if elapsed_min >= interval:
                    calls_to_make.append(rem)

        # ---------------- PHASE 2: MAKE CALLS ----------------
        for rem in calls_to_make:
            user = user_map[rem["user_id"]]

            label = "WATER" if rem["type"] == "water" else "MEDICINE"

            print(
                f"📞 CALLING [{label}] | "
                f"User={user['name']} | "
                f"Phone={user['phone']}"
            )

            make_call(user, rem)

            # log call
            append_json(CALL_LOG_FILE, {
                "reminder_id": rem["id"],
                "user_id": rem["user_id"],
                "type": rem["type"],
                "date": today,
                "called_at": now.isoformat()
            })

            # update last_triggered for water
            if rem["type"] == "water":
                rem["last_triggered"] = now.isoformat()
                write_json("reminders.json", reminders)

        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    run_scheduler()
