"""Create between-session OSINT podcasts with the NotebookLM CLI."""

import logging
import json
import os
import re
import subprocess
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg2

logger = logging.getLogger(__name__)
VIETNAM_TZ = timezone(timedelta(hours=7))
CHANNELS = ("vnwallstreet", "tintucvnws")
SESSION_NAMES = {
    "asia": "Bản tin NotebookLM giữa phiên Á",
    "europe": "Bản tin NotebookLM giữa phiên Âu",
    "us": "Bản tin NotebookLM giữa phiên Mỹ",
}


def is_enabled() -> bool:
    return os.getenv("NOTEBOOKLM_PODCAST_ENABLED", "false").strip().lower() in {
        "1", "true", "yes", "on"
    }


def _project_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _podcast_dir() -> Path:
    path = _project_dir() / "static" / "podcasts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _notebook_id() -> str:
    notebook_id = os.getenv("NOTEBOOKLM_NOTEBOOK", "").strip()
    if not notebook_id:
        raise RuntimeError("NOTEBOOKLM_NOTEBOOK chưa được cấu hình")
    return notebook_id


def _notebook_command(*args: str) -> list[str]:
    command = [os.getenv("NOTEBOOKLM_COMMAND", "notebooklm")]
    storage = os.getenv("NOTEBOOKLM_STORAGE", "/app/notebooklm/storage_state.json").strip()
    profile = os.getenv("NOTEBOOKLM_PROFILE", "").strip()
    if storage:
        command.extend(["--storage", storage])
    if profile:
        command.extend(["--profile", profile])
    return command + list(args)


def _run_notebooklm(*args: str) -> str:
    result = subprocess.run(
        _notebook_command(*args),
        capture_output=True,
        text=True,
        check=False,
        timeout=1900,
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"NotebookLM CLI thất bại ({result.returncode}): {details}")
    return result.stdout.strip()


def _add_and_wait_for_source(source_text: str, title: str) -> None:
    add_output = _run_notebooklm(
        "source", "add", source_text,
        "--notebook", _notebook_id(), "--type", "text", "--title", title,
        "--json",
    )
    try:
        source_result = json.loads(add_output)
        source = source_result.get("source") if isinstance(source_result, dict) else None
        source_id = (
            (source.get("id") if isinstance(source, dict) else None)
            or source_result.get("id")
            or source_result.get("source_id")
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(f"NotebookLM trả về kết quả source không hợp lệ: {add_output[:500]}") from error
    if not source_id:
        raise RuntimeError(f"Không lấy được source ID từ NotebookLM: {add_output[:500]}")
    _run_notebooklm(
        "source", "wait", source_id,
        "--notebook", _notebook_id(), "--timeout", "300", "--json",
    )


def _split_source_text(source_text: str, max_chars: int = 100_000) -> list[str]:
    if len(source_text) <= max_chars:
        return [source_text]
    chunks = []
    remaining = source_text
    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n", 0, max_chars)
        if split_at < 1:
            split_at = max_chars
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:].lstrip("\n")
    return chunks


