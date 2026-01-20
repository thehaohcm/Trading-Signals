import os
import psycopg2
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Load biến môi trường
load_dotenv()

# Cấu hình Client mới (Google Gen AI SDK mới)
GENAI_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GENAI_KEY)

# Cấu hình file prompt
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

def generate_market_signal(prompt_text):
    """Gọi AI với cơ chế tự thử lại (Retry) khi Server quá tải"""
    print("⏳ Đang gọi Gemini & Google Search...")
    
    # Thử tối đa 3 lần
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", # Hoặc gemini-1.5-flash
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    response_mime_type="text/plain"
                )
            )
            return response.text
            
        except Exception as e:
            print(f"⚠️ Lần {attempt + 1}/{max_retries} thất bại: {e}")
            if "503" in str(e) or "429" in str(e):
                # Nếu lỗi quá tải (503) hoặc quá giới hạn (429) -> Chờ 10 giây rồi thử lại
                print("Sleeping 10s...")
                time.sleep(10)
            else:
                # Nếu lỗi khác (sai code, sai key) -> Dừng luôn
                break
                
    print("❌ Đã thử hết số lần nhưng vẫn thất bại.")
    return None

def save_to_db(content, original_prompt):
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
        # Lưu bản ghi mới, note rõ dùng model 2.5-pro
        cur.execute(sql, (content, original_prompt, "gemini-2.5-pro", "done"))
        
        conn.commit()
        cur.close()
        print("✅ THÀNH CÔNG: Đã cập nhật tín hiệu từ Gemini 2.5 Pro!")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Lỗi khi lưu DB: {e}")
    finally:
        if conn:
            conn.close()

def main():
    prompt_content = read_prompt_file()
    if not prompt_content:
        return
    
    print(prompt_content)

    ai_result = generate_market_signal(prompt_content)
    
    if ai_result:
        save_to_db(ai_result, prompt_content)
    else:
        print("⚠️ Không nhận được kết quả từ AI.")

if __name__ == "__main__":
    main()