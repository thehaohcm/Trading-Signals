"""Dedicated HTTP worker for NotebookLM podcast generation."""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from apscheduler.schedulers.background import BackgroundScheduler

from agents.notebooklm_podcast import run_notebooklm_podcast

logging.basicConfig(level=logging.INFO, format="%(asctime)s - notebooklm_worker - %(levelname)s - %(message)s")
logger = logging.getLogger("notebooklm_worker")


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
            logger.info("Starting NotebookLM podcast generation (session=%s)", session)
            result = run_notebooklm_podcast(session, force=True)
            if result is None:
                raise RuntimeError("NotebookLM không tạo được podcast")
            self._json(200, {"status": "success", "data": result, "message": "Tạo podcast NotebookLM thành công!"})
        except Exception as error:
            logger.error("NotebookLM podcast failed: %s", error, exc_info=True)
            self._json(500, {"status": "error", "message": str(error)})

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "service": "notebooklm_worker"})
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