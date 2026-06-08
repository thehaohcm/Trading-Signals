import os
import json
import logging
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from openai import OpenAI  # BỔ SUNG: Import OpenAI client để gọi 9router
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cấu hình biến môi trường
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# BỔ SUNG: Cấu hình dữ liệu 9router (Ưu tiên đọc từ .env, nếu không có sẽ lấy giá trị default bạn cung cấp)
NINE_ROUTER_API_KEY = os.getenv("NINE_ROUTER_API_KEY", "sk-9364b94cdc4d2aa6-j38x1o-c85be73b")
NINE_ROUTER_ENDPOINT = os.getenv("NINE_ROUTER_ENDPOINT", "http://152.53.208.182:20128/v1")
NINE_ROUTER_MODEL = os.getenv("NINE_ROUTER_MODEL", "my-combo")

# ==========================================
# CẤU TRÚC ĐẦU RA (PYDANTIC SCHEMAS)
# ==========================================

class AdvancedMarketMetric(BaseModel):
    metric_name: str = Field(description="Tên chỉ số hoặc thị trường cụ thể. Ví dụ: Euro Stoxx 50, KOSDAQ, Bitcoin, RMB, v.v.")
    status_or_value: str = Field(description="Trạng thái hoặc xu hướng biến động. Ví dụ: Giảm 3%, Thắt chặt cung ứng, Căng thẳng leo thang...")

class SignalItem(BaseModel):
    category: str = Field(description="Categories: Policy, Liquidity, Inflation, Growth, Market Sentiment, Geopolitics, Asset_Specific")
    signal: str = Field(description="Xu hướng tổng quan: Hawkish, Dovish, Tightening, Easing, Risk-off, Risk-on...")
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(description="Phân tích chi tiết bối cảnh sự kiện vĩ mô.")
    
    # 💡 THÊM TRƯỜNG NÀY ĐỂ CHỨA DỮ LIỆU ĐA DẠNG CỦA 9ROUTER
    specific_metrics: Optional[List[AdvancedMarketMetric]] = Field(
        default=None, 
        description="Danh sách các số liệu, thị trường hoặc sự kiện chi tiết đi kèm nếu có (ví dụ: các chỉ số tương lai, địa điểm xung đột)."
    )

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
# CLIENTS MANAGEMENT (SINGLETON PATTERN)
# ==========================================

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemma-4-26b-a4b-it" 

    def generate_structured_data(self, prompt: str, response_schema) -> dict:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {}

class NineRouterClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=NINE_ROUTER_API_KEY,
            base_url=NINE_ROUTER_ENDPOINT
        )
        self.model = NINE_ROUTER_MODEL

    def generate_structured_data(self, prompt: str, response_schema) -> dict:
        try:
            logger.info(f"🔗 Đang xử lý dữ liệu qua cổng 9router (Combo: {self.model})...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Quant Researcher. You MUST respond strictly in valid JSON format matching the schema requested."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                timeout=30.0
            )
            
            raw_content = response.choices[0].message.content.strip()
            
            clean_json = raw_content
            if "```json" in raw_content:
                json_match = re.search(r"```json\s*(.*?)\s*```", raw_content, re.DOTALL)
                if json_match:
                    clean_json = json_match.group(1).strip()
            
            try:
                data = json.loads(clean_json)
            except Exception:
                raise ValueError("9router không trả về cấu trúc JSON hợp lệ.")

            # =========================================================================
            # 🛠️ BỘ LỌC CƠ KHÍ NÂNG CẤP: CHỐNG MỌI BIẾN DẠNG SCHEMA
            # =========================================================================
            if response_schema.__name__ == "SignalOutput":
                rebuilt_signals = []

                # Hàm bổ trợ ép kiểu confidence từ chuỗi 'high/medium/low' về float chuẩn
                def clean_confidence(val) -> float:
                    if isinstance(val, (int, float)):
                        return float(val)
                    if isinstance(val, str):
                        val_lower = val.strip().lower()
                        if "high" in val_lower:
                            return 0.9
                        if "medium" in val_lower:
                            return 0.7
                        if "low" in val_lower:
                            return 0.5
                        try:
                            return float(val_lower)
                        except ValueError:
                            return 0.85
                    return 0.85

                # 💡 BỔ SUNG ĐOẠN NÀY LÊN ĐẦU: Xử lý trường hợp 9router trả về thẳng một MẶNG [] (Root List)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            # Kiểm tra xem có phải cấu trúc biến dị mới (signal_type, description, direction)
                            if "signal_type" in item or "description" in item:
                                txt_signal = item.get("description", "Tín hiệu thị trường")
                                txt_reason = f"Direction: {item.get('direction', '')} | Assets: {', '.join(item.get('affected_assets', []))} | Level: {item.get('impact_level', '')}"
                                rebuilt_signals.append({
                                    "category": item.get("signal_type", "Market Sentiment"),
                                    "signal": str(txt_signal)[:100],
                                    "confidence": clean_confidence(item.get("impact_level")),
                                    "reason": txt_reason
                                })
                            # Phòng hờ mảng chứa các signal chuẩn bị thiếu trường
                            else:
                                txt = item.get("signal", item.get("reason", "Phân tích tín hiệu vĩ mô"))
                                rebuilt_signals.append({
                                    "category": item.get("category", "Market Sentiment"),
                                    "signal": txt[:100],
                                    "confidence": clean_confidence(item.get("confidence")),
                                    "reason": item.get("reason", txt)
                                })

                # Trường hợp 1: Dữ liệu trả về dạng Dictionary và có mảng 'signals' chuẩn
                elif isinstance(data, dict) and "signals" in data and isinstance(data["signals"], list):
                    for item in data["signals"]:
                        if isinstance(item, dict):
                            txt = item.get("signal", item.get("reason", "Phân tích tín hiệu vĩ mô"))
                            rebuilt_signals.append({
                                "category": item.get("category", "Market Sentiment"),
                                "signal": txt[:100],
                                "confidence": clean_confidence(item.get("confidence")),
                                "reason": item.get("reason", txt)
                            })

                # Trường hợp 2: Dữ liệu trả về các mảng tùy biến khác (events, macro_signals...)
                elif isinstance(data, dict):
                    # 🔹 Biến thể A: 9router trả về mảng rỗng nhưng CÓ câu giải thích tin rác
                    if any(k in data for k in ["analysis", "summary"]) and (not data.get("macro_signals") and not data.get("signals") and not data.get("macroeconomic_signals")):
                        txt_reason = data.get("analysis", data.get("summary", "Không có tín hiệu vĩ mô"))
                        rebuilt_signals.append({
                            "category": "Market Sentiment",
                            "signal": "Neutral",
                            "confidence": 0.9,
                            "reason": str(txt_reason)[:500]
                        })

                    # 🔹 Biến thể I (MỚI): Tin động đất Philippines - mảng "macroeconomic_signals" rỗng hoặc chứa cấu trúc lồng
                    elif "macroeconomic_signals" in data and isinstance(data["macroeconomic_signals"], list):
                        raw_macros = data["macroeconomic_signals"]
                        if len(raw_macros) == 0: # Động đất nhưng chưa có đánh giá vĩ mô sâu
                            txt_event = data.get("event", "Thiên tai/Địa chất")
                            txt_loc = f"Location: {data.get('location', '')} | Magnitude: {data.get('magnitude', '')}"
                            rebuilt_signals.append({
                                "category": "Geopolitics", # Gom thiên tai lớn vào nhóm rủi ro hệ thống toàn cầu
                                "signal": f"Earthquake {data.get('magnitude', '')}",
                                "confidence": 0.85,
                                "reason": txt_loc
                            })
                        else: # Động đất có mảng đánh giá tác động (Infrastructure damage, Supply chain)
                            for mac_sig in raw_macros:
                                if isinstance(mac_sig, dict):
                                    txt_sig = mac_sig.get("signal", "Thiên tai lớn ảnh hưởng vĩ mô")
                                    effects = mac_sig.get("potential_effects", [])
                                    txt_reason = f"Areas: {', '.join(mac_sig.get('impact_areas', []))} | Effects: {'; '.join(effects)}"
                                    rebuilt_signals.append({
                                        "category": "Growth",
                                        "signal": str(txt_sig)[:100],
                                        "confidence": 0.85,
                                        "reason": txt_reason
                                    })

                    # 🔹 Biến thể J (MỚI): Cấu trúc chỉ số kinh tế phẳng của Nhật (indicator, actual_value/actual, interpretation/implication)
                    elif "indicator" in data:
                        txt_indicator = data.get("indicator", "Chỉ số kinh tế")
                        actual = data.get("actual_value", data.get("actual", "N/A"))
                        previous = data.get("previous_value", data.get("previous", "N/A"))
                        unit = data.get("unit", "")
                        
                        txt_signal = f"{txt_indicator}: {actual} {unit} (Prev: {previous})"
                        txt_reason = data.get("interpretation", data.get("implication", "Cập nhật số liệu vĩ mô cứng"))
                        
                        rebuilt_signals.append({
                            "category": "Growth" if "Trade" in txt_indicator or "Account" in txt_indicator else "Liquidity",
                            "signal": str(txt_signal)[:100],
                            "confidence": 1.0, # Số liệu chính phủ công bố, độ tin cậy tuyệt đối
                            "reason": str(txt_reason)
                        })

                    # 🔹 Biến thể B: Object phẳng hoàn toàn - Tin địa chính trị nóng (Israel tấn công Iran)
                    elif any(k in data for k in ["geopolitical_impact", "market_implications"]):
                        txt_signal = data.get("event", "Biến động địa chính trị")
                        txt_reason = f"Impact: {data.get('geopolitical_impact', '')} | Market: {data.get('market_implications', '')}"
                        rebuilt_signals.append({
                            "category": "Geopolitics",
                            "signal": str(txt_signal)[:100],
                            "confidence": 0.9,
                            "reason": txt_reason
                        })

                    # 🔹 Biến thể C: "macro_signals" chứa danh sách chuỗi thô (Tin Yemen bắn tên lửa)
                    elif "macro_signals" in data and isinstance(data["macro_signals"], list) and len(data["macro_signals"]) > 0:
                        first_item = data["macro_signals"][0]
                        if isinstance(first_item, str): 
                            for str_signal in data["macro_signals"]:
                                rebuilt_signals.append({
                                    "category": "Market Sentiment",
                                    "signal": str(str_signal)[:100],
                                    "confidence": 0.85,
                                    "reason": data.get("event", "Phát hiện biến động địa chính trị")
                                })
                        elif isinstance(first_item, dict): 
                            for obj_signal in data["macro_signals"]:
                                txt = obj_signal.get("signal", "Biến động vĩ mô")
                                rebuilt_signals.append({
                                    "category": "Market Sentiment",
                                    "signal": str(txt)[:100],
                                    "confidence": clean_confidence(obj_signal.get("confidence")),
                                    "reason": obj_signal.get("reason", txt)
                                })

                    # 🔹 Biến thể D: Xuất hiện mảng "extracted_signals" lồng object (Tin Goldman Sachs)
                    elif "extracted_signals" in data and isinstance(data["extracted_signals"], list) and len(data["extracted_signals"]) > 0:
                        for ext_sig in data["extracted_signals"]:
                            if isinstance(ext_sig, dict):
                                txt = ext_sig.get("detail", ext_sig.get("signal", "Tín hiệu trích xuất"))
                                rebuilt_signals.append({
                                    "category": ext_sig.get("category", "Policy"),
                                    "signal": str(txt)[:100],
                                    "confidence": clean_confidence(ext_sig.get("confidence")),
                                    "reason": f"Source: {ext_sig.get('source', 'Unknown')} | Impact: {ext_sig.get('impact', 'Medium')}"
                                })

                    # 💡 BỔ SUNG BIẾN THỂ F VÀO ĐÂY: Xử lý cấu trúc chính sách bán dẫn (actionable_signals + impact)
                    elif "actionable_signals" in data and isinstance(data["actionable_signals"], list) and len(data["actionable_signals"]) > 0:
                        # Gom thông tin tác động ngắn hạn/dài hạn làm lý do
                        impact_data = data.get("impact", {})
                        txt_reason = ""
                        if isinstance(impact_data, dict):
                            txt_reason = f"Short-term: {impact_data.get('short_term', '')} | Long-term: {impact_data.get('long_term', '')}"
                        else:
                            txt_reason = str(impact_data)
                            
                        for act_sig in data["actionable_signals"]:
                            rebuilt_signals.append({
                                "category": "Policy",
                                "signal": str(act_sig)[:100],
                                "confidence": 0.85,
                                "reason": txt_reason if txt_reason else "Theo dõi chính sách công nghiệp chính phủ"
                            })

                    # 💡 BỔ SUNG BIẾN THỂ G VÀO ĐÂY: Xử lý cấu trúc rủi ro địa chính trị (potential_macro_impact)
                    elif any(k in data for k in ["potential_macro_impact", "geopolitical_risk"]):
                        txt_signal = data.get("potential_macro_impact", "Phát hiện tác động vĩ mô tiềm năng")
                        txt_reason = f"Risk: {data.get('geopolitical_risk', '')} | Assets to watch: {', '.join(data.get('key_assets_to_monitor', []))}"
                        
                        rebuilt_signals.append({
                            "category": data.get("event_category", "Geopolitics"),
                            # Vì potential_macro_impact có thể dài, ta lấy 100 ký tự đầu làm tiêu đề signal
                            "signal": str(txt_signal)[:100], 
                            "confidence": clean_confidence(data.get("confidence")),
                            "reason": txt_reason
                        })
                    
                    # 💡 BỔ SUNG BIẾN THỂ H VÀO ĐÂY: Xử lý cấu trúc khủng hoảng thị trường (key_signals + main_event)
                    elif "key_signals" in data and isinstance(data["key_signals"], list) and len(data["key_signals"]) > 0:
                        txt_reason_global = data.get("overall_macro_outlook", data.get("main_event", "Khủng hoảng thị trường"))
                        for k_sig in data["key_signals"]:
                            if isinstance(k_sig, dict):
                                txt_signal = k_sig.get("description", "Phát hiện tín hiệu thị trường")
                                txt_reason = f"Impact: {k_sig.get('value_impact', '')} | Outlook: {txt_reason_global}"
                                rebuilt_signals.append({
                                    "category": k_sig.get("signal_type", "Market Sentiment"),
                                    "signal": str(txt_signal)[:100],
                                    "confidence": 0.9, # Sự kiện sập mạnh, đặt confidence cao
                                    "reason": txt_reason
                                })

                    # 🔹 Biến thể E: Các mảng dữ liệu cấu trúc cũ (events, event_analysis)
                    else:
                        raw_items = data.get("events", data.get("event_analysis", []))
                        if isinstance(raw_items, list) and len(raw_items) > 0:
                            for x in raw_items:
                                if isinstance(x, dict):
                                    txt = x.get("signal", x.get("event_type", x.get("metric", "Biến động vĩ mô")))
                                    rebuilt_signals.append({
                                        "category": "Market Sentiment",
                                        "signal": str(txt)[:100],
                                        "confidence": clean_confidence(x.get("confidence")),
                                        "reason": json.dumps(x, ensure_ascii=False)
                                    })
                        
                        # Trường hợp 9router trả về dạng Object đơn lẻ khác
                        elif any(k in data for k in ["signal_type", "event_type", "signal", "metric"]):
                            txt = data.get("signal", data.get("signal_type", "Cập nhật dữ liệu cấu trúc đơn"))
                            rebuilt_signals.append({
                                "category": "Market Sentiment",
                                "signal": str(txt)[:100],
                                "confidence": clean_confidence(data.get("confidence")),
                                "reason": json.dumps(data, ensure_ascii=False)
                            })

                # Đoạn cứu nguy tối hậu nếu mảng trống
                if not rebuilt_signals:
                    # Kiểm tra xem có phải AI chủ động báo tin rác không (macro_signals hoặc signals trống)
                    if isinstance(data, dict) and (data.get("macro_signals") == [] or data.get("signals") == []):
                        logger.info("ℹ️ 9router xác nhận tin tức không chứa dữ liệu vĩ mô. Ghi nhận trạng thái Trung lập (Neutral).")
                        rebuilt_signals.append({
                            "category": "Market Sentiment",
                            "signal": "Neutral",
                            "confidence": 1.0,
                            "reason": data.get("analysis", data.get("summary", "News text contains no macroeconomic data."))
                        })
                    else:
                        # Đây mới thực sự là LỖI cấu trúc biến dị mới lạ hoắc
                        logger.error("=" * 60)
                        logger.error("🚨 [CRITICAL_SCHEMA_ERROR] Xuất hiện cấu trúc biến dị mới hoàn toàn!")
                        logger.error(f"📄 Dữ liệu thô lỗi:\n{clean_json}")
                        logger.error("=" * 60)
                        
                        # Bạn có thể gọi bot Telegram Pyrogram ở đây để bắn thông báo về điện thoại:
                        # send_telegram_alert(f"Bot gặp cấu trúc lạ: {clean_json[:200]}")

                        logger.warning("⚠️ Tự động ép bản ghi mặc định để bảo vệ vòng lặp APScheduler...")
                        rebuilt_signals.append({
                            "category": "Market Sentiment",
                            "signal": "Neutral",
                            "confidence": 0.5,
                            "reason": f"Dữ liệu lỗi cấu trúc, tự động hạ cấp phòng thủ. Raw: {clean_json[:200]}"
                        })

                # Ghi đè lại biến data bằng cấu trúc hoàn chỉnh sạch sẽ
                data = {"signals": rebuilt_signals}

            if response_schema.__name__ == "ThesisOutput" and isinstance(data, dict):
                # Nếu 9router dùng các key dị như 'macro_judgment' hoặc 'judgment' thay vì 'theses'
                if "theses" not in data:
                    # 💡 BỔ SUNG: Thêm data.get("macro_assessment") vào đầu chuỗi quét key dị
                    raw_theses = data.get("macro_assessment", data.get("macro_judgment", data.get("judgment", data.get("allocation_thesis", None))))
                    
                    # Nếu nội dung trả về là một Object đơn lẻ (không bọc mảng)
                    if isinstance(raw_theses, dict):
                        # Chuẩn hóa cấu trúc con allocation_plan
                        raw_plan = raw_theses.get("allocation_plan", {})
                        clean_plan = {
                            "increase_weight": raw_plan.get("increase_weight", []),
                            "decrease_weight": raw_plan.get("decrease_weight", []),
                            "rwa_strategy_details": raw_plan.get("rwa_strategy_details", [])
                        }
                        
                        data = {
                            "theses": [{
                                "thesis": raw_theses.get("thesis", "Nhận định chiến lược dòng tiền vĩ mô"),
                                "confidence": float(raw_theses.get("confidence", 0.85)),
                                "allocation_plan": clean_plan
                            }]
                        }
                    
                    # Nếu nó trả về mảng nhưng sai tên key
                    elif isinstance(raw_theses, list):
                        data = {"theses": raw_theses}

            # =========================================================================
            # TIẾN HÀNH VALIDATE HOẶC FIXER
            # =========================================================================
            try:
                response_schema.model_validate(data)
                return data
            except Exception as schema_err:
                logger.warning(f"⚠️ Dữ liệu vẫn lệch Schema sau khi gọt bằng Python ({schema_err}). Chuyển giao sang Gemini Fixer...")
                fixed_data = ask_gemini_to_fix_schema(data, response_schema)
                if fixed_data:
                    return fixed_data
                raise schema_err

        except Exception as e:
            logger.error(f"❌ Cổng 9router combo gặp sự cố: {e}")
            logger.info("🛡️ Kích hoạt Fallback toàn phần từ Gemini bản gốc...")
            return global_gemini_client.generate_structured_data(prompt, response_schema)

