import sqlite3
import os
import re
from datetime import datetime, timedelta
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cengfitness.db")


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    salt            TEXT NOT NULL,
    name            TEXT,
    weight_kg       REAL,
    height_cm       REAL,
    age             INTEGER,
    gender          TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS food_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    food_name       TEXT NOT NULL,
    calories        INTEGER NOT NULL,
    protein_g       REAL DEFAULT 0,
    carbs_g         REAL DEFAULT 0,
    fat_g           REAL DEFAULT 0,
    source          TEXT DEFAULT 'manual',
    logged_at       TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exercise_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    exercise_name   TEXT NOT NULL,
    duration_min    INTEGER NOT NULL,
    calories_burned INTEGER NOT NULL,
    met_value       REAL,
    logged_at       TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS body_measurements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    weight_kg       REAL,
    chest_cm        REAL,
    waist_cm        REAL,
    hip_cm          REAL,
    arm_cm          REAL,
    thigh_cm        REAL,
    body_fat_pct    REAL,
    note            TEXT,
    logged_at       TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_food_user_date ON food_log(user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_exercise_user_date ON exercise_log(user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_measurements_user_date ON body_measurements(user_id, logged_at);
"""


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        cur = conn.execute("PRAGMA table_info(exercise_log)")
        existing_cols = [row["name"] for row in cur.fetchall()]
        if "sets" not in existing_cols:
            conn.execute("ALTER TABLE exercise_log ADD COLUMN sets INTEGER DEFAULT 0")
        if "reps" not in existing_cols:
            conn.execute("ALTER TABLE exercise_log ADD COLUMN reps INTEGER DEFAULT 0")
        if "weight_kg" not in existing_cols:
            conn.execute("ALTER TABLE exercise_log ADD COLUMN weight_kg REAL DEFAULT 0")


def create_user(email, password_hash, salt, name, weight_kg, height_cm, age, gender):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO users (email, password_hash, salt, name, weight_kg, height_cm, age, gender)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (email.lower().strip(), password_hash, salt, name, weight_kg, height_cm, age, gender)
        )
        return cur.lastrowid


def get_user_by_email(email):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower().strip(),)
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def update_user_profile(user_id, name=None, weight_kg=None, height_cm=None, age=None, gender=None):
    fields, values = [], []
    for key, val in [("name", name), ("weight_kg", weight_kg), ("height_cm", height_cm),
                     ("age", age), ("gender", gender)]:
        if val is not None:
            fields.append(f"{key} = ?")
            values.append(val)
    if not fields:
        return
    values.append(user_id)
    with get_connection() as conn:
        conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)


def _parse_grams(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"[\d.]+", str(value))
    return float(match.group()) if match else 0.0


def _parse_calories(value):
    if value is None or value == "?":
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else 0


def add_food_log(user_id, food_name, calories, protein_g=0, carbs_g=0, fat_g=0, source="manual"):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO food_log (user_id, food_name, calories, protein_g, carbs_g, fat_g, source)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, food_name, _parse_calories(calories),
             _parse_grams(protein_g), _parse_grams(carbs_g), _parse_grams(fat_g), source)
        )
        return cur.lastrowid


def delete_food_log(log_id, user_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM food_log WHERE id = ? AND user_id = ?", (log_id, user_id))


def get_food_logs(user_id, days=None):
    query = "SELECT * FROM food_log WHERE user_id = ?"
    params = [user_id]
    if days is not None:
        query += " AND logged_at >= datetime('now', ?, 'localtime')"
        params.append(f"-{days} days")
    query += " ORDER BY logged_at DESC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_today_calories_in(user_id):
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COALESCE(SUM(calories), 0) AS total FROM food_log
               WHERE user_id = ? AND date(logged_at, 'localtime') = date('now', 'localtime')""",
            (user_id,)
        ).fetchone()
        return int(row["total"])


def add_exercise_log(user_id, exercise_name, duration_min, calories_burned, met_value,
                     sets=0, reps=0, weight_kg=0):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO exercise_log
                  (user_id, exercise_name, duration_min, calories_burned,
                   met_value, sets, reps, weight_kg)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, exercise_name, int(duration_min), int(calories_burned),
             float(met_value), int(sets or 0), int(reps or 0), float(weight_kg or 0))
        )
        return cur.lastrowid


