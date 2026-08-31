#!/usr/bin/env python3
import time
import os
import sys
import requests
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import psycopg2

# Load environment variables
env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_file_path):
    load_dotenv(env_file_path)
else:
    load_dotenv()

TV_CALENDAR_URL = "https://economic-calendar.tradingview.com/events"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/"
}

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'trading'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )

def init_economic_calendar_table():
    """Ensure public.economic_calendar table exists"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.economic_calendar (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                country VARCHAR(20) NOT NULL,
                event_time TIMESTAMPTZ NOT NULL,
                impact VARCHAR(20) DEFAULT 'Low',
                forecast VARCHAR(50),
                previous VARCHAR(50),
                actual VARCHAR(50),
                surprise VARCHAR(50),
                status VARCHAR(20) DEFAULT 'SCHEDULED',
                retry_count INT DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_economic_event UNIQUE(title, country, event_time)
            );
            CREATE INDEX IF NOT EXISTS idx_economic_calendar_event_time ON public.economic_calendar(event_time);
            CREATE INDEX IF NOT EXISTS idx_economic_calendar_status ON public.economic_calendar(status);
        """)
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"⚠️ [CALENDAR] Init table error: {e}")
    finally:
        if conn:
            conn.close()

def format_val(val, unit):
    if val is None:
        return ""
    u = unit or ""
    if isinstance(val, (int, float)):
        # Format nice float
        if isinstance(val, float) and val.is_integer():
            val_str = str(int(val))
        else:
            val_str = f"{val:.2f}".rstrip('0').rstrip('.')
        return f"{val_str}{u}"
    return f"{val}{u}"

def map_impact(importance):
    if importance is None:
        return 'Low'
    if importance >= 1:
        return 'High'
    elif importance == 0:
        return 'Medium'
    return 'Low'

