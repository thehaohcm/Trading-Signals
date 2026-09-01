import os
import json
import logging
from typing import List, Optional, Dict
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
ROUTER_API_ENDPOINT = os.getenv("ROUTER_API_ENDPOINT") or os.getenv("NINE_ROUTER_ENDPOINT")
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY") or os.getenv("NINE_ROUTER_API_KEY")
ROUTER_COMBO_NAME = os.getenv("ROUTER_COMBO_NAME") or os.getenv("NINE_ROUTER_MODEL")

# Gemini API (Fallback)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ==========================================
# CẤU TRÚC ĐẦU RA (PYDANTIC SCHEMAS)
# ==========================================

class SignalItem(BaseModel):
    category: str = Field(description="Categories: Policy, Liquidity, Inflation, Growth, Market Sentiment")
    signal: str = Field(description="Xu hướng tín hiệu rõ ràng viết bằng Tiếng Việt (ví dụ: Thắt chặt, Nới lỏng, Tăng lãi suất, Cắt giảm sản lượng...)")
    confidence: float = Field(ge=0.0, le=1.0, description="Độ tin cậy từ 0.0 đến 1.0")
    reason: str = Field(description="Lý do trích xuất tín hiệu từ văn bản viết bằng Tiếng Việt")

class SignalOutput(BaseModel):
    signals: List[SignalItem] = Field(default_factory=list)

class RwaTokenSuggestion(BaseModel):
    category: str = Field(description="Phân khúc tài sản/RWA: Trái phiếu Mỹ (Treasuries), Vàng (Physical Gold & Gold RWA), Tín dụng tư nhân, Bất động sản VN...")
    assets_or_tokens: List[str] = Field(default_factory=list, description="Danh sách các mã token hoặc tên tài sản cụ thể. Ví dụ: ['ONDO', 'USDY'] hoặc ['Vàng vật chất', 'PAXG', 'XAUT']")
    reason: str = Field(description="Lý do ngắn gọn tại sao chọn phân khúc này trong bối cảnh hiện tại.")

class CashAllocation(BaseModel):
    currency_distribution: Optional[Dict[str, float]] = Field(default_factory=dict, description="Phân bổ tỷ lệ tiền mặt theo đồng tiền. Key: 'VND', 'USD', 'USDT', 'USDC'... Value: tỷ lệ từ 0.0 đến 1.0, tổng = 1.0")
    vn_bank_interest_rate: Optional[str] = Field(default="", description="Lãi suất ngân hàng VN hiện tại cho kỳ hạn phổ biến. Ví dụ: '5.0-5.5%/năm kỳ hạn 6 tháng tại Vietcombank/BIDV/VietinBank'")
    stablecoin_platform_yields: Optional[List[str]] = Field(default_factory=list, description="Danh sách lợi suất USD stable coin trên các nền tảng.")
    recommendation: Optional[str] = Field(default="", description="Khuyến nghị chi tiết bằng Tiếng Việt: nên giữ VND hay USD/USDT, tỉ lệ bao nhiêu, gửi NH VN hay stake stablecoin trên sàn...")

class RealEstateRecommendation(BaseModel):
    property_type: str = Field(description="Loại hình BĐS: 'Chung cư', 'Nhà phố', 'Đất nền', 'Biệt thự', 'Shophouse', 'BĐS công nghiệp', 'BĐS nghỉ dưỡng', 'Nhà ở xã hội', 'Đất nông nghiệp'...")
    area: str = Field(description="Khu vực/quận/huyện cụ thể. Ví dụ: 'Quận 2 (TP.Thủ Đức)', 'Huyện Bình Chánh', 'Quận Long Biên', 'TP. Dĩ An - Bình Dương'")
    project: Optional[str] = Field(default="", description="Tên dự án cụ thể (nếu có) hoặc mô tả khu vực.")
    price_range: Optional[str] = Field(default="", description="Khoảng giá tham khảo.")
    reason: str = Field(description="Lý do chọn khu vực/dự án này trong bối cảnh hiện tại.")

