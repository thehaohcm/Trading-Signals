import os
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# API CONFIGURATION
# ==========================================

# 9Router API (Default/Primary)
ROUTER_API_ENDPOINT = os.getenv("ROUTER_API_ENDPOINT")
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY")
ROUTER_COMBO_NAME = os.getenv("ROUTER_COMBO_NAME")

# Gemini API (Fallback)
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

class RwaTokenSuggestion(BaseModel):
    category: str = Field(description="Phân khúc tài sản/RWA: Trái phiếu Mỹ (Treasuries), Vàng (Physical Gold & Gold RWA), Tín dụng tư nhân...")
    assets_or_tokens: List[str] = Field(description="Danh sách các mã token hoặc tên tài sản cụ thể. Ví dụ: ['ONDO', 'USDY'] hoặc ['Vàng vật chất', 'PAXG', 'XAUT']")
    reason: str = Field(description="Lý do ngắn gọn tại sao chọn phân khúc này trong bối cảnh hiện tại.")

class AssetAllocation(BaseModel):
    increase_weight: List[str] = Field(description="Các loại tài sản cần TĂNG tỷ trọng. Ví dụ: ['USD/Tiền mặt', 'Vàng']")
    decrease_weight: List[str] = Field(description="Các loại tài sản cần GIẢM tỷ trọng. Ví dụ: ['Cổ phiếu', 'Crypto đầu cơ']")
    rwa_strategy_details: List[RwaTokenSuggestion] = Field(description="Chi tiết các mã token RWA cụ thể được chọn lọc.")

class ThesisItem(BaseModel):
    thesis: str = Field(description="Tóm tắt ngắn gọn nhận định vĩ mô cốt lõi dựa trên TÍN HIỆU ĐÃ LỌC (2-3 câu).")
    confidence: float = Field(ge=0.0, le=1.0)
    allocation_plan: AssetAllocation = Field(description="Kế hoạch phân bổ danh mục được định dạng cấu trúc để hiển thị giao diện.")

class ThesisOutput(BaseModel):
    theses: List[ThesisItem]

class ProposedChangeItem(BaseModel):
    target_entity: str = Field(description="FED, ECB, BOE, BOJ, RBA, RBNZ, BoC, OPEC, OPEC+, SBV, VN_Economy, US_Economy, Global_Liquidity, Crypto_Market, v.v.")
    field_name: str = Field(description="trend, status, risk_level, production_policy, liquidity_status, v.v.")
    new_value: str = Field(description="BẮT BUỘC viết bằng Tiếng Việt. Dịch nghĩa hoàn toàn các từ như Thắt chặt (Diều hâu), Nới lỏng (Bồ câu), Trung lập, Tăng/Giảm sản lượng... Đưa ra thời gian dự kiến gần nhất các ngân hàng trung ương họp.")
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(description="Lý do đề xuất thay đổi dựa trên tin tức vĩ mô mới, viết bằng Tiếng Việt.")

class WorldStateChangesOutput(BaseModel):
    proposed_changes: List[ProposedChangeItem]


# ==========================================
# LLM CLIENT (SINGLETON PATTERN)
# Primary: 9Router API | Fallback: Gemini API
# ==========================================

