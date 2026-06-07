import os
import json
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-2.5-pro" # or gemini-2.0-flash

    def generate_json(self, prompt: str) -> dict:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {}

def extract_signals(news_content: str) -> dict:
    prompt = f"""
    You are a Quant Researcher and Macro-Economic Analyst.
    Analyze the following news text and extract key macroeconomic signals.
    Categories: [Policy, Liquidity, Inflation, Growth, Market Sentiment]

    News Text: {news_content}

    Respond in JSON format with a list of signals. Example:
    {{
        "signals": [
            {{
                "category": "Policy",
                "signal": "Hawkish",
                "confidence": 0.85,
                "reason": "The Fed chair explicitly mentioned higher for longer rates."
            }}
        ]
    }}
    """
    client = GeminiClient()
    return client.generate_json(prompt)

def generate_thesis(news_content: str) -> dict:
    prompt = f"""
    Bạn là chuyên gia phân tích vĩ mô và tài chính (Quant Researcher).
    Dựa vào các tin tức sau đây:
    {news_content}
    
    Hãy tổng hợp và đưa ra Nhận định Vĩ mô hiện tại và Hành động bảo vệ/gia tăng tài sản.
    Trả về định dạng JSON:
    {{
        "theses": [
            {{
                "thesis": "Tóm tắt ngắn gọn nhận định vĩ mô cốt lõi (khoảng 2-3 câu).",
                "confidence": 0.85,
                "supporting_evidence": "Hành động cụ thể: Gợi ý phân bổ danh mục (Crypto, Vàng, USD, Cổ phiếu) để bảo vệ và gia tăng tài sản."
            }}
        ]
    }}
    Lưu ý: "confidence" là số thập phân từ 0.0 đến 1.0. "supporting_evidence" sẽ được dùng làm các bước chuẩn bị tài sản.
    """
    client = GeminiClient()
    return client.generate_json(prompt)

def propose_world_state_changes(current_state: str, signals: str, theses: str) -> dict:
    prompt = f"""
    Bạn là AI Quản lý World State cho một nền tảng Macro Intelligence.
    Nhiệm vụ của bạn là xem xét Trạng thái Thế giới hiện tại (World State), các Tín hiệu (Signals) mới nhất và Nhận định (Theses) hiện tại, sau đó đề xuất các thay đổi (nếu cần) đối với World State.
    
    YÊU CẦU QUAN TRỌNG VỀ NGÔN NGỮ:
    - Tất cả các trường nội dung mô tả bao gồm "new_value" và "reason" trong kết quả đề xuất BẮT BUỘC phải viết bằng Tiếng Việt.
    - Không sử dụng các thuật ngữ tiếng Anh gốc như "Hawkish", "Dovish", "Neutral", "Tightening", "Easing" trực tiếp mà hãy dịch/mô tả bằng Tiếng Việt. Ví dụ:
      + Thay vì "Hawkish" hay "Tightening", hãy ghi "Thắt chặt (Diều hâu)" hoặc "Tăng lãi suất".
      + Thay vì "Dovish" hay "Easing", hãy ghi "Nới lỏng (Bồ câu)" hoặc "Giảm lãi suất".
      + Thay vì "Neutral", hãy ghi "Trung lập".
      + Đối với biến động của OPEC/OPEC+, hãy ghi rõ hành động như "Cắt giảm sản lượng", "Tăng sản lượng", hoặc "Giữ nguyên sản lượng".
      + Đối với Ngân hàng Nhà nước Việt Nam (SBV) và kinh tế Việt Nam (VN_Economy), dùng các cụm từ tiếng Việt chính xác như "Hạ lãi suất điều hành", "Tăng lãi suất điều hành", "Bơm/Hút thanh khoản", "Tăng trưởng nóng", v.v.

    Current World State (JSON):
    {current_state}
    
    Recent Signals:
    {signals}
    
    Active Theses:
    {theses}
    
    Hãy đề xuất thay đổi dưới định dạng JSON:
    {{
        "proposed_changes": [
            {{
                "target_entity": "FED", 
                "field_name": "interest_rate_trend",
                "new_value": "Thắt chặt (Diều hâu)",
                "confidence": 0.9,
                "reason": "Chủ tịch FED phát biểu cứng rắn về việc duy trì lãi suất cao hơn để chống lạm phát."
            }}
        ]
    }}
    "target_entity" có thể là: FED, ECB, BOJ, RBA, BOC, OPEC, OPEC+, SBV, VN_Economy, US_Economy, Global_Liquidity, Crypto_Market, BRICS_Economy, NDB_Bank, v.v.
    "field_name" có thể là: trend, status, risk_level, production_policy, liquidity_status, v.v.
    Nếu không có gì cần thay đổi, trả về danh sách rỗng.
    """
    client = GeminiClient()
    return client.generate_json(prompt)