class RealEstateVN(BaseModel):
    market_outlook: Optional[str] = Field(default="", description="Tổng quan thị trường bất động sản Việt Nam hiện tại. Viết bằng Tiếng Việt.")
    attractive_segments: Optional[List[str]] = Field(default_factory=list, description="Các phân khúc BĐS VN hấp dẫn trong bối cảnh hiện tại.")
    recommended_properties: Optional[List[RealEstateRecommendation]] = Field(default_factory=list, description="Danh sách chi tiết các loại hình BĐS, khu vực, dự án cụ thể NÊN đầu tư.")
    risks: Optional[List[str]] = Field(default_factory=list, description="Rủi ro khi đầu tư BĐS VN hiện tại.")
    recommendation: Optional[str] = Field(default="", description="Khuyến nghị hành động: NÊN hay KHÔNG NÊN đầu tư BĐS VN lúc này. Viết bằng Tiếng Việt.")

class AssetAllocation(BaseModel):
    increase_weight: Optional[List[str]] = Field(default_factory=list, description="Các loại tài sản cần TĂNG tỷ trọng. Ví dụ: ['USD/Tiền mặt', 'Vàng', 'Bất động sản VN', 'Cổ phiếu VN']")
    decrease_weight: Optional[List[str]] = Field(default_factory=list, description="Các loại tài sản cần GIẢM tỷ trọng. Ví dụ: ['Cổ phiếu', 'Crypto đầu cơ', 'Bất động sản VN']")
    rwa_strategy_details: Optional[List[RwaTokenSuggestion]] = Field(default_factory=list, description="Chi tiết các mã token RWA cụ thể được chọn lọc. Nếu bỏ qua, trả về [].")
    cash_allocation: Optional[CashAllocation] = Field(default=None, description="Phân tích chi tiết phân bổ tiền mặt. Nếu bỏ qua, trả về null.")
    real_estate_vn: Optional[RealEstateVN] = Field(default=None, description="Phân tích chuyên sâu về bất động sản Việt Nam. Nếu bỏ qua, trả về null.")
    recommended_forex_pairs: Optional[List[str]] = Field(default_factory=list, description="Khuyến nghị giao dịch các cặp tiền Forex theo xu hướng vĩ mô. Nếu bỏ qua, trả về [].")

class ThesisItem(BaseModel):
    thesis: str = Field(description="Tóm tắt ngắn gọn nhận định vĩ mô cốt lõi dựa trên TÍN HIỆU ĐÃ LỌC (2-3 câu).")
    confidence: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Độ tin cậy của nhận định (từ 0.0 đến 1.0). Đánh giá dựa trên độ đầy đủ của dữ liệu: 0.80 - 0.95 khi các tín hiệu chính sách, cảnh báo dòng tiền và lãi suất đều có sự đồng thuận cao; 0.65 - 0.79 khi xu hướng rõ ràng; dưới 0.60 chỉ khi dữ liệu quá ít hoặc mâu thuẫn."
    )
    allocation_plan: AssetAllocation = Field(description="Kế hoạch phân bổ danh mục được định dạng cấu trúc để hiển thị giao diện.")

class ThesisOutput(BaseModel):
    theses: List[ThesisItem] = Field(default_factory=list)

class ProposedChangeItem(BaseModel):
    target_entity: str = Field(description="FED, ECB, BOE, BOJ, RBA, RBNZ, BoC, OPEC, OPEC+, SBV, VN_Economy, US_Economy, Global_Liquidity, Crypto_Market, Oil (Crude, WTI, Brent) v.v.")
    field_name: str = Field(description="trend, status, risk_level, production_policy, liquidity_status, v.v.")
    new_value: str = Field(description="BẮT BUỘC viết bằng Tiếng Việt. Dịch nghĩa hoàn toàn các từ như Thắt chặt (Diều hâu), Nới lỏng (Bồ câu), Trung lập, Tăng/Giảm sản lượng... Đưa ra thời gian dự kiến gần nhất các ngân hàng trung ương họp.")
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(description="Lý do đề xuất thay đổi dựa trên tin tức vĩ mô mới, viết bằng Tiếng Việt.")

class WorldStateChangesOutput(BaseModel):
    proposed_changes: List[ProposedChangeItem] = Field(default_factory=list)


# ==========================================
# LLM CLIENT (SINGLETON PATTERN)
# Primary: 9Router API | Fallback: Gemini API
# ==========================================