def sync_weekly_economic_calendar():
    """Fetches full week economic calendar from TradingView and syncs to PostgreSQL"""
    now = datetime.now(timezone.utc)
    # Start of week (Monday)
    start_of_week = now - timedelta(days=now.weekday())
    start_str = start_of_week.strftime("%Y-%m-%dT00:00:00.000Z")
    # End of week (Sunday + 7 days)
    end_of_week = start_of_week + timedelta(days=7)
    end_str = end_of_week.strftime("%Y-%m-%dT23:59:59.000Z")

    print(f"📅 [CALENDAR] Đồng bộ lịch kinh tế từ {start_str[:10]} đến {end_str[:10]}...")
    try:
        resp = requests.get(f"{TV_CALENDAR_URL}?from={start_str}&to={end_str}", headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ [CALENDAR] API error: HTTP {resp.status_code}")
            return False

        data = resp.json().get('result', [])
        if not data:
            print("⚠️ [CALENDAR] Không có sự kiện nào trong tuần.")
            return False

        conn = get_db_connection()
        cur = conn.cursor()

        upsert_query = """
            INSERT INTO public.economic_calendar (
                title, country, event_time, impact, forecast, previous, actual, surprise, status, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (title, country, event_time) DO UPDATE SET
                impact = EXCLUDED.impact,
                forecast = COALESCE(NULLIF(EXCLUDED.forecast, ''), public.economic_calendar.forecast),
                previous = COALESCE(NULLIF(EXCLUDED.previous, ''), public.economic_calendar.previous),
                actual = COALESCE(NULLIF(EXCLUDED.actual, ''), public.economic_calendar.actual),
                status = CASE 
                    WHEN NULLIF(EXCLUDED.actual, '') IS NOT NULL THEN 'COMPLETED'
                    ELSE public.economic_calendar.status
                END,
                updated_at = CURRENT_TIMESTAMP;
        """

        count = 0
        for item in data:
            title = item.get('title', '').strip()
            country = item.get('country', '').strip()
            date_str = item.get('date')
            if not title or not country or not date_str:
                continue

            unit = item.get('unit', '')
            forecast = format_val(item.get('forecast'), unit)
            previous = format_val(item.get('previous'), unit)
            actual = format_val(item.get('actual'), unit)
            impact = map_impact(item.get('importance'))
            status = 'COMPLETED' if actual else 'SCHEDULED'

            surprise = ""
            if item.get('actual') is not None and item.get('forecast') is not None:
                try:
                    diff = float(item['actual']) - float(item['forecast'])
                    surprise = f"{'+' if diff > 0 else ''}{diff:.2f}{unit}".rstrip('0').rstrip('.')
                except Exception:
                    pass

            cur.execute(upsert_query, (
                title, country, date_str, impact, forecast, previous, actual, surprise, status
            ))
            count += 1

        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ [CALENDAR] Đã đồng bộ thành công {count} sự kiện kinh tế vào cơ sở dữ liệu.")
        
        # Tự động dọn dẹp dữ liệu cũ hơn 8 ngày ngay sau khi nạp lịch mới
        cleanup_stale_economic_calendar(days=8)
        return True
    except Exception as e:
        print(f"⚠️ [CALENDAR] Lỗi đồng bộ lịch kinh tế: {e}")
        return False

# Keep track of last daily sync
_last_daily_sync = 0

def monitor_economic_calendar_step():
    """
    Smart Event-Triggered Poller:
    - Only queries TradingView when High/Medium impact events are in the active window (NOW - 15m to NOW + 2m)
    - If events are waiting for actual numbers, performs micro-polling with max 8 retries
    - 99% of time, this function returns in 0.001s with 0 network requests
    """
    global _last_daily_sync
    current_timestamp = time.time()

    # 1. Daily Sync check (runs once every 24h or on initial launch)
    if current_timestamp - _last_daily_sync > 86400:
        if sync_weekly_economic_calendar():
            _last_daily_sync = current_timestamp

    # 2. Check if any High/Medium impact events are occurring right now
    conn = None
    pending_events = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Find events within [NOW - 15 minutes, NOW + 2 minutes] that have no actual number yet
        cur.execute("""
            SELECT id, title, country, event_time, impact, forecast, previous, retry_count
            FROM public.economic_calendar
            WHERE event_time <= NOW() + INTERVAL '2 minutes'
              AND event_time >= NOW() - INTERVAL '15 minutes'
              AND (actual IS NULL OR actual = '')
              AND status IN ('SCHEDULED', 'FETCHING')
              AND impact IN ('High', 'Medium')
            ORDER BY event_time ASC;
        """)
        pending_events = cur.fetchall()
        cur.close()
    except Exception as e:
        print(f"⚠️ [CALENDAR] Lỗi kiểm tra sự kiện: {e}")
    finally:
        if conn:
            conn.close()

    # If no pending events, return immediately (Zero network requests!)
    if not pending_events:
        return

    print(f"⚡ [CALENDAR] Phát hiện {len(pending_events)} sự kiện quan trọng trong khung giờ ra tin. Bắt đầu Smart Micro-Polling...")

    # Fetch today's real-time events from TradingView
    now = datetime.now(timezone.utc)
    today_start = now.strftime("%Y-%m-%dT00:00:00.000Z")
    today_end = now.strftime("%Y-%m-%dT23:59:59.000Z")

    try:
        resp = requests.get(f"{TV_CALENDAR_URL}?from={today_start}&to={today_end}", headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return

        live_data = resp.json().get('result', [])
        live_map = {}
        for item in live_data:
            key = f"{item.get('title', '').strip()}_{item.get('country', '').strip()}"
            live_map[key] = item

        conn = get_db_connection()
        cur = conn.cursor()

        for event in pending_events:
            ev_id, ev_title, ev_country, ev_time, ev_impact, ev_forecast, ev_previous, ev_retries = event
            key = f"{ev_title}_{ev_country}"
            live_item = live_map.get(key)

            if live_item and live_item.get('actual') is not None:
                unit = live_item.get('unit', '')
                actual_str = format_val(live_item.get('actual'), unit)
                
                surprise = ""
                if live_item.get('forecast') is not None:
                    try:
                        diff = float(live_item['actual']) - float(live_item['forecast'])
                        surprise = f"{'+' if diff > 0 else ''}{diff:.2f}{unit}".rstrip('0').rstrip('.')
                    except Exception:
                        pass

                cur.execute("""
                    UPDATE public.economic_calendar
                    SET actual = %s, surprise = %s, status = 'COMPLETED', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (actual_str, surprise, ev_id))
                conn.commit()

                print(f"🎯 [CALENDAR ALERT] ĐÃ CÓ ACTUAL CHO: {ev_title} ({ev_country}) | Actual: {actual_str} | Forecast: {ev_forecast} | Prev: {ev_previous}")
            else:
                new_retries = (ev_retries or 0) + 1
                new_status = 'NO_DATA' if new_retries >= 8 else 'FETCHING'
                cur.execute("""
                    UPDATE public.economic_calendar
                    SET retry_count = %s, status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (new_retries, new_status, ev_id))
                conn.commit()

        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ [CALENDAR] Lỗi trong Micro-Polling: {e}")

def cleanup_stale_economic_calendar(days=8):
    """Clean up economic calendar records older than `days` days (default: 8 days)"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM public.economic_calendar 
            WHERE event_time < NOW() - (%s || ' days')::INTERVAL;
        """, (str(days),))
        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        print(f"🧹 [CALENDAR] Đã dọn dẹp {deleted_count} sự kiện cũ hơn {days} ngày khỏi DB.")
        return deleted_count
    except Exception as e:
        print(f"⚠️ [CALENDAR] Lỗi dọn dẹp dữ liệu cũ: {e}")
        return 0
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_economic_calendar_table()
    sync_weekly_economic_calendar()
    monitor_economic_calendar_step()
    cleanup_stale_economic_calendar(8)
