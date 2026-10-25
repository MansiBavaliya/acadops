
import sqlite3
import json

DATABASE_NAME = "acadops.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                deadline TEXT NOT NULL,
                estimated_hours REAL NOT NULL,
                priority INTEGER NOT NULL DEFAULT 3,
                completed INTEGER NOT NULL DEFAULT 0,
                progress INTEGER NOT NULL DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS academic_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'ACTIVE'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO app_settings
            (setting_key, setting_value)
            VALUES ('available_hours_today', '3')
        """)

        connection.commit()

    finally:
        connection.close()


def get_setting(key, default=None):
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT setting_value
            FROM app_settings
            WHERE setting_key = ?
        """, (key,))

        row = cursor.fetchone()
        return default if row is None else row["setting_value"]

    finally:
        connection.close()


def set_setting(key, value):
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO app_settings (setting_key, setting_value)
            VALUES (?, ?)
            ON CONFLICT(setting_key)
            DO UPDATE SET setting_value = excluded.setting_value
        """, (key, str(value)))

        connection.commit()

        return {
            "success": True,
            "setting": key,
            "value": value
        }

    finally:
        connection.close()


def get_available_study_hours():
    return float(get_setting("available_hours_today", "3"))


def set_available_study_hours(hours):
    hours = float(hours)

    if not 0 <= hours <= 24:
        return {
            "success": False,
            "message": "Available study hours must be between 0 and 24."
        }

    return set_setting("available_hours_today", hours)


def add_task(title, deadline, estimated_hours, priority=3):
    """Add a task unless its title and deadline already exist."""
    title = title.strip()

    if not title:
        raise ValueError("Task title cannot be empty.")

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id
            FROM tasks
            WHERE LOWER(TRIM(title)) = LOWER(TRIM(?))
              AND deadline = ?
            ORDER BY id ASC
            LIMIT 1
        """, (title, deadline))

        existing = cursor.fetchone()

        if existing is not None:
            return existing["id"]

        cursor.execute("""
            INSERT INTO tasks (
                title, deadline, estimated_hours, priority
            )
            VALUES (?, ?, ?, ?)
        """, (title, deadline, estimated_hours, priority))

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_tasks():
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT *
            FROM tasks
            ORDER BY deadline ASC, id ASC
        """)

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def update_progress_by_id(task_id, progress):
    """Update exactly one task using its database ID."""
    try:
        progress = int(progress)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Progress must be a whole number from 0 to 100."
        }

    if not 0 <= progress <= 100:
        return {
            "success": False,
            "message": "Progress must be between 0 and 100."
        }

    connection = get_connection()

    try:
        cursor = connection.cursor()
        completed = 1 if progress == 100 else 0

        cursor.execute("""
            UPDATE tasks
            SET progress = ?, completed = ?
            WHERE id = ?
        """, (progress, completed, int(task_id)))

        connection.commit()

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": f"No task found with ID {task_id}."
            }

        cursor.execute("""
            SELECT id, title, deadline, estimated_hours,
                   priority, completed, progress
            FROM tasks
            WHERE id = ?
        """, (int(task_id),))

        row = cursor.fetchone()

        return {
            "success": True,
            "task_id": row["id"],
            "task": row["title"],
            "progress": row["progress"],
            "completed": bool(row["completed"])
        }

    finally:
        connection.close()


def update_progress(title, progress):
    """Update by title only if it uniquely identifies one task."""
    title = title.strip()

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id
            FROM tasks
            WHERE LOWER(TRIM(title)) = LOWER(TRIM(?))
            ORDER BY id ASC
        """, (title,))

        matches = cursor.fetchall()

    finally:
        connection.close()

    if not matches:
        return {
            "success": False,
            "message": f"Task '{title}' was not found."
        }

    if len(matches) > 1:
        return {
            "success": False,
            "message": (
                f"Multiple tasks have the title '{title}'. "
                "Please identify the correct task."
            )
        }

    return update_progress_by_id(matches[0]["id"], progress)


def mark_completed(title):
    """Mark a task complete only if its title is unique."""
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id
            FROM tasks
            WHERE LOWER(TRIM(title)) = LOWER(TRIM(?))
            ORDER BY id ASC
        """, (title.strip(),))

        matches = cursor.fetchall()

    finally:
        connection.close()

    if len(matches) != 1:
        return False

    return update_progress_by_id(matches[0]["id"], 100)["success"]


def delete_task(title):
    """Delete by title only when it uniquely identifies one task."""
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id
            FROM tasks
            WHERE LOWER(TRIM(title)) = LOWER(TRIM(?))
            ORDER BY id ASC
        """, (title.strip(),))

        matches = cursor.fetchall()

        if len(matches) != 1:
            return False

        cursor.execute("""
            DELETE FROM tasks
            WHERE id = ?
        """, (matches[0]["id"],))

        connection.commit()
        return cursor.rowcount == 1

    finally:
        connection.close()


def save_academic_plan(plan):
    """Save a plan and make it the active plan."""
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE academic_plans
            SET status = 'SUPERSEDED'
            WHERE status = 'ACTIVE'
        """)

        cursor.execute("""
            INSERT INTO academic_plans (plan_json, status)
            VALUES (?, 'ACTIVE')
        """, (json.dumps(plan),))

        plan_id = cursor.lastrowid
        connection.commit()

        return {
            "success": True,
            "plan_id": plan_id,
            "message": "Academic plan saved successfully."
        }

    finally:
        connection.close()


def get_latest_academic_plan():
    """Retrieve the most recently saved active plan."""
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, plan_json, created_at, status
            FROM academic_plans
            WHERE status = 'ACTIVE'
            ORDER BY id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

        if row is None:
            return {
                "success": False,
                "message": "No saved academic plan exists yet."
            }

        return {
            "success": True,
            "plan_id": row["id"],
            "created_at": row["created_at"],
            "status": row["status"],
            "plan": json.loads(row["plan_json"])
        }

    finally:
        connection.close()


def get_academic_plan_history(limit=50):
    """Retrieve recent plans without modifying them."""
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, plan_json, created_at, status
            FROM academic_plans
            ORDER BY id DESC
            LIMIT ?
        """, (max(1, min(int(limit), 200)),))

        history = []

        for row in cursor.fetchall():
            try:
                plan_data = json.loads(row["plan_json"])
            except (json.JSONDecodeError, TypeError):
                plan_data = {}

            history.append({
                "plan_id": row["id"],
                "created_at": row["created_at"],
                "status": row["status"],
                "plan": plan_data
            })

        return history

    finally:
        connection.close()