class LLMClient:
    def __init__(self):
        # 9Router OpenAI-compatible client (Primary)
        self.router_enabled = bool(ROUTER_API_KEY)
        if self.router_enabled:
            self.router_client = OpenAI(
                base_url=ROUTER_API_ENDPOINT,
                api_key=ROUTER_API_KEY,
            )
            self.router_combo = ROUTER_COMBO_NAME
        else:
            self.router_client = None
            self.router_combo = None
            logger.warning("ROUTER_API_KEY is not set. 9Router is disabled.")

        # Gemini client (Fallback)
        self.gemini_enabled = bool(GEMINI_API_KEY)
        if self.gemini_enabled:
            self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            self.gemini_models = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.5-pro"]
        else:
            logger.warning("GEMINI_API_KEY is not set. Gemini fallback is disabled.")

    def _try_router(self, prompt: str, response_schema) -> dict:
        """Thử gọi 9Router qua OpenAI SDK (chuẩn tương thích OpenAI)
        và nhúng JSON schema vào prompt (vì DeepSeek backend không hỗ trợ json_schema strict mode)."""
        if not self.router_enabled or not self.router_client:
            raise RuntimeError("9Router is not configured")

        # Lấy JSON schema từ Pydantic model
        schema_json = json.dumps(response_schema.model_json_schema(), ensure_ascii=False, indent=2)
        
        # Nhúng schema vào prompt để model biết định dạng output mong đợi
        schema_prompt = f"""{prompt}

CRITICAL FORMAT REQUIREMENT:
You MUST respond with ONLY a valid, raw JSON object conforming strictly to this JSON Schema.
Do NOT include markdown formatting, backticks (```json), or any text outside the JSON object.

JSON Schema:
{schema_json}"""

        messages = [
            {
                "role": "system",
                "content": "You are a quantitative macro analyst and structured data extraction engine. Always output pure, valid raw JSON only. Never use markdown codeblocks.",
            },
            {
                "role": "user", 
                "content": schema_prompt
            }
        ]

        logger.info(f"[LLM] Trying 9Router ({self.router_combo})...")
        response = self.router_client.chat.completions.create(
            model=self.router_combo,
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return self._clean_and_parse_json(content)

    def _try_gemini(self, prompt: str, response_schema) -> dict:
        """Fallback: Gọi Google Gemini (2.5 Flash / 1.5 Flash) với native structured outputs."""
        if not self.gemini_enabled or not self.gemini_client:
            raise RuntimeError("Gemini is not configured")

        last_err = None
        for model_name in self.gemini_models:
            try:
                logger.info(f"[LLM] Fallback to Gemini ({model_name})...")
                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0.2,
                    ),
                )
                return self._clean_and_parse_json(response.text)
            except Exception as ge:
                logger.warning(f"[LLM] Gemini {model_name} failed: {ge}")
                last_err = ge
        raise last_err or RuntimeError("All Gemini fallback models failed")

    def generate_structured_data(self, prompt: str, response_schema) -> dict:
        """
        Tạo dữ liệu có cấu trúc với cơ chế Fallback:
        1. Ưu tiên gọi 9Router (DeepSeek V3 / R1)
        2. Nếu lỗi hoặc timeout -> tự động fallback sang Gemini 2.0 Flash
        """
        if self.router_enabled:
            try:
                return self._try_router(prompt, response_schema)
            except Exception as e:
                logger.warning(f"[LLM] 9Router call failed: {e}. Switching to Gemini fallback...")

        if self.gemini_enabled:
            return self._try_gemini(prompt, response_schema)

        raise RuntimeError("No LLM backend available (both 9Router and Gemini failed or unconfigured)")

    def _clean_and_parse_json(self, raw_text: str) -> dict:
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())


global_gemini_client = LLMClient()


# ==========================================
# PROMPTS & CORE FUNCTIONS
# ==========================================

DEFAULT_SIGNAL_EXTRACTION_PROMPT = """Bạn là chuyên gia nghiên cứu định lượng (Quant Researcher) và phân tích kinh tế vĩ mô.
Nhiệm vụ: Phân tích nội dung tin tức được cung cấp và trích xuất các tín hiệu kinh tế vĩ mô có giá trị.

YÊU CẦU QUAN TRỌNG:
1. Tập trung tuyệt đối vào dữ liệu thực tế (Hard Data), phát biểu chính sách chính thức hoặc sự kiện kinh tế đã diễn ra.
2. Trường 'reason' và 'signal' BẮT BUỘC viết bằng Tiếng Việt súc tích.
3. Phân loại trường 'category' CHỈ ĐƯỢC CHỌN trong các nhóm sau:
   - Policy (Chính sách tiền tệ, lãi suất, điều hành ngân hàng trung ương)
   - Liquidity (Thanh khoản, cung tiền M2, dòng vốn)
   - Inflation (Lạm phát, CPI, PPI, giá cả hàng hóa)
   - Growth (Tăng trưởng GDP, việc làm, sản xuất PMI, xuất nhập khẩu)
   - Market Sentiment (Tâm lý rủi ro Risk-On / Risk-Off)
4. LỌC TIN RÁC (Noise Filtering): Nếu bản tin là tin đồn vô căn cứ, giật gân, quảng cáo hoặc không chứa thông tin vĩ mô cụ thể, BẮT BUỘC trả về danh sách tín hiệu rỗng: {"signals": []}."""


