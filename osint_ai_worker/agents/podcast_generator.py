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
    title: str = Field(description="Tiêu đề bản tin podcast hấp dẫn, súc tích (Ví dụ: 'Bản Tin Macro Phiên Á: DXY Chững Lại, Vàng và Dầu Giữ Nhịp Trước Giờ Mở Cửa')")
    session_focus: str = Field(description="Điểm nhấn cốt lõi nhất của phiên giao dịch (1-2 câu)")
    script_text: str = Field(
        description="Toàn văn kịch bản phát thanh tiếng Việt hoàn chỉnh (khoảng 350 - 450 từ, tương đương 2 đến 3 phút đọc). "
                    "Văn phong phát thanh viên tài chính chuyên nghiệp, mạch lạc, lôi cuốn, dễ nghe khi phát âm qua giọng đọc TTS. "
                    "Bao gồm đầy đủ: Lời chào phiên mới, Điểm tin liên thị trường (DXY, Trái phiếu, Vàng, Dầu, Cổ phiếu), "
                    "Tâm điểm vĩ mô từ World State (NHTW, Thanh khoản), Nhận định Platform Intelligence & Tư vấn phân bổ danh mục bảo vệ tài sản, "
                    "và Lời dặn dò quản trị rủi ro trước phiên."
    )

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_vietnam_time() -> datetime:
    """Get current time in Vietnam Timezone (UTC+7)"""
    return datetime.now(timezone(timedelta(hours=7)))

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

def fetch_osint_data_for_podcast() -> tuple[dict, list, list]:
    """
    Fetch Current World State, Platform Intelligence (Theses), and recent OSINT Signals.
    """
    db_url = os.getenv("DATABASE_URL")
    world_state = {}
    theses = []
    signals = []
    
    if not db_url:
        return world_state, theses, signals

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

        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error fetching data for podcast: {e}")

    return world_state, theses, signals

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YÊU CẦU BIÊN TẬP KỊCH BẢN (SCRIPT_TEXT):
1. ĐỘ DÀI & THỜI LƯỢNG: Khoảng 350 - 450 từ (đọc trong 2 đến 3 phút).
2. GIỌNG ĐIỆU & PHONG CÁCH:
   - Tự nhiên, đĩnh đạc, nhịp điệu dứt khoát, phong thái bản tin tài chính quốc tế như Bloomberg Radio hoặc Reuters Audio Briefing.
   - Phát âm các thuật ngữ vĩ mô tự nhiên (FED, FOMC, CPI, DXY, Vàng XAU, Lợi suất trái phiếu Mỹ 10 năm, Crypto, RWA...).
3. CẤU TRÚC BẢN TIN BẮT BUỘC:
   - PHẦN 1 - MỞ ĐẦU: Chào đón quý nhà đầu tư đến với {session_name}. Điểm nhanh bức tranh liên thị trường (Chỉ số DXY, Lợi suất, Vàng, Dầu, Chứng khoán).
   - PHẦN 2 - TÂM ĐIỂM VĨ MÔ (Current World State): Điểm nhấn chính sách các NHTW (FED, ECB, BOJ, SBV...) và trạng thái dòng tiền/thanh khoản toàn cầu.
   - PHẦN 3 - CHIẾN LƯỢC & HÀNH ĐỘNG (Platform Intelligence): Tóm tắt nhận định cốt lõi và tư vấn danh mục (Tỷ lệ phân bổ tiền mặt, vàng, bất động sản hoặc nhóm ngành cần thận trọng/ưu tiên).
   - PHẦN 4 - TRỌNG TÂM PHIÊN & KẾT THÚC: Nhắc nhở các sự kiện, chỉ số kinh tế cần theo dõi trong phiên sắp tới và lời chúc giao dịch an toàn, kỷ luật.

Hãy tạo ra một bản tin hoàn hảo theo JSON Schema được yêu cầu.
"""

def generate_podcast_script(session_code: str, session_name: str) -> dict:
    """Generate podcast script from DB data using LLM"""
    world_state, theses, signals = fetch_osint_data_for_podcast()

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

    prompt = PODCAST_PROMPT_TEMPLATE.format(
        session_name=session_name,
        today_date=today_date,
        world_state_text=world_state_str,
        theses_text=theses_str,
        signals_text=signals_str
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

    logger.info(f"Podcast generation completed successfully! Title: {title}, Duration: {duration_seconds}s")
    return podcast_data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    session_arg = sys.argv[1] if len(sys.argv) > 1 else None
    res = run_podcast_generation_pipeline(session_arg)
    print(json.dumps(res, ensure_ascii=False, indent=2))