# Khởi tạo các client dùng chung cho toàn bộ ứng dụng
global_gemini_client = GeminiClient()
global_9router_client = NineRouterClient()


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
    # Bạn có thể dùng 9router hoặc Gemini cho bước này. Khuyên dùng 9router để đồng bộ dòng tư duy logic.
    return global_9router_client.generate_structured_data(prompt, SignalOutput)


def generate_thesis(extracted_signals: dict) -> dict:
    """Bước 2: Lập luận xác suất và cấu trúc danh mục tài sản"""
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
    return global_9router_client.generate_structured_data(prompt, ThesisOutput)


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
    return global_9router_client.generate_structured_data(prompt, WorldStateChangesOutput)

def ask_gemini_to_fix_schema(bad_json_data: dict, response_schema) -> dict:
    """
    Hàm gọt giũa JSON cấu trúc lạ bằng Gemini Flash
    """
    try:
        logger.info("🛡️ [Fixer] Đang nhờ Gemini định dạng lại cấu trúc JSON cứng...")
        fixer_prompt = f"""
        You are a strict Data Transformation Engine.
        Map the following raw data fields into the strictly required JSON schema format.
        
        Raw Data:
        {json.dumps(bad_json_data, ensure_ascii=False)}

        CRITICAL: Output ONLY valid JSON matching the schema. No explanations.
        """
        response = global_gemini_client.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=fixer_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"❌ [Fixer Failed] Không thể ép cấu trúc bằng Gemini: {e}")
        return {}