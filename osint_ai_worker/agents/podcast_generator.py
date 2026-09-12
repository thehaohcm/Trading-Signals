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
    title: str = Field(description="Tiêu đề bản tin podcast hấp dẫn, súc tích (Ví dụ: 'Bản Tin Macro Phiên Mỹ: Toàn Cảnh Sóng Tin High Impact Tuần Này & Kịch Bản Giao Dịch Vàng, Stock, Crypto, Forex')")
    session_focus: str = Field(description="Điểm nhấn cốt lõi nhất của phiên giao dịch và tin tức High Impact trong tuần (1-2 câu)")
    script_text: str = Field(
        description="Toàn văn kịch bản phát thanh tiếng Việt hoàn chỉnh (khoảng 480 - 620 từ, tương đương 3 đến 4 phút đọc lưu loát). "
                    "Văn phong phát thanh viên tài chính chuyên nghiệp, đĩnh đạc, mạch lạc, dễ nghe khi phát âm qua giọng đọc TTS. "
                    "Bao gồm đầy đủ 4 phần: Tổng quan bức tranh liên thị trường, Toàn cảnh các tin tức High Impact trọng tâm trong tuần, "
                    "Phân tích kịch bản chi tiết (Scenario Playbook cho Vàng, Chứng khoán, Crypto, Forex), và Chiến lược hành động quản trị rủi ro trước giờ ra tin."
    )

# ==========================================
# HELPER FUNCTIONS
# ==========================================

import urllib.request
import urllib.error
import requests
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

def get_vietnam_time() -> datetime:
    """Get current time in Vietnam Timezone (UTC+7)"""
    return datetime.now(timezone(timedelta(hours=7)))

def fetch_live_market_prices() -> str:
    """
    Fetch live inter-market prices (Gold, Silver, WTI Oil, Brent Oil, DXY, US10Y, S&P 500, Nasdaq, BTC, USD/VND)
    via yfinance in parallel.
    """
    tickers_config = [
        ("Vàng Thế Giới (Gold Futures / XAUUSD)", "GC=F", "USD/ounce"),
        ("Bạc Thế Giới (Silver Futures)", "SI=F", "USD/ounce"),
        ("Dầu Thô WTI (Crude Oil)", "CL=F", "USD/thùng"),
        ("Dầu Thô Brent", "BZ=F", "USD/thùng"),
        ("Chỉ số Sức mạnh Đô la Mỹ (DXY Index)", "DX-Y.NYB", "điểm"),
        ("Lợi suất Trái phiếu Mỹ 10 năm (US10Y)", "^TNX", "%"),
        ("Chỉ số Chứng khoán Mỹ S&P 500", "^GSPC", "điểm"),
        ("Chỉ số Chứng khoán Mỹ Nasdaq 100", "QQQ", "USD"),
        ("Tiền mã hóa Bitcoin (BTC/USD)", "BTC-USD", "USD"),
        ("Tỷ giá USD/VND (Liên ngân hàng)", "USDVND=X", "VND")
    ]

    def _fetch_single_ticker(name, sym, unit):
        try:
            t = yf.Ticker(sym)
            price = t.fast_info.get('lastPrice')
            prev_close = t.fast_info.get('previousClose')
            if price is None:
                hist = t.history(period='2d')
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    if len(hist) > 1:
                        prev_close = float(hist['Close'].iloc[-2])
            
            chg_pct = 0.0
            if price is not None and prev_close:
                chg_pct = ((price - prev_close) / prev_close) * 100
            return name, sym, unit, price, chg_pct
        except Exception as e:
            logger.warning(f"Error fetching ticker {sym}: {e}")
            return name, sym, unit, None, 0.0

    lines = []
    try:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_fetch_single_ticker, name, sym, unit) for name, sym, unit in tickers_config]
            for f in futures:
                name, sym, unit, price, chg_pct = f.result()
                if price is not None:
                    sign = "+" if chg_pct >= 0 else ""
                    lines.append(f"- {name} [{sym}]: {price:,.2f} {unit} ({sign}{chg_pct:.2f}%)")
                else:
                    lines.append(f"- {name} [{sym}]: Đang cập nhật")
    except Exception as e:
        logger.error(f"Error fetching live market prices: {e}")
        return "Dữ liệu thị trường trực tiếp đang được cập nhật."

    return "\n".join(lines)

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

