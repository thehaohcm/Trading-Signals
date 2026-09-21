"""Dedicated HTTP worker for NotebookLM podcast generation."""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2

from agents.notebooklm_podcast import run_notebooklm_podcast

logging.basicConfig(level=logging.INFO, format="%(asctime)s - notebooklm_worker - %(levelname)s - %(message)s")
logger = logging.getLogger("notebooklm_worker")
jobs = {}
jobs_lock = threading.Lock()
VIETNAM_TZ = timezone(timedelta(hours=7))
DAILY_PODCAST_SESSION = "us"


def prepare_notebooklm_auth():
    """Make the mounted auth file available at notebooklm-py's default path too."""
    storage_path = Path(os.getenv("NOTEBOOKLM_STORAGE", "/app/notebooklm/storage_state.json"))
    default_path = Path.home() / ".notebooklm" / "profiles" / "default" / "storage_state.json"
    if not storage_path.is_file():
        logger.error("NotebookLM storage file is missing: %s", storage_path)
        return
    default_path.parent.mkdir(parents=True, exist_ok=True)
    if default_path.exists() or default_path.is_symlink():
        default_path.unlink()
    try:
        default_path.symlink_to(storage_path)
        logger.info("NotebookLM auth linked: %s -> %s", default_path, storage_path)
    except OSError as error:
        logger.warning("Could not symlink NotebookLM auth (%s); copying instead", error)
        import shutil
        shutil.copy2(storage_path, default_path)


def db_connection():
    database_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(database_url) if database_url else None


def ensure_jobs_table():
    connection = db_connection()
    if not connection:
        return
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notebooklm_podcast_jobs (
                    id VARCHAR(255) PRIMARY KEY,
                    session VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    result_json JSONB,
                    error TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notebooklm_podcast_daily_runs (
                    generation_date DATE PRIMARY KEY,
                    job_id VARCHAR(255) NOT NULL,
                    session VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'claimed',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
        connection.commit()
    finally:
        connection.close()


def save_job(job_id, session, status, result=None, error=None):
    with jobs_lock:
        jobs[job_id] = {"status": status, "session": session}
        if result is not None:
            jobs[job_id]["data"] = result
        if error:
            jobs[job_id]["message"] = error
    connection = db_connection()
    if not connection:
        return
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO notebooklm_podcast_jobs (id, session, status, result_json, error)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status,
                    result_json = EXCLUDED.result_json, error = EXCLUDED.error,
                    updated_at = NOW()
                """,
                (job_id, session, status, json.dumps(result, ensure_ascii=False) if result else None, error),
            )
        connection.commit()
    finally:
        connection.close()


def load_job(job_id):
    connection = db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT session, status, result_json, error FROM notebooklm_podcast_jobs WHERE id = %s", (job_id,))
                row = cursor.fetchone()
            if row:
                result = {"status": row[1], "session": row[0]}
                if row[2] is not None:
                    result["data"] = row[2]
                if row[3]:
                    result["message"] = row[3]
                return result
        finally:
            connection.close()
    with jobs_lock:
        return jobs.get(job_id)


def claim_daily_podcast(job_id, session):
    """Claim today's only NotebookLM generation in Vietnam time."""
    connection = db_connection()
    if not connection:
        raise RuntimeError("DATABASE_URL chưa được cấu hình; không thể khóa podcast theo ngày")
    generation_date = datetime.now(VIETNAM_TZ).date()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO notebooklm_podcast_daily_runs
                    (generation_date, job_id, session)
                VALUES (%s, %s, %s)
                ON CONFLICT (generation_date) DO NOTHING
                """,
                (generation_date, job_id, session),
            )
            claimed = cursor.rowcount == 1
        connection.commit()
        return claimed
    finally:
        connection.close()


def create_podcast_job(session, manual=False):
    job_id = str(uuid.uuid4())
    if not manual and not claim_daily_podcast(job_id, session):
        logger.info("NotebookLM podcast already claimed for %s", datetime.now(VIETNAM_TZ).date())
        return None
    save_job(job_id, session, "running")

    def run():
        try:
            result = run_notebooklm_podcast(session, force=True)
            save_job(job_id, session, "success", result=result)
        except Exception as error:
            logger.error("NotebookLM podcast failed (job=%s): %s", job_id, error, exc_info=True)
            save_job(job_id, session, "error", error=str(error))

    threading.Thread(target=run, name=f"notebooklm-{job_id[:8]}", daemon=True).start()
    return job_id


class NotebookLMHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/trigger-notebooklm-podcast":
            self.send_error(404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(content_length) or b"{}") if content_length else {}
            session = payload.get("session") or DAILY_PODCAST_SESSION
            job_id = create_podcast_job(session, manual=True)
            if job_id is None:
                self._json(409, {
                    "status": "already_claimed",
                    "message": "Podcast NotebookLM tự động hôm nay đã được khởi chạy.",
                })
                return
            self._json(202, {
                "status": "accepted",
                "job_id": job_id,
                "message": "Đã nhận yêu cầu tạo podcast NotebookLM.",
            })
        except Exception as error:
            logger.error("NotebookLM podcast failed: %s", error, exc_info=True)
            self._json(500, {"status": "error", "message": str(error)})

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "service": "notebooklm_worker"})
            return
        if self.path.startswith("/notebooklm-status?job_id="):
            job_id = self.path.split("=", 1)[1]
            job = load_job(job_id)
            self._json(200, job or {"status": "not_found", "message": "Không tìm thấy job"})
            return
        self.send_error(404)

    def _json(self, status, payload):
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format_string, *args):
        logger.info("%s - %s", self.address_string(), format_string % args)


def is_notebooklm_auto_enabled() -> bool:
    """Check if automatic NotebookLM podcast generation is enabled via system_settings."""
    connection = db_connection()
    if not connection:
        return True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT value FROM system_settings WHERE key = %s", ("notebooklm_auto_generate",))
            row = cursor.fetchone()
            if not row or not row[0]:
                cursor.execute("SELECT value FROM system_settings WHERE key = %s", ("notebooklm_podcast_auto_generate",))
                row = cursor.fetchone()
            if row and row[0]:
                return row[0].strip().lower() in ['true', '1', 'yes', 'on']
        return True
    except Exception as error:
        logger.warning("Failed to check notebooklm_auto_generate setting: %s", error)
        return True
    finally:
        connection.close()


def run_scheduled_notebooklm_podcast():
    """Run daily scheduled NotebookLM podcast if enabled in user settings."""
    if not is_notebooklm_auto_enabled():
        logger.info("Automatic NotebookLM podcast generation is disabled in settings (notebooklm_auto_generate=false). Skipping.")
        return
    logger.info("Starting scheduled daily NotebookLM podcast generation...")
    create_podcast_job(DAILY_PODCAST_SESSION, manual=False)


if __name__ == "__main__":
    storage_path = os.getenv("NOTEBOOKLM_STORAGE", "/app/notebooklm/storage_state.json")
    logger.info("NotebookLM storage configured: %s (exists=%s)", storage_path, os.path.isfile(storage_path))
    prepare_notebooklm_auth()
    ensure_jobs_table()
    port = int(os.getenv("NOTEBOOKLM_WORKER_PORT", "8082"))
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scheduled_notebooklm_podcast,
        "cron",
        hour=20,
        minute=0,
        timezone="Asia/Ho_Chi_Minh",
        id="notebooklm_daily",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    server = HTTPServer(("0.0.0.0", port), NotebookLMHandler)
    logger.info("NotebookLM worker listening on port %s", port)
    try:
        server.serve_forever()
    finally:
        scheduler.shutdown()