def estimate_1rm(weight_kg, reps):
    if not weight_kg or not reps or reps <= 0:
        return 0
    return weight_kg * (1 + reps / 30.0)


def get_personal_records(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT exercise_name,
                      MAX(weight_kg) AS max_weight,
                      MAX(weight_kg * (1 + CAST(reps AS REAL) / 30.0)) AS max_1rm
               FROM exercise_log
               WHERE user_id = ? AND weight_kg > 0
               GROUP BY exercise_name
               ORDER BY max_1rm DESC""",
            (user_id,)
        ).fetchall()

        records = []
        for r in rows:
            best = conn.execute(
                """SELECT sets, reps, weight_kg, logged_at
                   FROM exercise_log
                   WHERE user_id = ? AND exercise_name = ? AND weight_kg > 0
                   ORDER BY weight_kg DESC, reps DESC
                   LIMIT 1""",
                (user_id, r["exercise_name"])
            ).fetchone()
            records.append({
                "exercise_name": r["exercise_name"],
                "max_weight": float(r["max_weight"] or 0),
                "max_1rm": round(float(r["max_1rm"] or 0), 1),
                "best_reps": best["reps"] if best else 0,
                "best_sets": best["sets"] if best else 0,
                "best_at": best["logged_at"] if best else None,
            })
        return records


def get_exercise_history(user_id, exercise_name, days=None):
    query = """SELECT logged_at, sets, reps, weight_kg, duration_min, calories_burned
               FROM exercise_log
               WHERE user_id = ? AND exercise_name = ?"""
    params = [user_id, exercise_name]
    if days is not None:
        query += " AND logged_at >= datetime('now', ?, 'localtime')"
        params.append(f"-{days} days")
    query += " ORDER BY logged_at ASC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_exercise_history_range(user_id, exercise_name, start_date, end_date):
    s = str(start_date)[:10]
    e = str(end_date)[:10]
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT logged_at, sets, reps, weight_kg, duration_min, calories_burned
               FROM exercise_log
               WHERE user_id = ? AND exercise_name = ?
                 AND date(logged_at, 'localtime') BETWEEN ? AND ?
               ORDER BY logged_at ASC""",
            (user_id, exercise_name, s, e)
        ).fetchall()
        return [dict(r) for r in rows]


def get_strength_logs_range(user_id, start_date, end_date):
    s = str(start_date)[:10]
    e = str(end_date)[:10]
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT exercise_name, sets, reps, weight_kg, logged_at
               FROM exercise_log
               WHERE user_id = ? AND weight_kg > 0
                 AND date(logged_at, 'localtime') BETWEEN ? AND ?""",
            (user_id, s, e)
        ).fetchall()
        return [dict(r) for r in rows]


def get_distinct_strength_exercises(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT DISTINCT exercise_name
               FROM exercise_log
               WHERE user_id = ? AND weight_kg > 0
               ORDER BY exercise_name""",
            (user_id,)
        ).fetchall()
        return [r["exercise_name"] for r in rows]


