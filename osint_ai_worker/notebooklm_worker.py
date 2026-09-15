"""Dedicated HTTP worker for NotebookLM podcast generation."""

import json
import logging
import os
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


def create_podcast_job(session):
    job_id = str(uuid.uuid4())
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
            body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            session = json.loads(body).get("session")
            session = session if session in ("asia", "europe", "us") else "us"
            job_id = create_podcast_job(session)
            logger.info("Queued NotebookLM podcast generation (job=%s, session=%s)", job_id, session)
            self._json(202, {"status": "accepted", "job_id": job_id, "message": "NotebookLM đang tạo podcast"})
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


if __name__ == "__main__":
    ensure_jobs_table()
    port = int(os.getenv("NOTEBOOKLM_WORKER_PORT", "8082"))
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: run_notebooklm_podcast("asia"), "cron", day_of_week="mon-fri", hour=10, minute=0, timezone="Asia/Ho_Chi_Minh", id="notebooklm_asia", max_instances=1)
    scheduler.add_job(lambda: run_notebooklm_podcast("europe"), "cron", day_of_week="mon-fri", hour=16, minute=0, timezone="Asia/Ho_Chi_Minh", id="notebooklm_europe", max_instances=1)
    scheduler.add_job(lambda: run_notebooklm_podcast("us"), "cron", day_of_week="mon-fri", hour=22, minute=0, timezone="Asia/Ho_Chi_Minh", id="notebooklm_us", max_instances=1)
    scheduler.start()
    server = HTTPServer(("0.0.0.0", port), NotebookLMHandler)
    logger.info("NotebookLM worker listening on port %s", port)
    try:
        server.serve_forever()
    finally:
        scheduler.shutdown()