def extract_signals(news_content: str, custom_prompt: str = None, enabled_categories: dict = None) -> dict:
    """Bước 1: Trích xuất dữ liệu cứng/tín hiệu thô từ tin tức văn bản"""
    instruction_body = custom_prompt.strip() if (custom_prompt and custom_prompt.strip()) else DEFAULT_SIGNAL_EXTRACTION_PROMPT
    
    category_filter_note = ""
    if enabled_categories:
        allowed = [k.capitalize() for k, v in enabled_categories.items() if v]
        if allowed:
            category_filter_note = f"\nCHỈ trích xuất các tín hiệu thuộc các nhóm sau: {', '.join(allowed)}."
    
    prompt = f"""{instruction_body}{category_filter_note}

Tin tức cần phân tích:
{news_content}
"""
    return global_gemini_client.generate_structured_data(prompt, SignalOutput)


DEFAULT_THESIS_PROMPT = """Bạn là một nhà quản lý quỹ định lượng (Quant Fund Manager) và chuyên gia phân tích chu kỳ dòng tiền tài chính vĩ mô toàn cầu & Việt Nam.
Nhiệm vụ của bạn là dựa trên các tín hiệu vĩ mô thực tế, lãi suất và các cảnh báo kích hoạt để đưa ra nhận định vĩ mô cốt lõi và chiến lược phân bổ danh mục tài sản tối ưu."""


