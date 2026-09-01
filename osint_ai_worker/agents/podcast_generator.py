import os
import sys
import json
import uuid
import time
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Import LLM Client
from agents.gemini_client import global_gemini_client

# ==========================================
# PYDANTIC SCHEMA
# ==========================================

class PodcastOutput(BaseModel):
    title: str = Field(description="Tiêu đề bản tin podcast hấp dẫn, súc tích (Ví dụ: 'Bản Tin Macro Phiên Mỹ: Đón Sóng CPI, DXY Giằng Co và Chiến Lược Quản Trị Rủi Ro Vàng')")
    session_focus: str = Field(description="Điểm nhấn cốt lõi nhất của phiên giao dịch (1-2 câu)")
    script_text: str = Field(
        description="Toàn văn kịch bản phát thanh tiếng Việt hoàn chỉnh (khoảng 380 - 480 từ, tương đương 2 đến 3 phút đọc). "
                    "Văn phong phát thanh viên tài chính chuyên nghiệp, mạch lạc, lôi cuốn, dễ nghe khi phát âm qua giọng đọc TTS. "
                    "Bao gồm đầy đủ: Lời chào phiên mới, Điểm tin liên thị trường (DXY, Trái phiếu, Vàng, Dầu, Cổ phiếu), "
                    "Tâm điểm vĩ mô từ World State (NHTW, Thanh khoản), Nhận định Platform Intelligence & Tư vấn phân bổ danh mục, "
                    "ĐẶC BIỆT: Lịch kinh tế trọng tâm công bố trong phiên (đọc rõ mốc giờ, chỉ số, dự báo vs kỳ trước, rủi ro biến động), "
                    "và Lời dặn dò quản trị rủi ro trước phiên."
    )

# ==========================================
# HELPER FUNCTIONS
# ==========================================

import urllib.request
import urllib.error
import requests

def get_vietnam_time() -> datetime:
    """Get current time in Vietnam Timezone (UTC+7)"""
    return datetime.now(timezone(timedelta(hours=7)))

# In-memory cache for economic events (TTL 15 mins)
_CALENDAR_CACHE = {
    "timestamp": 0,
    "events": []
}