def get_strength_logs(user_id, days=7):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT exercise_name, sets, reps, weight_kg, logged_at
               FROM exercise_log
               WHERE user_id = ? AND weight_kg > 0
                 AND logged_at >= datetime('now', ?, 'localtime')""",
            (user_id, f"-{days} days")
        ).fetchall()
        return [dict(r) for r in rows]


def get_strength_summary(user_id, days=7):
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COALESCE(SUM(weight_kg * reps * sets), 0) AS volume,
                      COALESCE(SUM(sets), 0) AS total_sets
               FROM exercise_log
               WHERE user_id = ? AND weight_kg > 0
                 AND logged_at >= datetime('now', ?, 'localtime')""",
            (user_id, f"-{days} days")
        ).fetchone()

        week_max = conn.execute(
            """SELECT exercise_name, MAX(weight_kg) AS mw
               FROM exercise_log
               WHERE user_id = ? AND weight_kg > 0
                 AND logged_at >= datetime('now', ?, 'localtime')
               GROUP BY exercise_name""",
            (user_id, f"-{days} days")
        ).fetchall()
        before_max = conn.execute(
            """SELECT exercise_name, MAX(weight_kg) AS mw
               FROM exercise_log
               WHERE user_id = ? AND weight_kg > 0
                 AND logged_at < datetime('now', ?, 'localtime')
               GROUP BY exercise_name""",
            (user_id, f"-{days} days")
        ).fetchall()

    before_map = {r["exercise_name"]: float(r["mw"]) for r in before_max}
    new_prs = 0
    top_growth = None
    for r in week_max:
        name = r["exercise_name"]
        w = float(r["mw"] or 0)
        prev = before_map.get(name, 0)
        if w > prev:
            new_prs += 1
            delta = w - prev
            if prev > 0 and (top_growth is None or delta > top_growth[1]):
                top_growth = (name, delta, prev, w)

    return {
        "volume": float(row["volume"] or 0),
        "sets": int(row["total_sets"] or 0),
        "new_prs": new_prs,
        "top_growth": top_growth,
    }


def add_body_measurement(user_id, weight_kg=None, chest_cm=None, waist_cm=None,
                         hip_cm=None, arm_cm=None, thigh_cm=None,
                         body_fat_pct=None, note=None):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO body_measurements
                  (user_id, weight_kg, chest_cm, waist_cm, hip_cm,
                   arm_cm, thigh_cm, body_fat_pct, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, weight_kg, chest_cm, waist_cm, hip_cm,
             arm_cm, thigh_cm, body_fat_pct, note)
        )
        return cur.lastrowid


def get_body_measurements(user_id, days=None):
    query = "SELECT * FROM body_measurements WHERE user_id = ?"
    params = [user_id]
    if days is not None:
        query += " AND logged_at >= datetime('now', ?, 'localtime')"
        params.append(f"-{days} days")
    query += " ORDER BY logged_at ASC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def delete_body_measurement(measurement_id, user_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM body_measurements WHERE id = ? AND user_id = ?",
            (measurement_id, user_id)
        )