def fetch_weekly_high_impact_events(target_dt: Optional[datetime] = None) -> list[dict]:
    """
    Fetch all High-Impact and notable Medium-Impact events for the ENTIRE week (Monday through Sunday)
    and upcoming key events with formatted Vietnamese day labels.
    """
    if target_dt is None:
        target_dt = get_vietnam_time()

    all_events = _fetch_all_raw_events()
    weekly_events = []
    vietnam_weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

    # Calculate Monday 00:00 of the current week to Sunday 23:59:59 (and lookahead 7 days)
    start_of_week = (target_dt - timedelta(days=target_dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=7, hours=6) # include early next week if close

    for ev in all_events:
        ev_dt = ev.get("datetime_vn")
        if not ev_dt:
            continue

        if start_of_week <= ev_dt <= end_of_week:
            weekday_name = vietnam_weekdays[ev_dt.weekday()]
            day_formatted = f"{weekday_name} ({ev_dt.strftime('%d/%m')})"
            ev_copy = dict(ev)
            ev_copy["day_vn"] = day_formatted
            ev_copy["is_today"] = (ev_dt.strftime('%Y-%m-%d') == target_dt.strftime('%Y-%m-%d'))
            ev_copy["is_upcoming"] = (ev_dt >= target_dt - timedelta(hours=2))
            weekly_events.append(ev_copy)

    # Sort events chronologically
    weekly_events.sort(key=lambda x: x["datetime_vn"])
    return weekly_events

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

def fetch_osint_data_for_podcast() -> tuple[dict, list, list, list, list]:
    """
    Fetch Current World State, Platform Intelligence (Theses), recent OSINT Signals,
    Active Rising/Breakout Alerts, and Latest OSINT News Items.
    """
    db_url = os.getenv("DATABASE_URL")
    world_state = {}
    theses = []
    signals = []
    alerts = []
    news_items = []
    
    if not db_url:
        return world_state, theses, signals, alerts, news_items

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

        # 5. Latest OSINT Breaking News (last 48 hours)
        try:
            cur.execute("""
                SELECT title, content, importance, created_at
                FROM news_items
                WHERE created_at > NOW() - INTERVAL '48 hours'
                ORDER BY 
                    CASE importance 
                        WHEN 'critical' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3 
                        ELSE 4 
                    END,
                    created_at DESC
                LIMIT 10
            """)
            news_items = cur.fetchall()
        except Exception as ne:
            logger.warning(f"Could not fetch news_items: {ne}")
            conn.rollback()

        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error fetching data for podcast: {e}")

    return world_state, theses, signals, alerts, news_items

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

PODCAST_PROMPT_TEMPLATE = """Bạn là Trưởng ban Phân tích Chiến lược Vĩ mô kiêm Phát thanh viên Cao cấp của nền tảng Trading Signals.
Nhiệm vụ của bạn là soạn kịch bản và phát thanh một bản tin âm thanh Podcast (dạng Pre-Market Briefing & Macro Scenario Playbook) chuyên sâu, sắc bén và chất lượng cao cho {session_name} ({today_date}).

BẢN TIN PHỤC VỤ CÁC TRADER & NHÀ ĐẦU TƯ TÀI CHÍNH TRÊN CÁC THỊ TRƯỜNG VÀNG (GOLD), CHỨNG KHOÁN (US & VN), CRYPTO (BITCOIN) VÀ NGOẠI HỐI (FOREX).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THÔNG TIN THỜI GIAN & TRẠNG THÁI THỊ TRƯỜNG HIỆN TẠI:
- HÔM NAY: {today_date} (Giờ Việt Nam)
- TRẠNG THÁI HOẠT ĐỘNG CỦA CÁC THỊ TRƯỜNG:
{market_schedule_info}

DƯỚI ĐÂY LÀ DỮ LIỆU THỰC TẾ TỪ HỆ THỐNG OSINT & VĨ MÔ:

1. GIÁ CẢ THỊ TRƯỜNG THỜI GIAN THỰC (Real-Time Live Market Prices - Nguồn dữ liệu trực tiếp yfinance):
{live_market_prices_text}

2. TRẠNG THÁI THẾ GIỚI HIỆN TẠI (Current World State - Vĩ mô, NHTW, Địa chính trị, Lợi suất Trái phiếu, Thanh khoản & Năng lượng):
{world_state_text}

3. TIN TỨC VĨ MÔ & ĐỊA CHÍNH TRỊ OSINT MỚI NHẤT (Breaking OSINT News Feeds):
{osint_news_text}

4. TOÀN BỘ LỊCH SỰ KIỆN KINH TẾ & TIN TỨC HIGH IMPACT QUAN TRỌNG TRONG TUẦN NÀY:
{weekly_high_impact_text}

5. SỰ KIỆN KINH TẾ TRỌNG TÂM NGAY TRONG PHIÊN NÀY ({session_name}):
{session_events_text}

6. NHẬN ĐỊNH VÀ LUẬN ĐIỂM VĨ MÔ TỪ PLATFORM INTELLIGENCE:
{theses_text}

7. CÁC TÍN HIỆU OSINT & CẢNH BÁO ALERT BIẾN ĐỘNG GIÁ MỚI NHẤT:
{signals_and_alerts_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YÊU CẦU BIÊN TẬP KỊCH BẢN PHÁT THANH (SCRIPT_TEXT):
1. ĐỘ DÀI & THỜI LƯỢNG: Khoảng 480 - 620 từ (đọc trong 3 đến 4 phút lưu loát).
2. GIỌNG ĐIỆU & PHONG THÁI:
   - Tự nhiên, đĩnh đạc, nhịp điệu dứt khoát, chuyên nghiệp và giàu hàm lượng tri thức thực chiến như Bloomberg Radio, Reuters Market Briefing hoặc Morgan Stanley Audio.
   - Phát âm các thuật ngữ tài chính tiếng Anh một cách tự nhiên và chính xác (CPI, Core PPI, FOMC, Non-Farm Payrolls, GDP, DXY, Vàng Spot XAU/USD, Lợi suất US10Y, S&P 500, VN-Index, Bitcoin ETF, EUR/USD, USD/JPY...).
   - Tận dụng hiệu quả dữ liệu Trạng thái Thế giới (World State), Tin tức OSINT, sự kiện High Impact và các mốc giá thực tế để tạo nên nội dung phân tích đa chiều và thuyết phục.

⚠️ NGUYÊN TẮC BẮT BUỘC VỀ SỐ LIỆU GIÁ THỊ TRƯỜNG THỜI GIAN THỰC:
- BẮT BUỘC sử dụng chính xác các con số giá thị trường thời gian thực được cung cấp ở mục 1 (Đặc biệt: Giá Vàng Spot/Futures XAU/USD hiện tại đang ở vùng thực tế ~4,400+ USD/ounce, Bitcoin, DXY, Lợi suất US10Y...).
- TUYỆT ĐỐI KHÔNG sử dụng các mốc giá cũ trong quá khứ hoặc tự hallucinate (Ví dụ TUYỆT ĐỐI KHÔNG ĐƯỢC nói giá vàng là 2,500 hay 2,600 USD/ounce). Tất cả các mốc giá và kịch bản phân tích cho Vàng, Dầu, Crypto, Chứng khoán PHẢI bám sát theo vùng giá thời gian thực này.

3. CẤU TRÚC BẢN TIN BẮT BUỘC GỒM 4 PHẦN CHẶT CHẼ (ĐIỀU CHỈNH THEO NGÀY THƯỜNG HOẶC NGÀY NGHỈ CUỐI TUẦN):

   ◆ PHẦN 1: MỞ ĐẦU & BỨC TRANH LIÊN THỊ TRƯỜNG
     - Chào đón quý nhà đầu tư đến với {session_name} ({today_date}).
     - Nêu rõ bối cảnh ngày giao dịch: Xác định rõ hôm nay là ngày trong tuần hay ngày nghỉ cuối tuần (Thứ Bảy / Chủ Nhật).
     - Điểm nhanh xu hướng và số liệu giá thị trường thời gian thực: Giá Vàng thế giới (nêu rõ mốc giá live hiện tại), Chỉ số DXY (Đô la Mỹ), Lợi suất Trái phiếu Mỹ 10 năm, Dầu thô, TTCK Mỹ/VN và Bitcoin.
     - Lồng ghép ngắn gọn bối cảnh vĩ mô / địa chính trị nổi bật từ Current World State & Tin tức OSINT.

   ◆ PHẦN 2: TOÀN CẢNH CÁC TIN TỨC HIGH IMPACT TRỌNG TÂM
     - Nếu là ngày trong tuần: Điểm danh rõ ràng các sự kiện kinh tế / tin tức High Impact sẽ diễn ra trong tuần (ví dụ: CPI, PPI, FOMC, Non-Farm Payrolls...). Nêu rõ thời điểm (thứ mấy, ngày nào, mốc giờ Việt Nam) và kỳ vọng.
     - Nếu là Thứ Bảy / Chủ Nhật (Cuối tuần): Tổng kết ngắn gọn các sự kiện lớn vừa diễn ra trong tuần qua và điểm danh trước các tin tức High Impact tâm điểm của tuần tới mà nhà đầu tư cần chuẩn bị đón đầu.

   ◆ PHẦN 3: PHÂN TÍCH KỊCH BẢN CHI TIẾT (SCENARIO PLAYBOOK) CHO TỪNG LỚP TÀI SẢN
     - LƯU Ý PHÂN TÍCH BÁM SÁT TRẠNG THÁI HOẠT ĐỘNG CỦA CÁC THỊ TRƯỜNG:
       • 🪙 CRYPTO (Bitcoin & Altcoins): 
         - Nếu là Thứ Bảy / Chủ Nhật: Nhấn mạnh Crypto là thị trường DUY NHẤT hoạt động 24/7. Cảnh báo đặc tính thanh khoản mỏng cuối tuần (low liquidity), thị trường dễ bị quét 2 đầu hoặc bẫy giá (fake breakout), khuyến nghị hạn chế giao dịch lướt sóng đòn bẩy cao. ĐẶC BIỆT: Nhấn mạnh nếu có tin tức kinh tế, chính trị hoặc sự kiện thiên nga đen khẩn cấp phát sinh trong ngày nghỉ cuối tuần, Crypto sẽ là kênh tài sản đầu tiên và duy nhất chịu tác động, phản ánh biến động ngay lập tức trước khi thị trường truyền thống mở cửa vào sáng Thứ Hai.
         - Nếu là ngày trong tuần: Phân tích tác động của thanh khoản vĩ mô, dòng vốn Bitcoin Spot ETF và khẩu vị rủi ro thị trường tiền mã hóa.
       • 🥇 VÀNG (Gold / XAUUSD): 
         - Nếu cuối tuần: Nhắc nhở thị trường Vàng đang đóng cửa nghỉ giao dịch, tổng kết vùng giá chốt tuần và xây dựng kịch bản hỗ trợ / kháng cự quan trọng khi mở phiên đầu tuần.
         - Nếu trong tuần: Phân tích kịch bản số liệu Hawkish (Vàng chịu áp lực điều chỉnh về hỗ trợ nào) vs Dovish (Vàng bứt phá chinh phục mốc cản mới).
       • 📈 CHỨNG KHOÁN (US Stocks & VN-Index): 
         - Nếu cuối tuần: Nêu rõ chứng khoán VN và Mỹ đang đóng cửa nghỉ cuối tuần, điểm lại trạng thái tuần qua và xu hướng chuẩn bị cho tuần tới.
         - Nếu trong tuần: Phân tích xu hướng nhóm Cổ phiếu Công nghệ (Nasdaq/Tech), S&P 500 và phản ứng của dòng tiền tự doanh/khối ngoại trên VN-Index.
       • 💱 FOREX & NGOẠI HỐI: 
         - Nếu cuối tuần: Đang đóng cửa nghỉ giao dịch, điểm lại mức chốt của DXY và tác động lên tỷ giá USD/VND.
         - Nếu trong tuần: Xu hướng sức mạnh đồng USD (DXY), các cặp tỷ giá chủ đạo (EUR/USD, USD/JPY) và USD/VND.

   ◆ PHẦN 4: CHIẾN LƯỢC HÀNH ĐỘNG & NGUYÊN TẮC QUẢN TRỊ RỦI RO
     - Nếu là Thứ Bảy / Chủ Nhật: Khuyến nghị nhà đầu tư nghỉ ngơi tái tạo năng lượng, kỷ luật hạn chế giao dịch fomo trên thị trường crypto thanh khoản thấp, sẵn sàng kế hoạch cho tuần giao dịch mới.
     - Nếu là ngày trong tuần: Khuyến nghị hạn chế mở vị thế lớn sát thời điểm công bố tin High Impact để tránh giãn spread, tuân thủ kỷ luật Stop-Loss chặt chẽ.

Hãy tạo ra một bản tin âm thanh Podcast hoàn hảo, hấp dẫn và thực chiến theo đúng JSON Schema đã định nghĩa.
"""

def format_world_state_to_text(world_state: dict) -> str:
    """Format Current World State dict into clean, structured readable bullet points"""
    if not world_state:
        return "Hệ thống đang duy trì theo dõi trạng thái vĩ mô toàn cầu ổn định."
    
    lines = []
    for entity, val in world_state.items():
        if entity.startswith('_'):
            continue
        if isinstance(val, dict):
            details = []
            for k, v in val.items():
                if not k.startswith('_') and v is not None and str(v).strip():
                    details.append(f"{k}: {v}")
            if details:
                lines.append(f"• **{entity}**: " + " | ".join(details))
            else:
                lines.append(f"• **{entity}**: Trạng thái ổn định")
        else:
            lines.append(f"• **{entity}**: {val}")
            
    return "\n".join(lines) if lines else json.dumps(world_state, ensure_ascii=False, indent=2)

def generate_podcast_script(session_code: str, session_name: str) -> dict:
    """Generate podcast script from DB data, live yfinance market prices, ForexFactory calendar, and live alerts using LLM"""
    world_state, theses, signals, alerts, news_items = fetch_osint_data_for_podcast()
    weekly_events = fetch_weekly_high_impact_events()
    session_events = fetch_forexfactory_events_for_session(session_code)
    live_market_prices_str = fetch_live_market_prices()

    vn_now = get_vietnam_time()
    weekday_map = {
        0: "Thứ Hai",
        1: "Thứ Ba",
        2: "Thứ Tư",
        3: "Thứ Năm",
        4: "Thứ Sáu",
        5: "Thứ Bảy",
        6: "Chủ Nhật"
    }
    weekday_vn = weekday_map.get(vn_now.weekday(), "Thứ")
    today_date = f"{weekday_vn}, ngày {vn_now.strftime('%d/%m/%Y')}"
    is_weekend = vn_now.weekday() in [5, 6]

    if is_weekend:
        market_schedule_info = f"""⚠️ LƯU Ý QUAN TRỌNG VỀ LỊCH GIAO DỊCH CUỐI TUẦN ({weekday_vn.upper()}):
1. THỊ TRƯỜNG TRUYỀN THỐNG ĐANG NGHỈ GIAO DỊCH:
   - Thị trường Chứng khoán Việt Nam (VN-Index), Chứng khoán Mỹ (S&P 500, Nasdaq, Dow Jones), Thị trường Ngoại hối (Forex) và Thị trường Hàng hóa (Vàng Spot/Futures XAU/USD, Dầu thô WTI/Brent, Bạc) đều ĐANG ĐÓNG CỬA nghỉ giao dịch cuối tuần từ đêm Thứ Sáu đến sáng Thứ Hai.
   - Các nhận định cho Vàng, Chứng khoán, Forex mang tính tổng kết tuần qua, đánh giá trạng thái đóng nến tuần và chuẩn bị kịch bản cho phiên mở cửa đầu tuần mới.
2. THỊ TRƯỜNG TIỀN MÃ HÓA (CRYPTO / BITCOIN) HOẠT ĐỘNG 24/7:
   - Thị trường Crypto là thị trường DUY NHẤT vẫn mở cửa giao dịch xuyên suốt Thứ 7 và Chủ Nhật.
   - ĐẶC ĐIỂM THANH KHOẢN THẤP & RỦI RO CUỐI TUẦN: Vào Thứ 7 và Chủ Nhật, thanh khoản thị trường tiền số thường sụt giảm mạnh (low liquidity), dễ xuất hiện các đợt giật quét 2 đầu biên giá (fake breakout / stop-hunt). Khuyến nghị nhà đầu tư HẠN CHẾ giao dịch lướt sóng đòn bẩy cao, ưu tiên quan sát bảo toàn vốn.
   - BỘ ĐỆM ĐÓN ĐẦU TIN TỨC KHẨN CẤP: Nếu có tin tức địa chính trị, kinh tế vĩ mô khẩn cấp (breaking news / black swan) bùng nổ trong ngày nghỉ cuối tuần, Crypto là kênh tài sản đầu tiên và duy nhất chịu tác động và hấp thụ biến động ngay lập tức trước khi các thị trường truyền thống mở cửa trở lại vào sáng Thứ Hai."""
    else:
        market_schedule_info = f"""✅ LỊCH GIAO DỊCH NGÀY TRONG TUẦN ({weekday_vn.upper()}):
- Toàn bộ các thị trường tài chính (Chứng khoán Việt Nam, Chứng khoán Mỹ, Ngoại hối Forex, Vàng, Dầu thô, Bạc và Crypto) đều đang hoạt động bình thường theo các phiên Á, Âu, Mỹ."""

    world_state_str = format_world_state_to_text(world_state)
    
    news_items_str = ""
    if news_items:
        for n in news_items:
            imp = (n.get('importance') or 'INFO').upper()
            imp_tag = f"[{imp}]"
            title = n.get('title', '').strip()
            content = (n.get('content') or '').strip()
            if content and content != title:
                news_items_str += f"- {imp_tag} {title} (Tóm tắt: {content[:150]}...)\n"
            else:
                news_items_str += f"- {imp_tag} {title}\n"
    else:
        news_items_str = "Chưa ghi nhận tin tức đột biến khẩn cấp trong 24-48 giờ qua."

    theses_str = ""
    if theses:
        for i, t in enumerate(theses, 1):
            theses_str += f"- Nhận định #{i}: {t.get('thesis', '')}\n  + Tư vấn hành động & bảo vệ tài sản: {t.get('supporting_evidence', '')}\n  + Độ tin cậy: {int((t.get('confidence') or 0.8) * 100)}%\n"
    else:
        theses_str = "Hệ thống đang duy trì theo dõi trạng thái vĩ mô tích cực trung hạn."

    signals_and_alerts_str = ""
    if signals:
        signals_and_alerts_str += "TÍN HIỆU VĨ MÔ OSINT:\n"
        for s in signals[:8]:
            signals_and_alerts_str += f"- [{s.get('category', 'Macro')}] {s.get('signal', '')}: {s.get('reason', '')}\n"
    
    if alerts:
        signals_and_alerts_str += "\nCẢNH BÁO DÒNG TIỀN / BREAKOUT LIVE:\n"
        for a in alerts[:6]:
            atype = a.get('asset_type', '').upper()
            sym = a.get('symbol', '')
            price = a.get('price', '')
            msg = a.get('message', '')
            signals_and_alerts_str += f"- [{atype}] {sym} @ {price}: {msg}\n"
    
    if not signals_and_alerts_str:
        signals_and_alerts_str = "Dòng tiền trên các lớp tài sản đang vận động tích lũy ổn định."

    # Format weekly high impact events
    weekly_high_impact_str = ""
    if weekly_events:
        for ev in weekly_events:
            if ev['impact'] == 'High' or (ev['impact'] == 'Medium' and ev.get('is_upcoming')):
                impact_tag = "🔴 [HIGH IMPACT - BIẾN ĐỘNG CỰC MẠNH]" if ev['impact'] == 'High' else "🟠 [MEDIUM IMPACT]"
                fc_info = f"Dự báo: {ev['forecast']}" if ev['forecast'] else "Không có dự báo"
                prev_info = f"Kỳ trước: {ev['previous']}" if ev['previous'] else "Chưa có kỳ trước"
                today_tag = "👉 [HÔM NAY]" if ev.get('is_today') else f"📅 [{ev.get('day_vn', '')}]"
                weekly_high_impact_str += f"- {today_tag} {ev['time_vn']} Giờ VN | [{ev['country']}] {ev['title']} | {impact_tag} | {fc_info} | {prev_info}\n"
    
    if not weekly_high_impact_str:
        weekly_high_impact_str = "Tuần này không có tin tức High Impact đột biến từ các nền kinh tế lớn. Thị trường sẽ ưu tiên chạy theo kỹ thuật và dòng tiền tự nhiên."

    # Format session-specific events
    session_events_str = ""
    if session_events:
        for ev in session_events:
            impact_tag = "🔴 RẤT QUAN TRỌNG (High)" if ev['impact'] == 'High' else "🟠 QUAN TRỌNG VỪA (Medium)"
            fc_info = f"Dự báo: {ev['forecast']}" if ev['forecast'] else "Không có dự báo"
            prev_info = f"Kỳ trước: {ev['previous']}" if ev['previous'] else "Chưa có kỳ trước"
            session_events_str += f"- {ev['time_vn']} (Giờ VN) | [{ev['country']}] {ev['title']} | Mức độ: {impact_tag} | {fc_info} | {prev_info}\n"
    else:
        session_events_str = "Không có tin tức kinh tế quan trọng nào công bố trực tiếp trong khung giờ của phiên này. Thị trường dự kiến giao dịch thuần kỹ thuật."

    prompt = PODCAST_PROMPT_TEMPLATE.format(
        session_name=session_name,
        today_date=today_date,
        market_schedule_info=market_schedule_info,
        live_market_prices_text=live_market_prices_str,
        world_state_text=world_state_str,
        osint_news_text=news_items_str,
        weekly_high_impact_text=weekly_high_impact_str,
        session_events_text=session_events_str,
        theses_text=theses_str,
        signals_and_alerts_text=signals_and_alerts_str
    )

    logger.info(f"Generating podcast script with LLM for {session_name} ({today_date})...")
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
