# highest_bank_interest_rate.py
# Lấy lãi suất tiết kiệm NGÂN HÀNG CAO NHẤT từ cake.vn (02/2026)
# Lưu kết quả vào DB theo cấu hình file .env

import asyncio
import asyncpg
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import re
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load biến môi trường từ file .env (cùng thư mục scripts/)
load_dotenv()


def get_highest_savings_rate() -> Optional[Tuple[str, float, str, str]]:
    url = "https://cake.vn/tin-tuc/tai-chinh/lai-suat-gui-tiet-kiem-ngan-hang-nao-cao-nhat"

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504, 520])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    }

    try:
        resp = session.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
    except Exception as e:
        print(f"Lỗi tải trang: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        print("Không tìm thấy bảng nào.")
        return None

    max_rate = -1.0
    best = {"bank": "", "rate": 0.0, "term": "", "channel": "không rõ"}

    for table in tables:
        # Lấy heading trước bảng một cách an toàn
        heading = table.find_previous(["h2", "h3", "h4", "p", "strong"])
        heading_text = ""
        if heading:
            heading_text = heading.get_text(strip=True).lower()

        # Xác định channel
        if any(word in heading_text for word in ["online", "trực tuyến", "digital"]):
            channel = "online"
        elif any(word in heading_text for word in ["quầy", "tại quầy", "counter"]):
            channel = "tại quầy"
        else:
            channel = "không rõ (có thể online)"

        # Lấy header row (thường row 0 là kỳ hạn)
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        col_headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]

        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            bank = cols[0].get_text(strip=True).replace("\n", " ").strip()
            if not bank:
                continue

            for idx, col in enumerate(cols[1:], start=1):
                text = col.get_text(strip=True)
                if not text:
                    continue

                # Tìm số lãi suất (hỗ trợ **7.30**, 7,3, 7.30%, v.v.)
                match = re.search(r"(\d+[.,]?\d*)", text)
                if match:
                    try:
                        rate_str = match.group(1).replace(",", ".")
                        rate = float(rate_str)

                        term = col_headers[idx] if idx < len(col_headers) else "không rõ"

                        # Update nếu cao hơn, hoặc bằng nhưng ưu tiên online
                        update = False
                        if rate > max_rate:
                            update = True
                        elif rate == max_rate and "online" in channel and "online" not in best["channel"]:
                            update = True

                        if update:
                            max_rate = rate
                            best = {
                                "bank": bank,
                                "rate": rate,
                                "term": term,
                                "channel": channel
                            }

                    except ValueError:
                        pass

    if max_rate > 0:
        return best["bank"], best["rate"], best["term"], best["channel"]
    else:
        print("Không tìm thấy lãi suất hợp lệ.")
        return None


async def save_to_db(bank: str, rate: float, term: str, channel: str) -> None:
    """Lưu kết quả vào bảng highest_bank_interest_rate theo cấu hình .env"""
    db_port_str = os.environ.get("DB_PORT", "5432")

    conn = await asyncpg.connect(
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        host=os.environ.get("DB_HOST"),
        port=int(db_port_str),
    )

    try:
        # Đảm bảo bảng tồn tại
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.highest_bank_interest_rate (
                id SERIAL PRIMARY KEY,
                bank VARCHAR(100) NOT NULL,
                rate NUMERIC(5, 2) NOT NULL,
                term VARCHAR(50),
                channel VARCHAR(50),
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """)

        # Xoá record cũ (chỉ giữ 1 record mới nhất)
        await conn.execute("DELETE FROM public.highest_bank_interest_rate")
        await conn.execute(
            """
            INSERT INTO public.highest_bank_interest_rate (bank, rate, term, channel)
            VALUES ($1, $2, $3, $4)
            """,
            bank, rate, term, channel,
        )
        print(f"✅ Đã lưu vào DB: bank={bank}, rate={rate}, term={term}, channel={channel}")
    except asyncpg.PostgresError as e:
        print(f"❌ Lỗi DB khi lưu dữ liệu: {e}")
        raise
    finally:
        await conn.close()


async def main():
    result = get_highest_savings_rate()

    if result:
        bank, rate, term, channel = result
        print("\n" + "="*60)
        print("LÃI SUẤT TIẾT KIỆM CAO NHẤT HIỆN NAY (cake.vn)")
        print("="*60)
        print(f"Ngân hàng : {bank}")
        print(f"Lãi suất  : {rate}% / năm")
        print(f"Kỳ hạn    : {term}")
        print(f"Kênh      : {channel}")
        print(f"Nguồn     : https://cake.vn/tin-tuc/tai-chinh/lai-suat-gui-tiet-kiem-ngan-hang-nao-cao-nhat")
        print("="*60)
        print("→ Đây là mức cao nhất trong bảng online (thường cao hơn tại quầy).")
        print("→ Kiểm tra trực tiếp app Cake hoặc website để xác nhận điều kiện mới nhất.")

        # Lưu vào database
        await save_to_db(bank, rate, term, channel)
    else:
        print("Không lấy được dữ liệu. Có thể trang thay đổi cấu trúc hoặc lỗi mạng.")


if __name__ == "__main__":
    asyncio.run(main())