def _fetch_telegram_text(days: int = 2) -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL chưa được cấu hình")

    channel_pattern = "|".join(re.escape(channel) for channel in CHANNELS)
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT title, content, source_url, created_at
                FROM news_items
                WHERE status = 'active'
                  AND created_at >= NOW() - (%s * INTERVAL '1 day')
                  AND source_url ~* %s
                ORDER BY created_at DESC
                LIMIT 250
                """,
                (days, rf"t\.me/({channel_pattern})(/|$)"),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        raise RuntimeError("Không có bài Telegram VNWS mới trong khoảng thời gian yêu cầu")

    sections = [
        "TELEGRAM OSINT - VN WALL STREET / TIN TỨC VNWS",
        f"Thời điểm tạo: {datetime.now(VIETNAM_TZ).strftime('%d/%m/%Y %H:%M')} (GMT+7)",
        f"Số bài: {len(rows)}",
        "",
    ]
    for index, (title, content, source_url, created_at) in enumerate(rows, 1):
        published_at = created_at
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        published_at = published_at.astimezone(VIETNAM_TZ)
        sections.extend(
            [
                f"[{index}] {published_at.strftime('%d/%m/%Y %H:%M')} - {title}",
                f"Nguồn: {source_url or 'Telegram'}",
                content.strip(),
                "-" * 70,
            ]
        )
    return "\n".join(sections)


def _build_notebooklm_source(days: int) -> str:
    """Combine Telegram posts with market and OSINT context without importing an LLM client."""
    telegram_text = _fetch_telegram_text(days)
    try:
        from agents.market_context import fetch_live_market_prices

        db_url = os.getenv("DATABASE_URL")
        world_state, theses, signals, alerts = {}, [], [], []
        conn = psycopg2.connect(db_url)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT state_json FROM osint_world_state WHERE id = 1")
                row = cur.fetchone()
                world_state = row[0] if row else {}
                cur.execute("SELECT thesis, confidence, supporting_evidence FROM osint_theses WHERE status = 'active' ORDER BY updated_at DESC LIMIT 5")
                theses = cur.fetchall()
                cur.execute("SELECT category, signal, confidence, reason FROM osint_signals WHERE created_at > NOW() - INTERVAL '24 hours' ORDER BY created_at DESC LIMIT 15")
                signals = cur.fetchall()
                cur.execute("SELECT asset_type, symbol, message FROM triggered_alerts WHERE created_at > NOW() - INTERVAL '24 hours' ORDER BY created_at DESC LIMIT 10")
                alerts = cur.fetchall()
        finally:
            conn.close()

        if isinstance(world_state, str):
            world_state = json.loads(world_state)

        world_state_cutoff = datetime.now(VIETNAM_TZ) - timedelta(days=days)

        def format_world_state(value):
            if not isinstance(value, dict):
                return "Hệ thống chưa có trạng thái thế giới mới."
            recent_items = []
            for key, item in value.items():
                if key.startswith("_") or not isinstance(item, dict):
                    continue
                updated_at = item.get("_updated_at")
                if not updated_at:
                    continue
                try:
                    updated_at = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
                    if updated_at.tzinfo is None:
                        updated_at = updated_at.replace(tzinfo=VIETNAM_TZ)
                    if updated_at < world_state_cutoff:
                        continue
                except ValueError:
                    logger.warning("Skipping world state item with invalid _updated_at: %s", key)
                    continue
                recent_items.append(f"- {key}: {json.dumps(item, ensure_ascii=False)}")
            return "\n".join(recent_items) if recent_items else f"Không có trạng thái thế giới nào được cập nhật trong {days} ngày gần đây."

        market_prices = fetch_live_market_prices()
        context_sections = [
            "\n\n" + "=" * 80,
            "LIVE MARKET PRICES - GIÁ THỊ TRƯỜNG HIỆN TẠI",
            "Nguồn: yfinance; dùng để bổ sung bối cảnh, không thay thế dữ liệu Telegram.",
            market_prices,
            "\n" + "=" * 80,
            "CURRENT WORLD STATE - TRẠNG THÁI THẾ GIỚI HIỆN TẠI",
            format_world_state(world_state),
            "\n" + "=" * 80,
            "OSINT SIGNALS - TÍN HIỆU OSINT GẦN NHẤT",
        ]
        if signals:
            context_sections.extend(
                f"- [{item[0]}] {item[1]} (confidence: {item[2]}) - {item[3]}"
                for item in signals
            )
        else:
            context_sections.append("Không có tín hiệu OSINT mới trong 24 giờ qua.")
        context_sections.extend(["\n" + "=" * 80, "PLATFORM THESES - LUẬN ĐIỂM VĨ MÔ ĐANG HOẠT ĐỘNG"])
        if theses:
            context_sections.extend(
                f"- {item[0]} (confidence: {item[1]})\n  Bằng chứng: {item[2]}"
                for item in theses
            )
        else:
            context_sections.append("Chưa có luận điểm vĩ mô đang hoạt động.")
        if alerts:
            context_sections.extend(["\n" + "=" * 80, "PRICE ALERTS - CẢNH BÁO GIÁ GẦN NHẤT"])
            context_sections.extend(
                f"- {item[0]} {item[1]}: {item[2]}"
                for item in alerts
            )
        return telegram_text + "\n".join(context_sections)
    except Exception as error:
        logger.warning("Could not enrich NotebookLM source with market/OSINT context: %s", error)
        return telegram_text + "\n\nKhông lấy được phần bổ sung market/world state: " + str(error)


def _audio_duration(path: Path) -> int:
    try:
        from mutagen.mp4 import MP4

        return int(MP4(path).info.length)
    except Exception:
        return 0


def _save_podcast_record(session_code: str, title: str, audio_url: str, script_text: str, duration: int) -> dict:
    podcast_id = f"notebooklm_{session_code}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        conn = psycopg2.connect(db_url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO osint_podcasts
                    (id, session, session_name, title, audio_url, duration_seconds, script_text, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (podcast_id, session_code, SESSION_NAMES[session_code], title, audio_url, duration, script_text),
                )
            conn.commit()
        finally:
            conn.close()
    return {
        "id": podcast_id,
        "session": session_code,
        "session_name": SESSION_NAMES[session_code],
        "title": title,
        "audio_url": audio_url,
        "duration_seconds": duration,
        "script_text": script_text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def run_notebooklm_podcast(session_code: str, force: bool = False) -> dict | None:
    """Create one between-session NotebookLM audio briefing."""
    if session_code not in SESSION_NAMES:
        raise ValueError(f"Session NotebookLM không hợp lệ: {session_code}")
    if not force and not is_enabled():
        logger.info("NotebookLM podcast is disabled (NOTEBOOKLM_PODCAST_ENABLED=false).")
        return None

    podcast_dir = _podcast_dir()
    source_text = _build_notebooklm_source(int(os.getenv("NOTEBOOKLM_SOURCE_DAYS", "2")))
    title = f"{SESSION_NAMES[session_code]} - {datetime.now(VIETNAM_TZ).strftime('%d/%m/%Y %H:%M')}"
    audio_filename = f"notebooklm_{session_code}_{datetime.now(VIETNAM_TZ).strftime('%Y%m%d_%H%M')}.m4a"
    audio_path = podcast_dir / audio_filename

    source_chunks = _split_source_text(source_text.replace("\x00", ""))
    for index, source_chunk in enumerate(source_chunks, 1):
        chunk_title = title if len(source_chunks) == 1 else f"{title} - Phần {index}/{len(source_chunks)}"
        _add_and_wait_for_source(source_chunk, chunk_title)
    _run_notebooklm(
        "generate", "audio",
        os.getenv(
            "NOTEBOOKLM_AUDIO_PROMPT",
            """Bạn là trưởng ban phân tích vĩ mô và phát thanh viên tài chính. Tạo podcast tiếng Việt dạng Macro Market Briefing dựa trên toàn bộ source được cung cấp.