def delete_exercise_log(log_id, user_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM exercise_log WHERE id = ? AND user_id = ?", (log_id, user_id))


def get_exercise_logs(user_id, days=None):
    query = "SELECT * FROM exercise_log WHERE user_id = ?"
    params = [user_id]
    if days is not None:
        query += " AND logged_at >= datetime('now', ?, 'localtime')"
        params.append(f"-{days} days")
    query += " ORDER BY logged_at DESC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_today_calories_out(user_id):
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COALESCE(SUM(calories_burned), 0) AS total FROM exercise_log
               WHERE user_id = ? AND date(logged_at, 'localtime') = date('now', 'localtime')""",
            (user_id,)
        ).fetchone()
        return int(row["total"])


def get_daily_summary(user_id, days=7):
    with get_connection() as conn:
        today = datetime.now().date()
        dates = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]

        food_rows = conn.execute(
            """SELECT date(logged_at, 'localtime') AS day, SUM(calories) AS total
               FROM food_log
               WHERE user_id = ? AND logged_at >= datetime('now', ?, 'localtime')
               GROUP BY day""",
            (user_id, f"-{days} days")
        ).fetchall()
        food_map = {r["day"]: int(r["total"]) for r in food_rows}

        ex_rows = conn.execute(
            """SELECT date(logged_at, 'localtime') AS day, SUM(calories_burned) AS total
               FROM exercise_log
               WHERE user_id = ? AND logged_at >= datetime('now', ?, 'localtime')
               GROUP BY day""",
            (user_id, f"-{days} days")
        ).fetchall()
        ex_map = {r["day"]: int(r["total"]) for r in ex_rows}

        return [
            {
                "date": d,
                "cal_in": food_map.get(d, 0),
                "cal_out": ex_map.get(d, 0),
                "net": food_map.get(d, 0) - ex_map.get(d, 0),
            }
            for d in dates
        ]


def get_totals(user_id, days=None):
    where_date = ""
    params = [user_id]
    if days is not None:
        where_date = " AND logged_at >= datetime('now', ?, 'localtime')"
        params_food = params + [f"-{days} days"]
        params_ex = params + [f"-{days} days"]
    else:
        params_food = params
        params_ex = params

    with get_connection() as conn:
        cal_in = conn.execute(
            f"SELECT COALESCE(SUM(calories), 0) AS t FROM food_log WHERE user_id = ?{where_date}",
            params_food
        ).fetchone()["t"]
        cal_out = conn.execute(
            f"SELECT COALESCE(SUM(calories_burned), 0) AS t FROM exercise_log WHERE user_id = ?{where_date}",
            params_ex
        ).fetchone()["t"]
        return {"cal_in": int(cal_in), "cal_out": int(cal_out), "net": int(cal_in) - int(cal_out)}


def get_totals_today(user_id):
    with get_connection() as conn:
        cal_in = conn.execute(
            """SELECT COALESCE(SUM(calories), 0) AS t FROM food_log
               WHERE user_id = ? AND date(logged_at, 'localtime') = date('now', 'localtime')""",
            (user_id,)
        ).fetchone()["t"]
        cal_out = conn.execute(
            """SELECT COALESCE(SUM(calories_burned), 0) AS t FROM exercise_log
               WHERE user_id = ? AND date(logged_at, 'localtime') = date('now', 'localtime')""",
            (user_id,)
        ).fetchone()["t"]
        return {"cal_in": int(cal_in), "cal_out": int(cal_out), "net": int(cal_in) - int(cal_out)}


def get_totals_last_24h(user_id):
    with get_connection() as conn:
        cal_in = conn.execute(
            """SELECT COALESCE(SUM(calories), 0) AS t FROM food_log
               WHERE user_id = ? AND logged_at >= datetime('now', '-24 hours')""",
            (user_id,)
        ).fetchone()["t"]
        cal_out = conn.execute(
            """SELECT COALESCE(SUM(calories_burned), 0) AS t FROM exercise_log
               WHERE user_id = ? AND logged_at >= datetime('now', '-24 hours')""",
            (user_id,)
        ).fetchone()["t"]
        return {"cal_in": int(cal_in), "cal_out": int(cal_out), "net": int(cal_in) - int(cal_out)}


def get_totals_range(user_id, start_date, end_date):
    s = str(start_date)[:10]
    e = str(end_date)[:10]
    with get_connection() as conn:
        cal_in = conn.execute(
            """SELECT COALESCE(SUM(calories), 0) AS t FROM food_log
               WHERE user_id = ?
                 AND date(logged_at, 'localtime') BETWEEN ? AND ?""",
            (user_id, s, e)
        ).fetchone()["t"]
        cal_out = conn.execute(
            """SELECT COALESCE(SUM(calories_burned), 0) AS t FROM exercise_log
               WHERE user_id = ?
                 AND date(logged_at, 'localtime') BETWEEN ? AND ?""",
            (user_id, s, e)
        ).fetchone()["t"]
        return {"cal_in": int(cal_in), "cal_out": int(cal_out), "net": int(cal_in) - int(cal_out)}


def get_daily_summary_range(user_id, start_date, end_date):
    s = str(start_date)[:10]
    e = str(end_date)[:10]
    start = datetime.fromisoformat(s).date()
    end = datetime.fromisoformat(e).date()
    if end < start:
        start, end = end, start

    delta_days = (end - start).days
    dates = [(start + timedelta(days=i)).isoformat() for i in range(delta_days + 1)]

    with get_connection() as conn:
        food_rows = conn.execute(
            """SELECT date(logged_at, 'localtime') AS day, SUM(calories) AS total
               FROM food_log
               WHERE user_id = ?
                 AND date(logged_at, 'localtime') BETWEEN ? AND ?
               GROUP BY day""",
            (user_id, s, e)
        ).fetchall()
        food_map = {r["day"]: int(r["total"]) for r in food_rows}

        ex_rows = conn.execute(
            """SELECT date(logged_at, 'localtime') AS day, SUM(calories_burned) AS total
               FROM exercise_log
               WHERE user_id = ?
                 AND date(logged_at, 'localtime') BETWEEN ? AND ?
               GROUP BY day""",
            (user_id, s, e)
        ).fetchall()
        ex_map = {r["day"]: int(r["total"]) for r in ex_rows}

        return [
            {
                "date": d,
                "cal_in": food_map.get(d, 0),
                "cal_out": ex_map.get(d, 0),
                "net": food_map.get(d, 0) - ex_map.get(d, 0),
            }
            for d in dates
        ]


def get_hourly_summary_today(user_id):
    with get_connection() as conn:
        food_rows = conn.execute(
            """SELECT CAST(strftime('%H', logged_at, 'localtime') AS INTEGER) AS h,
                      SUM(calories) AS total
               FROM food_log
               WHERE user_id = ? AND date(logged_at, 'localtime') = date('now', 'localtime')
               GROUP BY h""",
            (user_id,)
        ).fetchall()
        food_map = {r["h"]: int(r["total"]) for r in food_rows}

        ex_rows = conn.execute(
            """SELECT CAST(strftime('%H', logged_at, 'localtime') AS INTEGER) AS h,
                      SUM(calories_burned) AS total
               FROM exercise_log
               WHERE user_id = ? AND date(logged_at, 'localtime') = date('now', 'localtime')
               GROUP BY h""",
            (user_id,)
        ).fetchall()
        ex_map = {r["h"]: int(r["total"]) for r in ex_rows}

        return [
            {
                "hour": h,
                "cal_in": food_map.get(h, 0),
                "cal_out": ex_map.get(h, 0),
                "net": food_map.get(h, 0) - ex_map.get(h, 0),
            }
            for h in range(24)
        ]


def get_hourly_summary_last_24h(user_id):
    with get_connection() as conn:
        food_rows = conn.execute(
            """SELECT strftime('%Y-%m-%d %H', logged_at, 'localtime') AS hr,
                      SUM(calories) AS total
               FROM food_log
               WHERE user_id = ? AND logged_at >= datetime('now', '-24 hours')
               GROUP BY hr""",
            (user_id,)
        ).fetchall()
        food_map = {r["hr"]: int(r["total"]) for r in food_rows}

        ex_rows = conn.execute(
            """SELECT strftime('%Y-%m-%d %H', logged_at, 'localtime') AS hr,
                      SUM(calories_burned) AS total
               FROM exercise_log
               WHERE user_id = ? AND logged_at >= datetime('now', '-24 hours')
               GROUP BY hr""",
            (user_id,)
        ).fetchall()
        ex_map = {r["hr"]: int(r["total"]) for r in ex_rows}

    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    result = []
    for i in range(23, -1, -1):
        slot = now - timedelta(hours=i)
        key = slot.strftime("%Y-%m-%d %H")
        result.append({
            "hour": slot.hour,
            "label": slot.strftime("%H"),
            "cal_in": food_map.get(key, 0),
            "cal_out": ex_map.get(key, 0),
            "net": food_map.get(key, 0) - ex_map.get(key, 0),
        })
    return result


init_db()