def _fetch_all_raw_events() -> list[dict]:
    """Fetch raw economic events from ForexFactory or TradingView with 15-min cache"""
    global _CALENDAR_CACHE
    now_ts = time.time()
    
    # 1. Return cache if still fresh (< 15 mins)
    if _CALENDAR_CACHE["events"] and (now_ts - _CALENDAR_CACHE["timestamp"] < 900):
        return _CALENDAR_CACHE["events"]

    raw_events = []
    vn_tz = timezone(timedelta(hours=7))

    # 2. Try ForexFactory JSON
    try:
        req = urllib.request.Request(
            "https://nfs.faireconomy.media/ff_calendar_thisweek.json", 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data:
                impact = item.get("impact", "")
                if impact not in ["High", "Medium"]:
                    continue
                raw_date = item.get("date", "")
                if not raw_date:
                    continue
                try:
                    event_utc_dt = datetime.fromisoformat(raw_date)
                    event_vn_dt = event_utc_dt.astimezone(vn_tz)
                    raw_events.append({
                        "title": item.get("title", ""),
                        "country": item.get("country", ""),
                        "impact": impact,
                        "forecast": str(item.get("forecast") or ""),
                        "previous": str(item.get("previous") or ""),
                        "time_vn": event_vn_dt.strftime("%H:%M"),
                        "datetime_vn": event_vn_dt,
                        "date_str": event_vn_dt.strftime("%Y-%m-%d")
                    })
                except Exception:
                    continue
            if raw_events:
                _CALENDAR_CACHE = {"timestamp": now_ts, "events": raw_events}
                return raw_events
    except Exception as e:
        logger.warning(f"ForexFactory feed failed ({e}), falling back to TradingView Calendar...")

    # 3. Fallback to TradingView Calendar API
    try:
        now_vn = get_vietnam_time()
        start_dt = now_vn - timedelta(days=now_vn.weekday())
        end_dt = start_dt + timedelta(days=7)
        tv_url = "https://economic-calendar.tradingview.com/events"
        params = {
            "from": start_dt.strftime("%Y-%m-%dT00:00:00.000Z"),
            "to": end_dt.strftime("%Y-%m-%dT23:59:59.000Z"),
            "countries": "US,EU,GB,JP,AU,CA,CH,NZ,CN",
            "minImportance": "0"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/"
        }
        resp = requests.get(tv_url, params=params, headers=headers, timeout=6)
        if resp.status_code == 200:
            items = resp.json().get("result", [])
            for item in items:
                importance = item.get("importance", 0)
                impact = "High" if (importance is not None and importance >= 1) else ("Medium" if importance == 0 else "Low")
                if impact not in ["High", "Medium"]:
                    continue
                raw_date = item.get("date", "")
                if not raw_date:
                    continue
                try:
                    dt_utc = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    dt_vn = dt_utc.astimezone(vn_tz)
                    raw_events.append({
                        "title": item.get("title", ""),
                        "country": item.get("currency") or item.get("country", ""),
                        "impact": impact,
                        "forecast": str(item.get("forecast")) if item.get("forecast") is not None else "",
                        "previous": str(item.get("previous")) if item.get("previous") is not None else "",
                        "time_vn": dt_vn.strftime("%H:%M"),
                        "datetime_vn": dt_vn,
                        "date_str": dt_vn.strftime("%Y-%m-%d")
                    })
                except Exception:
                    continue
            if raw_events:
                _CALENDAR_CACHE = {"timestamp": now_ts, "events": raw_events}
                return raw_events
    except Exception as tve:
        logger.warning(f"TradingView Calendar failed ({tve}), checking DB fallback...")

    # 4. Fallback to DB table
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT title, country, event_time, impact, forecast, previous 
                FROM public.economic_calendar 
                WHERE impact IN ('High', 'Medium')
                  AND event_time >= NOW() - INTERVAL '24 hours'
                  AND event_time <= NOW() + INTERVAL '48 hours'
                ORDER BY event_time ASC
            """)
            rows = cur.fetchall()
            for r in rows:
                ev_time = r['event_time'].astimezone(vn_tz)
                raw_events.append({
                    "title": r.get("title", ""),
                    "country": r.get("country", ""),
                    "impact": r.get("impact", "High"),
                    "forecast": r.get("forecast", ""),
                    "previous": r.get("previous", ""),
                    "time_vn": ev_time.strftime("%H:%M"),
                    "datetime_vn": ev_time,
                    "date_str": ev_time.strftime("%Y-%m-%d")
                })
            cur.close()
            conn.close()
        except Exception as dbe:
            logger.error(f"DB fallback error: {dbe}")

    if raw_events:
        _CALENDAR_CACHE = {"timestamp": now_ts, "events": raw_events}
    return raw_events

def fetch_forexfactory_events_for_session(session_code: str, target_dt: Optional[datetime] = None) -> list[dict]:
    """
    Filter economic events for specific session:
    - asia: 05:00 - 12:30 ICT
    - europe: 12:30 - 18:30 ICT
    - us: 18:30 - 04:00 (next day) ICT
    """
    if target_dt is None:
        target_dt = get_vietnam_time()

    today_date_str = target_dt.strftime("%Y-%m-%d")
    tomorrow_date_str = (target_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    
    all_events = _fetch_all_raw_events()
    session_events = []

    for ev in all_events:
        ev_date = ev["date_str"]
        ev_dt = ev["datetime_vn"]
        time_float = ev_dt.hour + ev_dt.minute / 60.0

        is_match = False
        if session_code == "asia":
            if ev_date == today_date_str and (5.0 <= time_float <= 12.5):
                is_match = True
        elif session_code == "europe":
            if ev_date == today_date_str and (12.5 <= time_float <= 18.5):
                is_match = True
        elif session_code == "us":
            if (ev_date == today_date_str and time_float >= 18.5) or \
               (ev_date == tomorrow_date_str and time_float <= 4.0):
                is_match = True
        else:
            if ev_date == today_date_str:
                is_match = True

        if is_match:
            session_events.append(ev)

    # Sort events chronologically
    session_events.sort(key=lambda x: x["datetime_vn"])
    return session_events

def determine_session(dt: Optional[datetime] = None) -> tuple[str, str]:
    """
    Determine the trading session based on time of day (ICT).
    Returns (session_code, session_name)
    - 00:00 - 11:59: 'asia' (Bản tin Phiên Á)
    - 12:00 - 17:59: 'europe' (Bản tin Phiên Âu)
    - 18:00 - 23:59: 'us' (Bản tin Phiên Mỹ)
    """
    if dt is None:
        dt = get_vietnam_time()
    
    hour = dt.hour
    if 0 <= hour < 12:
        return "asia", "Bản tin Phiên Á"
    elif 12 <= hour < 18:
        return "europe", "Bản tin Phiên Âu"
    else:
        return "us", "Bản tin Phiên Mỹ"

def ensure_podcast_table_and_dirs():
    """Ensure osint_podcasts table and storage directory exist"""
    # 1. Check directory
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "podcasts")
    os.makedirs(static_dir, exist_ok=True)

    # 2. Check DB table
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS osint_podcasts (
                id VARCHAR(255) PRIMARY KEY,
                session VARCHAR(50) NOT NULL,
                session_name VARCHAR(100) NOT NULL,
                title VARCHAR(255) NOT NULL,
                audio_url VARCHAR(500) NOT NULL,
                duration_seconds INTEGER DEFAULT 0,
                script_text TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_osint_podcasts_created_at ON osint_podcasts(created_at DESC);
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error ensuring osint_podcasts table: {e}")

def cleanup_old_podcasts():
    """
    Clean up podcast records and audio files older than 3 days (Vietnam Time, UTC+7)
    while always keeping at least the 5 most recent briefings.
    """
    logger.info("Cleaning up old podcasts (keeping recent 3 days and at least 5 latest records)...")
    db_url = os.getenv("DATABASE_URL")
    valid_audio_urls = set()
    
    if db_url:
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            # Delete DB records created older than 3 days in Vietnam timezone (UTC+7)
            cur.execute("""
                DELETE FROM osint_podcasts 
                WHERE created_at < (date_trunc('day', NOW() AT TIME ZONE 'Asia/Ho_Chi_Minh') - INTERVAL '3 days') AT TIME ZONE 'Asia/Ho_Chi_Minh'
                  AND id NOT IN (
                      SELECT id FROM osint_podcasts ORDER BY created_at DESC LIMIT 5
                  );
            """)
            deleted_rows = cur.rowcount
            conn.commit()
            
            # Get list of all remaining valid audio_urls currently in DB
            cur.execute("SELECT audio_url FROM osint_podcasts")
            valid_audio_urls = {row[0] for row in cur.fetchall() if row[0]}
            cur.close()
            conn.close()
            if deleted_rows > 0:
                logger.info(f"Purged {deleted_rows} old podcast records from database.")
        except Exception as e:
            logger.warning(f"Failed to cleanup old podcast records from DB: {e}")

    # Remove physical mp3 files that are no longer referenced in DB or older than 72h
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        static_dir = os.path.join(base_dir, "static", "podcasts")
        if os.path.exists(static_dir):
            now = time.time()
            for fname in os.listdir(static_dir):
                if fname.endswith(".mp3"):
                    fpath = os.path.join(static_dir, fname)
                    url_path = f"/static/podcasts/{fname}"
                    is_stale_file = (os.path.getmtime(fpath) < now - 259200) # 3 days (72h)
                    if (valid_audio_urls and url_path not in valid_audio_urls) or is_stale_file:
                        try:
                            os.remove(fpath)
                            logger.info(f"Cleaned up old podcast file: {fname}")
                        except Exception as err:
                            logger.warning(f"Could not remove {fname}: {err}")
    except Exception as e:
        logger.warning(f"Error during audio file cleanup: {e}")

def fetch_osint_data_for_podcast() -> tuple[dict, list, list, list]:
    """
    Fetch Current World State, Platform Intelligence (Theses), recent OSINT Signals,
    and Active Rising/Breakout Alerts.
    """
    db_url = os.getenv("DATABASE_URL")
    world_state = {}
    theses = []
    signals = []
    alerts = []
    
    if not db_url:
        return world_state, theses, signals, alerts

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # 1. World State
        cur.execute("SELECT state_json, updated_at FROM osint_world_state WHERE id = 1")
        row = cur.fetchone()
        if row:
            if isinstance(row['state_json'], str):
                try:
                    world_state = json.loads(row['state_json'])
                except:
                    world_state = {}
            else:
                world_state = row['state_json'] or {}

        # 2. Platform Intelligence (Active Theses)
        cur.execute("SELECT id, thesis, confidence, supporting_evidence, updated_at FROM osint_theses WHERE status = 'active' ORDER BY updated_at DESC LIMIT 5")
        theses = cur.fetchall()

        # 3. Recent Signals (last 24 hours)
        cur.execute("""
            SELECT category, signal, confidence, reason, created_at 
            FROM osint_signals 
            WHERE created_at > NOW() - INTERVAL '24 hours' 
            ORDER BY created_at DESC 
            LIMIT 15
        """)
        signals = cur.fetchall()

        # 4. Triggered / Active Price Alerts (last 24 hours)
        try:
            cur.execute("""
                SELECT asset_type, symbol, price, message, created_at
                FROM triggered_alerts
                WHERE created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 10
            """)
            alerts = cur.fetchall()
        except Exception as ae:
            logger.warning(f"Could not fetch triggered_alerts: {ae}")
            conn.rollback()

        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error fetching data for podcast: {e}")

    return world_state, theses, signals, alerts

# ==========================================
# AUDIO GENERATION VIA EDGE-TTS
# ==========================================

async def generate_tts_audio_async(text: str, output_path: str, voice: str = "vi-VN-HoaiMyNeural") -> int:
    """
    Generate MP3 file from text using Edge-TTS.
    Returns duration in seconds.
    """
    import edge_tts
    
    communicate = edge_tts.Communicate(text, voice, rate="+5%", pitch="+0Hz")
    await communicate.save(output_path)

    duration = 0
    try:
        from mutagen.mp3 import MP3
        audio = MP3(output_path)
        duration = int(audio.info.length)
    except Exception as e:
        logger.warning(f"Could not calculate audio duration with mutagen: {e}")
        # Rough estimate: ~150 words per minute
        word_count = len(text.split())
        duration = max(30, int((word_count / 150.0) * 60))

    return duration

def generate_tts_audio(text: str, output_path: str, voice: str = "vi-VN-HoaiMyNeural") -> int:
    """Synchronous wrapper for generate_tts_audio_async"""
    return asyncio.run(generate_tts_audio_async(text, output_path, voice))

# ==========================================
# MAIN PODCAST GENERATION PIPELINE
# ==========================================

PODCAST_PROMPT_TEMPLATE = """Bạn là Trưởng ban Biên tập kiêm Phát thanh viên Vĩ mô cao cấp của nền tảng Trading Signals.
Nhiệm vụ của bạn là soạn kịch bản và phát thanh một bản tin âm thanh Podcast (dạng Morning Macro Briefing / Market Squawk) chất lượng cao cho {session_name} ngày {today_date}.

BẢN TIN PHỤC VỤ CÁC TRADER & NHÀ ĐẦU TƯ TÀI CHÍNH TRƯỚC GIỜ MỞ PHIÊN GIAO DỊCH.

DƯỚI ĐÂY LÀ DỮ LIỆU THỰC TẾ TỪ HỆ THỐNG:

1. TRẠNG THÁI THẾ GIỚI HIỆN TẠI (Current World State - NHTW, Thanh khoản, Năng lượng):
{world_state_text}

2. NHẬN ĐỊNH VĨ MÔ & TƯ VẤN PHÂN BỔ TÀI SẢN (Platform Intelligence):
{theses_text}

3. CÁC TÍN HIỆU OSINT MỚI GHI NHẬN:
{signals_text}

4. LỊCH KINH TẾ FOREXFACTORY TRỌNG TÂM CẦN CHÚ Ý TRONG PHIÊN NÀY ({session_name}):
{economic_events_text}

5. CÁC TÍN HIỆU CẢNH BÁO TĂNG GIÁ & DÒNG TIỀN NỔI BẬT (Live Alerts & Breakout Signals):
{alerts_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YÊU CẦU BIÊN TẬP KỊCH BẢN (SCRIPT_TEXT):
1. ĐỘ DÀI & THỜI LƯỢNG: Khoảng 380 - 480 từ (đọc trong 2 đến 3 phút).
2. GIỌNG ĐIỆU & PHONG CÁCH:
   - Tự nhiên, đĩnh đạc, nhịp điệu dứt khoát, phong thái bản tin tài chính quốc tế như Bloomberg Radio hoặc Reuters Audio Briefing.
   - Phát âm các thuật ngữ tài chính tự nhiên (FED, FOMC, CPI, DXY, Vàng XAU, Lợi suất trái phiếu Mỹ 10 năm, Cổ phiếu VN, Crypto...).
3. CẤU TRÚC BẢN TIN BẮT BUỘC (4 PHẦN LIỀN MẠCH):
   - PHẦN 1 - MỞ ĐẦU: Chào đón quý nhà đầu tư đến với {session_name}. Điểm nhanh bức tranh liên thị trường (Chỉ số DXY, Lợi suất, Vàng, Dầu, Chứng khoán).
   - PHẦN 2 - TÂM ĐIỂM VĨ MÔ (Current World State): Điểm nhấn chính sách các NHTW (FED, ECB, BOJ, SBV...) và trạng thái dòng tiền/thanh khoản toàn cầu.
   - PHẦN 3 - LỊCH KINH TẾ & TÂM ĐIỂM TRONG PHIÊN:
     + Nếu có sự kiện kinh tế quan trọng trong phiên (High/Medium Impact): Đọc rõ mốc giờ Việt Nam, tên chỉ số, quốc gia liên quan, so sánh ngắn gọn số liệu dự báo so với kỳ trước và phân tích nhanh kịch bản ảnh hưởng tới thị trường (DXY, Vàng, Ngoại hối).
     + Cảnh báo rủi ro biến động mạnh, quét Stoploss hoặc giãn spread quanh thời điểm ra tin.
     + Nếu phiên này không có tin kinh tế lớn: Nhắc nhở trader thị trường sẽ chủ yếu vận động theo kỹ thuật và dòng tiền tích lũy.
   - PHẦN 4 - CƠ HỘI GIAO DỊCH, DANH MỤC ALERT NỔI BẬT & QUẢN TRỊ RỦI RO:
     + Nếu có danh mục Alert tăng giá/Breakout nổi bật: Điểm tên 2 đến 4 mã/cặp tài sản tiêu biểu có dòng tiền tích cực nhất phù hợp với phiên (Phiên Á: Cổ phiếu VN, Vàng; Phiên Âu: EUR, GBP, Dầu; Phiên Mỹ: US Tech, Crypto, Vàng). Gợi ý vùng giá quan sát/hỗ trợ để canh điểm vào lệnh hợp lý, KHÔNG hô hào mua đuổi giá cao.
     + Dặn dò nhà đầu tư luôn tuân thủ kỷ luật quản trị vốn, đặt mức Cắt lỗ (Stop-loss) an toàn trước giờ mở phiên.

Hãy tạo ra một bản tin hoàn hảo theo JSON Schema được yêu cầu.
"""

def generate_podcast_script(session_code: str, session_name: str) -> dict:
    """Generate podcast script from DB data, ForexFactory calendar, and live alerts using LLM"""
    world_state, theses, signals, alerts = fetch_osint_data_for_podcast()
    events = fetch_forexfactory_events_for_session(session_code)

    today_date = get_vietnam_time().strftime("%d/%m/%Y")

    world_state_str = json.dumps(world_state, ensure_ascii=False, indent=2) if world_state else "Chưa có dữ liệu chi tiết."
    
    theses_str = ""
    if theses:
        for i, t in enumerate(theses, 1):
            theses_str += f"- Nhận định #{i}: {t.get('thesis', '')}\n  + Tư vấn hành động & bảo vệ tài sản: {t.get('supporting_evidence', '')}\n  + Độ tin cậy: {int((t.get('confidence') or 0.8) * 100)}%\n"
    else:
        theses_str = "Hệ thống đang duy trì theo dõi trạng thái vĩ mô tích cực trung hạn."

    signals_str = ""
    if signals:
        for s in signals[:8]:
            signals_str += f"- [{s.get('category', 'Macro')}] {s.get('signal', '')}: {s.get('reason', '')}\n"
    else:
        signals_str = "Không có đột biến tín hiệu bất thường trong 24h qua."

    economic_events_str = ""
    if events:
        for ev in events:
            impact_tag = "🔴 RẤT QUAN TRỌNG (High)" if ev['impact'] == 'High' else "🟠 QUAN TRỌNG VỪA (Medium)"
            fc_info = f"Dự báo: {ev['forecast']}" if ev['forecast'] else "Không có dự báo"
            prev_info = f"Kỳ trước: {ev['previous']}" if ev['previous'] else "Chưa có kỳ trước"
            economic_events_str += f"- {ev['time_vn']} (Giờ VN) | [{ev['country']}] {ev['title']} | Mức độ: {impact_tag} | {fc_info} | {prev_info}\n"
    else:
        economic_events_str = "Không có tin tức kinh tế quan trọng (High/Medium Impact) nào công bố trong phiên này. Thị trường dự kiến giao dịch thuần kỹ thuật theo dòng tiền tự nhiên."

    alerts_str = ""
    if alerts:
        for a in alerts[:6]:
            atype = a.get('asset_type', '').upper()
            sym = a.get('symbol', '')
            price = a.get('price', '')
            msg = a.get('message', '')
            alerts_str += f"- [{atype}] {sym} @ {price}: {msg}\n"
    else:
        alerts_str = "Dòng tiền trên các lớp tài sản đang phân bổ đều, chưa có tín hiệu mua đuổi đột biến bất thường."

    prompt = PODCAST_PROMPT_TEMPLATE.format(
        session_name=session_name,
        today_date=today_date,
        world_state_text=world_state_str,
        theses_text=theses_str,
        signals_text=signals_str,
        economic_events_text=economic_events_str,
        alerts_text=alerts_str
    )

    logger.info(f"Generating podcast script with LLM for {session_name}...")
    result = global_gemini_client.generate_structured_data(prompt, PodcastOutput)
    return result

def run_podcast_generation_pipeline(target_session: Optional[str] = None) -> dict:
    """
    Complete pipeline:
    1. Ensure DB & Dir
    2. Determine Session
    3. Generate LLM Script
    4. Generate Edge-TTS MP3
    5. Save to DB
    """
    ensure_podcast_table_and_dirs()

    if target_session and target_session in ['asia', 'europe', 'us']:
        session_code = target_session
        session_map = {'asia': 'Bản tin Phiên Á', 'europe': 'Bản tin Phiên Âu', 'us': 'Bản tin Phiên Mỹ'}
        session_name = session_map.get(session_code, 'Bản tin Thị trường')
    else:
        session_code, session_name = determine_session()

    logger.info(f"Starting podcast generation pipeline for session: {session_code} ({session_name})")

    # 1. Generate Script
    ai_result = generate_podcast_script(session_code, session_name)
    title = ai_result.get("title", f"{session_name} - {get_vietnam_time().strftime('%d/%m/%Y')}")
    script_text = ai_result.get("script_text", "")

    if not script_text:
        raise ValueError("AI generated an empty podcast script")

    podcast_id = f"podcast_{session_code}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    filename = f"{podcast_id}.mp3"
    
    # 2. Output path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_dir = os.path.join(base_dir, "static", "podcasts")
    os.makedirs(static_dir, exist_ok=True)
    mp3_path = os.path.join(static_dir, filename)

    # 3. TTS Audio Generation
    logger.info(f"Generating TTS audio with Edge-TTS to {mp3_path}...")
    duration_seconds = generate_tts_audio(script_text, mp3_path, voice="vi-VN-HoaiMyNeural")
    audio_url = f"/static/podcasts/{filename}"

    # 4. Save to Database
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO osint_podcasts 
                (id, session, session_name, title, audio_url, duration_seconds, script_text, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (podcast_id, session_code, session_name, title, audio_url, duration_seconds, script_text))
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Successfully saved podcast record {podcast_id} to database.")
        except Exception as e:
            logger.error(f"Error saving podcast to DB: {e}")

    podcast_data = {
        "id": podcast_id,
        "session": session_code,
        "session_name": session_name,
        "title": title,
        "audio_url": audio_url,
        "duration_seconds": duration_seconds,
        "script_text": script_text,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # 5. Clean up old podcasts and audio files to free server storage
    try:
        cleanup_old_podcasts()
    except Exception as ex:
        logger.warning(f"Background podcast cleanup failed: {ex}")

    logger.info(f"Podcast generation completed successfully! Title: {title}, Duration: {duration_seconds}s")
    return podcast_data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    session_arg = sys.argv[1] if len(sys.argv) > 1 else None
    res = run_podcast_generation_pipeline(session_arg)
    print(json.dumps(res, ensure_ascii=False, indent=2))
