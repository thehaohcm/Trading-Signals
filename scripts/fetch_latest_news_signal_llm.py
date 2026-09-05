import os
import psycopg2
import time
import requests
from dotenv import load_dotenv

# 1. Load biến môi trường
load_dotenv()

# 9Router API config
ROUTER_API_ENDPOINT = os.getenv("ROUTER_API_ENDPOINT") or os.getenv("NINE_ROUTER_ENDPOINT") or "http://152.53.208.182:20128/v1"
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY") or os.getenv("NINE_ROUTER_API_KEY")
ROUTER_COMBO_NAME = os.getenv("ROUTER_COMBO_NAME") or os.getenv("NINE_ROUTER_MODEL") or "my-combo"

# Google Gen AI fallback
GENAI_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
genai_client = None
if GENAI_KEY:
    try:
        from google import genai
        from google.genai import types
        genai_client = genai.Client(api_key=GENAI_KEY)
    except Exception as e:
        print(f"⚠️ Không thể khởi tạo Google GenAI Client: {e}")

# Cấu hình file prompt (fallback)
PROMPT_FILE = "prompt_llm_ai.txt"

def get_db_connection():
    """Hàm kết nối Database Postgres"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except Exception as e:
        print(f"❌ Lỗi kết nối DB: {e}")
        return None

def read_prompt_file():
    if not os.path.exists(PROMPT_FILE):
        print(f"❌ Không tìm thấy file {PROMPT_FILE}")
        return None
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()

def get_ai_prompt_from_db():
    """Read AI prompt template from system_settings table"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM system_settings WHERE key = 'ai_prompt_template'")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and row[0] and row[0].strip():
            return row[0]
    except Exception as e:
        print(f"⚠️ Không thể đọc prompt từ DB: {e}")
    finally:
        if conn:
            conn.close()
    return None

def is_ai_enabled():
    """Check if AI features are enabled via system_settings"""
    conn = get_db_connection()
    if conn is None:
        return True  # Default to enabled if can't check
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM system_settings WHERE key = 'ai_enabled'")
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row and row[0].lower() == 'true'
    except Exception as e:
        print(f"⚠️ Không thể kiểm tra ai_enabled: {e}")
        return True
    finally:
        if conn:
            conn.close()

def generate_market_signal(prompt_text):
    """Gọi 9Router (my-combo) trước, nếu lỗi -> fallback sang Gemini"""
    # 1. Thử qua 9Router (my-combo)
    if ROUTER_API_KEY:
        print(f"⏳ [1/2] Đang gọi 9Router ({ROUTER_COMBO_NAME})...")
        try:
            router_url = ROUTER_API_ENDPOINT.rstrip("/") + "/chat/completions"
            payload = {
                "model": ROUTER_COMBO_NAME,
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": "Bạn là chuyên gia phân tích thị trường tài chính và tín hiệu vĩ mô. Hãy phân tích chuyên sâu và súc tích bằng Tiếng Việt."
                    },
                    {
                        "role": "user",
                        "content": prompt_text
                    }
                ],
                "temperature": 0.3
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ROUTER_API_KEY}"
            }
            resp = requests.post(router_url, json=payload, headers=headers, timeout=90)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    text = choices[0].get("message", {}).get("content", "").strip()
                    if text:
                        print(f"✅ Thành công lấy tín hiệu từ 9Router ({ROUTER_COMBO_NAME})!")
                        return text, ROUTER_COMBO_NAME
            else:
                print(f"⚠️ 9Router trả về status {resp.status_code}: {resp.text[:200]}. Chuyển sang Gemini...")
        except Exception as e:
            print(f"⚠️ Lỗi kết nối 9Router: {e}. Chuyển sang Gemini fallback...")

    # 2. Fallback: Gọi Gemini
    if genai_client:
        print("⏳ [2/2] Đang gọi Gemini fallback...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = genai_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt_text,
                    config=types.GenerateContentConfig(
                        response_mime_type="text/plain"
                    )
                )
                if response and response.text:
                    print("✅ Thành công lấy tín hiệu từ Gemini fallback!")
                    return response.text, "gemini-2.0-flash"
            except Exception as e:
                print(f"⚠️ Lần {attempt + 1}/{max_retries} Gemini thất bại: {e}")
                if "503" in str(e) or "429" in str(e):
                    time.sleep(10)
                else:
                    break

    print("❌ Đã thử hết các nhà cung cấp AI nhưng không thành công.")
    return None, None

def save_to_db(content, original_prompt, model_name="my-combo"):
    """Lưu kết quả vào Postgres"""
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()
        
        # Xóa sạch bảng cũ để chỉ giữ 1 bài mới nhất
        cur.execute("TRUNCATE TABLE trading_news_signals RESTART IDENTITY;") 
        
        sql = """
            INSERT INTO trading_news_signals (content, raw_prompt, model_used, status)
            VALUES (%s, %s, %s, %s)
        """
        cur.execute(sql, (content, original_prompt, model_name, "done"))
        
        conn.commit()
        cur.close()
        print(f"✅ THÀNH CÔNG: Đã cập nhật tín hiệu từ {model_name}!")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Lỗi khi lưu DB: {e}")
    finally:
        if conn:
            conn.close()

def main():
    if not is_ai_enabled():
        print("⏸️ AI features bị tắt (ai_enabled=false). Thoát.")
        return

    # Try DB first, fallback to file
    prompt_content = get_ai_prompt_from_db()
    if prompt_content:
        print("✅ Đọc prompt từ system_settings (DB)")
    else:
        print("⚠️ Không có prompt trong DB, đọc từ file...")
        prompt_content = read_prompt_file()
    
    if not prompt_content:
        print("❌ Không có prompt. Thoát.")
        return
    
    print(prompt_content)

    ai_result, model_used = generate_market_signal(prompt_content)
    
    if ai_result:
        save_to_db(ai_result, prompt_content, model_used or "my-combo")
    else:
        print("⚠️ Không nhận được kết quả từ AI.")

if __name__ == "__main__":
    main()