Ưu tiên theo thứ tự: (1) tin Telegram mới nhất, (2) giá live của vàng, bạc, dầu WTI/Brent, DXY, US10Y, chứng khoán, Bitcoin và USD/VND, (3) Current World State, (4) OSINT signals, theses và price alerts.
Phải nói rõ thời điểm dữ liệu, không bịa số liệu và không dùng giá cũ khi source có giá live. Giải thích mối quan hệ giữa tin tức, lãi suất, DXY, lợi suất và các tài sản; phân tích riêng vàng, dầu, chứng khoán, crypto và forex. Nêu hai kịch bản chính (hawkish/dovish hoặc risk-on/risk-off), catalyst cần theo dõi và nguyên tắc quản trị rủi ro. Loại bỏ tin trùng lặp, phân biệt sự kiện đã xảy ra với tin chưa xác nhận, không biến tin Telegram thành sự thật nếu thiếu kiểm chứng. Văn phong tự nhiên, đĩnh đạc, dễ nghe; mở đầu bằng thời điểm và kết thúc bằng checklist hành động ngắn gọn.""",
        ),
        "--notebook", _notebook_id(), "--language", "vi", "--format", "deep-dive",
        "--length", os.getenv("NOTEBOOKLM_AUDIO_LENGTH", "default"), "--wait", "--timeout", "1800",
    )
    _run_notebooklm(
        "download", "audio", str(audio_path),
        "--notebook", _notebook_id(), "--latest", "--force",
    )

    if not audio_path.exists():
        raise RuntimeError(f"NotebookLM không tạo được file audio: {audio_path}")
    audio_url = f"/static/podcasts/{audio_filename}"
    result = _save_podcast_record(
        session_code, title, audio_url, source_text, _audio_duration(audio_path)
    )
    logger.info("NotebookLM podcast created: %s", audio_path)
    return result