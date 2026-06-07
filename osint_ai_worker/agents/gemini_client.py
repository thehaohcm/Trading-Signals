import os
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ==========================================
# CẤU TRÚC ĐẦU RA (PYDANTIC SCHEMAS)
# ==========================================

class SignalItem(BaseModel):
    category: str = Field(description="Categories: Policy, Liquidity, Inflation, Growth, Market Sentiment")
    signal: str = Field(description="Xu hướng tín hiệu rõ ràng (ví dụ: Hawkish, Dovish, Tightening, Easing...)")
    confidence: float = Field(ge=0.0, le=1.0, description="Độ tin cậy từ 0.0 đến 1.0")
    reason: str = Field(description="Lý do trích xuất tín hiệu từ văn bản")

class SignalOutput(BaseModel):
    signals: List[SignalItem]

class ThesisItem(BaseModel):
    thesis: str = Field(description="Tóm tắt ngắn gọn nhận định vĩ mô cốt lõi dựa trên TÍN HIỆU ĐÃ LỌC (2-3 câu).")
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: str = Field(description="Hành động cụ thể: Gợi ý phân bổ danh mục (Crypto, Vàng, USD, Cổ phiếu) dựa trên xác suất hệ thống.")

    rwa_strategy: Optional[str] = Field(
        None, 
        description="Nếu gợi ý Crypto có RWA, phải làm rõ: Chọn phân khúc nào (Trái phiếu Chính phủ - Treasuries, Vàng token hóa - Gold RWA, hay Tín dụng - Private Credit), mã token gợi ý (ví dụ: ONDO, USDY, PAXG...) và lý do vĩ mô tại sao phân khúc đó hưởng lợi."
    )
class ThesisOutput(BaseModel):
    theses: List[ThesisItem]

class ProposedChangeItem(BaseModel):
    target_entity: str = Field(description="FED, ECB, BOJ, OPEC, OPEC+, SBV, VN_Economy, US_Economy, Global_Liquidity, Crypto_Market, v.v.")
    field_name: str = Field(description="trend, status, risk_level, production_policy, liquidity_status, v.v.")
    new_value: str = Field(description="BẮT BUỘC viết bằng Tiếng Việt. Dịch nghĩa hoàn toàn các từ như Thắt chặt (Diều hâu), Nới lỏng (Bồ câu), Trung lập, Tăng/Giảm sản lượng...")
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(description="Lý do đề xuất thay đổi dựa trên tin tức vĩ mô mới, viết bằng Tiếng Việt.")

class WorldStateChangesOutput(BaseModel):
    proposed_changes: List[ProposedChangeItem]


# ==========================================
# GEMINI CLIENT (SINGLETON PATTERN)
# ==========================================

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-2.5-pro" # Khuyến khích dùng bản pro cho việc lập luận chuỗi (Reasoning) vĩ mô

    def generate_structured_data(self, prompt: str, response_schema) -> dict:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1, # Hạ thấp temperature để AI bớt "sáng tạo" lung tung, tập trung vào tính logic/xác suất
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {}

# Khởi tạo một client dùng chung cho toàn bộ app
global_gemini_client = GeminiClient()


# ==========================================
# CORE CORE FUNCTIONS
# ==========================================

def extract_signals(news_content: str) -> dict:
    """Bước 1: Trích xuất dữ liệu cứng/tín hiệu thô từ tin tức văn bản"""
    prompt = f"""
    You are a Quant Researcher and Macro-Economic Analyst.
    Analyze the following news text and extract key macroeconomic signals.
    Focus strictly on hard data, statements, and actual event outcomes.

    News Text: {news_content}
    """
    return global_gemini_client.generate_structured_data(prompt, SignalOutput)