def build_thesis_instruction(custom_prompt: str = None, enabled_modules: dict = None) -> str:
    """Xây dựng prompt nhận định linh hoạt theo các module được bật/tắt để tiết kiệm tối đa Token & Chi phí"""
    if enabled_modules is None:
        enabled_modules = {
            "real_estate_vn": True,
            "cash_allocation": True,
            "rwa_strategy": True,
            "forex_pairs": True,
            "asset_weights": True
        }
    
    base_instruction = custom_prompt.strip() if (custom_prompt and custom_prompt.strip()) else DEFAULT_THESIS_PROMPT
    
    sections = [base_instruction, "\n---", "HƯỚNG DẪN PHÂN TÍCH THEO CÁC DANH MỤC ĐƯỢC CHỌN:"]
    
    # 1. Tỷ trọng tài sản
    if enabled_modules.get("asset_weights", True):
        sections.append("""
1. TĂNG / GIẢM TỶ TRỌNG TÀI SẢN (increase_weight & decrease_weight):
   - Đánh giá xu hướng chu kỳ kinh tế (Lạm phát, Đình lạm, Tăng trưởng, Suy thoái).
   - Điền rõ tên các lớp tài sản cần tăng/giảm tỷ trọng (Cổ phiếu VN, Cổ phiếu Mỹ, Vàng, Tiền mặt/USD, BĐS VN, Crypto...).""")
    else:
        sections.append("\n1. TỶ TRỌNG TÀI SẢN: Bỏ qua mục này, trả về [] cho increase_weight và decrease_weight.")

    # 2. RWA Strategy
    if enabled_modules.get("rwa_strategy", True):
        sections.append("""
2. TÀI SẢN PHÒNG THỦ & RWA TOKEN (rwa_strategy_details):
   - Đánh giá các phân khúc: Trái phiếu chính phủ Mỹ (Treasuries), Vàng on-chain, Tín dụng tư nhân (Private Credit)...
   - Đề xuất các token hoặc tài sản RWA phù hợp với bối cảnh vĩ mô (ví dụ: Treasury RWA như ONDO/USDY khi lãi suất cao; Vàng vật chất/PAXG/XAUT khi rủi ro địa chính trị; Private Credit như CFG/MPL khi lãi suất hạ nhiệt).
   - Nêu rõ lý do định lượng cho từng phân khúc.""")
    else:
        sections.append("\n2. RWA STRATEGY: Bỏ qua mục này, trả về [] cho rwa_strategy_details để tiết kiệm chi phí.")

    # 3. Real Estate VN
    if enabled_modules.get("real_estate_vn", True):
        sections.append("""
3. BẤT ĐỘNG SẢN VIỆT NAM (real_estate_vn):
   - Đánh giá triển vọng thị trường BĐS VN dựa trên lãi suất SBV, tăng trưởng tín dụng, đầu tư công (cao tốc, metro, sân bay), FDI.
   - Điền 'market_outlook', 'attractive_segments', 'risks', 'recommendation' (NÊN hay KHÔNG NÊN đầu tư lúc này).
   - Đề xuất cụ thể 3-5 bất động sản/dự án vào 'recommended_properties' với đầy đủ: property_type, area (khu vực cụ thể), project (tên dự án uy tín hoặc khu vực quy hoạch), price_range (khoảng giá tham khảo), reason (lý do định lượng rõ ràng).""")
    else:
        sections.append("\n3. BẤT ĐỘNG SẢN VIỆT NAM: Bỏ qua mục này, trả về null cho trường 'real_estate_vn' để tiết kiệm chi phí.")

    # 4. Cash Allocation
    if enabled_modules.get("cash_allocation", True):
        sections.append("""
4. PHÂN BỔ TIỀN MẶT: VND vs USD (cash_allocation):
   - Phân bổ currency_distribution (tỷ lệ VND, USD, USDT/USDC với tổng = 1.0) theo dự báo tỷ giá USD/VND.
   - Tham chiếu bảng lãi suất ngân hàng VN thực tế (Cake.vn) cho vn_bank_interest_rate.
   - So sánh lợi suất Stablecoin USD (Binance/OKX Earn, On-chain lending) trong stablecoin_platform_yields.
   - Đưa ra recommendation chi tiết về chiến lược giữ tiền mặt tối ưu và quản trị rủi ro trượt giá/rủi ro sàn.""")
    else:
        sections.append("\n4. PHÂN BỔ TIỀN MẶT: Bỏ qua mục này, trả về null cho trường 'cash_allocation' để tiết kiệm chi phí.")

    # 5. Forex Pairs
    if enabled_modules.get("forex_pairs", True):
        sections.append("""
5. KHUYẾN NGHỊ GIAO DỊCH FOREX (recommended_forex_pairs):
   - Dựa trên DXY, lợi suất Trái phiếu Mỹ, giá Dầu và tâm lý Risk-On / Risk-Off.
   - Đề xuất tối thiểu 3 cặp tiền với vị thế rõ ràng (ví dụ: 'Mua EURUSD', 'Bán USDJPY', 'Bán USDCAD', 'Mua AUDUSD', 'Mua XAUUSD').""")
    else:
        sections.append("\n5. FOREX PAIRS: Bỏ qua mục này, trả về [] cho recommended_forex_pairs để tiết kiệm chi phí.")

    sections.append("""
---
YÊU CẦU ĐỊNH DẠNG & ĐÁNH GIÁ ĐỘ TIN CẬY (confidence):
- Đánh giá trường 'confidence' (0.0 đến 1.0) theo mức độ tin cậy của dữ liệu:
  + 0.80 - 0.95: Khi có đầy đủ dữ liệu vĩ mô, cảnh báo dòng tiền (DXY/Yield/Gold) và lãi suất hỗ trợ rõ ràng.
  + 0.65 - 0.79: Khi xu hướng vĩ mô đã định hình rõ nét.
- Toàn bộ nội dung mô tả, nhận định, lý do BẮT BUỘC viết bằng Tiếng Việt chuẩn mực.
- Tuân thủ chặt chẽ định dạng JSON Output Schema.""")
    
    return "\n".join(sections)