class LLMClient:
    def __init__(self):
        # 9Router OpenAI-compatible client (Primary)
        self.router_client = OpenAI(
            base_url=ROUTER_API_ENDPOINT,
            api_key=ROUTER_API_KEY,
        )
        self.router_combo = ROUTER_COMBO_NAME

        # Gemini client (Fallback)
        self.gemini_enabled = bool(GEMINI_API_KEY)
        if self.gemini_enabled:
            self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            self.gemini_model = "gemma-4-26b-a4b-it"
        else:
            logger.warning("GEMINI_API_KEY is not set. Gemini fallback is disabled.")

    def _try_router(self, prompt: str, response_schema) -> dict:
        """Gọi 9Router API (OpenAI-compatible) với response_format json_object
        và nhúng JSON schema vào prompt (vì DeepSeek backend không hỗ trợ json_schema strict mode)."""
        schema_name = response_schema.__name__
        json_schema = response_schema.model_json_schema()

        # Nhúng schema vào prompt để model biết định dạng output mong đợi
        schema_prompt = f"""
{prompt}

---

**IMPORTANT: You MUST respond with a valid JSON object matching this exact JSON schema.**
Do NOT include any text outside the JSON object (no markdown code blocks, no explanations).

JSON Schema:
```json
{json.dumps(json_schema, ensure_ascii=False)}
```

Respond ONLY with the JSON object that conforms to the schema above.
"""

        logger.info(f"Calling 9Router API with combo={self.router_combo}, schema={schema_name}")
        response = self.router_client.chat.completions.create(
            model=self.router_combo,
            messages=[
                {"role": "user", "content": schema_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _try_gemini(self, prompt: str, response_schema) -> dict:
        """Gọi Gemini API (Fallback)."""
        if not self.gemini_enabled:
            raise RuntimeError("Gemini API is not configured")

        logger.info(f"Falling back to Gemini API with model={self.gemini_model}")
        response = self.gemini_client.models.generate_content(
            model=self.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1,
            ),
        )
        return json.loads(response.text)

    def generate_structured_data(self, prompt: str, response_schema) -> dict:
        """Generate structured data: try 9Router first, fallback to Gemini on error."""
        # Try primary: 9Router API
        try:
            return self._try_router(prompt, response_schema)
        except Exception as e:
            logger.warning(f"9Router API failed: {e}. Trying Gemini fallback...")

        # Try fallback: Gemini API
        try:
            return self._try_gemini(prompt, response_schema)
        except Exception as e:
            logger.error(f"Gemini fallback also failed: {e}")
            return {}

# Khởi tạo một client dùng chung cho toàn bộ app
global_gemini_client = LLMClient()


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
    
    Nhiệm vụ của bạn là đưa ra nhận định vĩ mô và lập kế hoạch phân bổ danh mục chi tiết theo định dạng cấu trúc.

    YÊU CẦU ĐẶC BIỆT VỀ CHIẾN LƯỢC TÀI SẢN PHÒNG THỦ & RWA:
    Hãy phân tích bối cảnh và chỉ định chính xác các mã tài sản/token vào trường 'rwa_strategy_details' nếu có phân bổ:

    1. Nếu LÃI SUẤT FED CAO KÉO DÀI (Hawkish / Higher-for-longer) HOẶC THANH KHOẢN THẮT CHẶT:
       - Phân khúc: 'Trái phiếu Mỹ (Treasuries), Tiền mặt (Cash), Lãi suất ngân hàng Việt Nam'
       - Gợi ý chính xác: ['ONDO', 'USDY']
       - Lý do: Khai thác lợi suất phi rủi ro 4.5% - 5% từ tín phiếu kho bạc Mỹ ngay trên chuỗi.

    2. Nếu ĐỊA CHÍNH TRỊ LEO THANG (Chiến sự Mỹ-Iran, nghẽn mạch eo biển):
       - Phân khúc: 'Vàng (Physical Gold & Gold RWA)'
       - Gợi ý chính xác bao gồm cả tài sản vật chất và on-chain: ['Vàng vật chất', 'PAXG', 'XAUT']
       - Lý do: Kết hợp giữa việc nắm giữ vàng vật chất ngoài đời thực làm tài sản trú ẩn tối hậu (Sound Money) và các token vàng trên chuỗi để tối ưu hóa tính thanh khoản và khả năng giao dịch linh hoạt 24/7.

    3. Nếu VĨ MÔ ỔN ĐỊNH, LÃI SUẤT HẠ NHIỆT (Dovish / Easing):
       - Phân khúc: 'Tín dụng tư nhân (Private Credit)'
       - Gợi ý chính xác các token: ['CFG', 'MPL']
       - Lý do: Tìm kiếm lợi nhuận (yield) cao hơn từ dòng vốn tăng trưởng doanh nghiệp.

    YÊU CẦU ĐỊNH DẠNG:
    - Điền chính xác các nhóm tài sản cần tăng/giảm vào 'increase_weight' và 'decrease_weight'.
    - Toàn bộ phần mô tả lý do (reason, thesis) BẮT BUỘC viết bằng Tiếng Việt.
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