def generate_thesis(extracted_signals: dict) -> dict:
    prompt = f"""
    Bạn là một nhà quản lý quỹ định lượng (Quant Fund Manager) và chuyên gia phân tích chu kỳ dòng tiền tài chính vĩ mô.
    Dựa trên danh sách các TÍN HIỆU CỨNG đã được trích xuất dưới đây:
    
    Extracted Signals (JSON):
    {json.dumps(extracted_signals, ensure_ascii=False)}
    
    Nhiệm vụ của bạn là đưa ra nhận định vĩ mô và hành động phân bổ danh mục. 
    ĐẶC BIỆT, nếu môi trường vĩ mô có biến động, bạn phải làm rõ chiến lược RWA (Real-World Assets - Tài sản thực được token hóa trên chuỗi) theo tư duy sau:

    1. NẾU LÃI SUẤT FED CAO KÉO DÀI (Hawkish / Higher-for-longer) HOẶC THANH KHOẢN THẮT CHẶT:
       - Ưu tiên nhóm RWA Trái phiếu Chính phủ Mỹ ngắn hạn (Treasuries RWA như USDY, ONDO, BUIDL).
       - Giải thích rõ: Lãi suất cao ở thế giới thực mang lại lợi suất phi rủi ro (4.5% - 5%) cực an toàn cho dòng tiền trú ẩn trong Crypto mà không cần out ra Fiat.

    2. NẾU ĐỊA CHÍNH TRỊ LEO THANG (Chiến sự, căng thẳng Mỹ-Iran, đóng cửa eo biển):
       - Ưu tiên nhóm RWA Hàng hóa, đặc biệt là Vàng token hóa (Gold RWA như PAXG, XAUT).
       - Giải thích rõ: Đây là hầm trú ẩn chống lạm phát tiền tệ, vừa có tính bảo chứng của vàng vật chất, vừa có tính thanh khoản tự do 24/7 của Blockchain.

    3. NẾU VĨ MÔ ỔN ĐỊNH, LÃI SUẤT HẠ NHIỆT (Dovish / Easing):
       - Có thể cân nhắc dịch chuyển sang RWA Tín dụng tư nhân (Private Credit như Centrifuge, Maple) để tìm kiếm lợi nhuận (yield) cao hơn từ tăng trưởng doanh nghiệp.

    YÊU CẦU ĐẦU RA:
    - Điền đầy đủ thông tin vào trường "rwa_strategy" nếu có phân bổ vào Crypto. Nói rõ MUA CÁI GÌ, TẠI SAO MUA dựa trên logic trên. Ngôn ngữ hoàn toàn bằng Tiếng Việt.
    """
    return global_gemini_client.generate_structured_data(prompt, ThesisOutput)


def propose_world_state_changes(current_state: dict, signals: dict, theses: dict) -> dict:
    """Bước 3: Đề xuất cập nhật trạng thái hệ thống bằng Tiếng Việt"""
    prompt = f"""
    Bạn là AI Quản lý World State cho một nền tảng Macro Intelligence.
    Nhiệm vụ của bạn là so sánh Trạng thái Thế giới hiện tại (Current World State) với các Tín hiệu (Signals) và Nhận định (Theses) mới nhận được, từ đó đề xuất cập nhật.
    
    YÊU CẦU NGÔN NGỮ & ĐỊNH DANH (MỘT CÁCH TUYỆT ĐỐI):
    - Các trường "new_value" và "reason" BẮT BUỘC phải viết bằng Tiếng Việt.
    - Dịch hoàn toàn các thuật ngữ kinh tế sang tiếng Việt tương đương:
      + "Hawkish" / "Tightening" -> "Thắt chặt (Diều hâu)" hoặc "Tăng lãi suất".
      + "Dovish" / "Easing" -> "Nới lỏng (Bồ câu)" hoặc "Giảm lãi suất".
      + "Neutral" -> "Trung lập".
      + Biến động cung ứng: "Cắt giảm sản lượng", "Tăng sản lượng", "Giữ nguyên sản lượng".
      + Ngân hàng Nhà nước VN (SBV): "Hạ lãi suất điều hành", "Bơm/Hút thanh khoản"...

    Current World State (JSON):
    {json.dumps(current_state, ensure_ascii=False)}
    
    Recent Signals (JSON):
    {json.dumps(signals, ensure_ascii=False)}
    
    Active Theses (JSON):
    {json.dumps(theses, ensure_ascii=False)}
    
    Nếu dữ liệu mới trùng khớp hoàn toàn với Current World State hoặc không đủ trọng số để thay đổi, trả về danh sách proposed_changes rỗng [].
    """
    return global_gemini_client.generate_structured_data(prompt, WorldStateChangesOutput)