def generate_thesis(extracted_signals: dict, interest_rate_context: str = None, triggered_alerts_context: str = None, custom_prompt: str = None, enabled_modules: dict = None) -> dict:
    interest_section = ""
    if interest_rate_context and (enabled_modules is None or enabled_modules.get("cash_allocation", True)):
        interest_section = f"""
    Danh sách Lãi suất gửi tiết kiệm thực tế tại các Ngân hàng Việt Nam (cập nhật từ Cake.vn):
    {interest_rate_context}
    
    Hãy ưu tiên tham chiếu và trích xuất số liệu từ bảng lãi suất thực tế này để so sánh, phân tích trong phần 'cash_allocation'. Khi đưa ra con số lãi suất gửi tiết kiệm VN thực tế, hãy chỉ rõ các ngân hàng thương mại đang có lãi suất cao nổi trội bên cạnh nhóm ngân hàng nhà nước.
    """

    alerts_section = ""
    if triggered_alerts_context:
        alerts_section = f"""
    Danh sách các Cảnh báo giá/lợi suất đã kích hoạt gần đây (Triggered Alerts):
    {triggered_alerts_context}
    
    Hãy phân tích chi tiết các cảnh báo kích hoạt này (đặc biệt là các tín hiệu vượt đỉnh 52 tuần của lợi suất trái phiếu chính phủ Mỹ US30Y/US10Y, giá vàng, giá dầu, hoặc các cảnh báo tiền mã hóa/cổ phiếu lớn) để đánh giá sự chuyển dịch của dòng tiền vĩ mô (Money Flows) và các khuyến nghị phân bổ vốn/giao dịch ngoại hối.
    """

    instruction_body = build_thesis_instruction(custom_prompt=custom_prompt, enabled_modules=enabled_modules)

    prompt = f"""
    {instruction_body}

    ---
    DỮ LIỆU TÍN HIỆU CỨNG THỰC TẾ (REAL-TIME SIGNALS):
    Extracted Signals (JSON):
    {json.dumps(extracted_signals, ensure_ascii=False)}
    
    {interest_section}
    {alerts_section}
    """
    return global_gemini_client.generate_structured_data(prompt, ThesisOutput)


DEFAULT_WORLD_STATE_PROMPT = """Bạn là AI Quản lý World State cho nền tảng Macro Intelligence.
Nhiệm vụ của bạn là so sánh Trạng thái Thế giới hiện tại (Current World State) với các Tín hiệu (Signals) và Nhận định (Theses) mới nhận được để đề xuất cập nhật thay đổi.

DANH MỤC ENTITY & FIELD CHUẨN:
- target_entity:
  + Nhóm Ngân hàng TW: FED, ECB, BOE, BOJ, SBV, PBOC, RBA, BoC
  + Nhóm Năng lượng & Hàng hóa: OPEC, OPEC+, Oil (Crude, WTI, Brent), Gold
  + Nhóm Thanh khoản & Vĩ mô: US_Economy, VN_Economy, Global_Liquidity, Crypto_Market, DXY
- field_name: trend, status, risk_level, production_policy, liquidity_status, v.v.

QUY TẮC CẬP NHẬT:
1. Trường 'new_value' và 'reason' BẮT BUỘC viết bằng Tiếng Việt.
2. Dịch thuật ngữ chuẩn: 'Hawkish' -> 'Thắt chặt (Diều hâu)', 'Dovish' -> 'Nới lỏng (Bồ câu)', 'Neutral' -> 'Trung lập'.
3. NGƯỠNG THAY ĐỔI: Chỉ đề xuất thay đổi khi có dữ liệu/phát biểu chính sách mới rõ ràng có độ tin cậy cao (confidence >= 0.75). Nếu dữ liệu mới trùng khớp với trạng thái hiện tại hoặc chỉ là biến động nhỏ trong phiên, BẮT BUỘC trả về: {"proposed_changes": []}."""


def propose_world_state_changes(current_state: dict, signals: dict, theses: dict, custom_prompt: str = None, enabled_entities: dict = None) -> dict:
    """Bước 3: Đề xuất cập nhật trạng thái hệ thống bằng Tiếng Việt"""
    instruction_body = custom_prompt.strip() if (custom_prompt and custom_prompt.strip()) else DEFAULT_WORLD_STATE_PROMPT
    
    entity_filter_note = ""
    if enabled_entities:
        active_groups = [k for k, v in enabled_entities.items() if v]
        if active_groups:
            entity_filter_note = f"\nLƯU Ý: Chỉ tập trung đề xuất thay đổi cho các nhóm đối tượng: {', '.join(active_groups)}."
    
    prompt = f"""
    {instruction_body}{entity_filter_note}

    ---
    Current World State (JSON):
    {json.dumps(current_state, ensure_ascii=False)}
    
    Recent Signals (JSON):
    {json.dumps(signals, ensure_ascii=False)}
    
    Active Theses (JSON):
    {json.dumps(theses, ensure_ascii=False)}
    """
    return global_gemini_client.generate_structured_data(prompt, WorldStateChangesOutput)