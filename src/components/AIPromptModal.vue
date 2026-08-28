<template>
  <div v-if="modelValue" class="ai-prompt-modal-overlay" @click.self="close">
    <div class="ai-prompt-modal-container">
      <!-- Header -->
      <div class="ai-modal-header">
        <div class="d-flex align-items-center gap-3">
          <div class="ai-modal-badge-icon">🤖</div>
          <div>
            <h4 class="ai-modal-title mb-0">Chỉnh sửa Prompt AI Platform Intelligence</h4>
            <span class="ai-modal-subtitle">Tùy chỉnh chỉ dẫn và logic phân tích vĩ mô của AI</span>
          </div>
        </div>
        <button class="ai-close-btn" @click="close" title="Đóng modal">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <!-- Presets Toolbar -->
      <div class="ai-presets-bar">
        <span class="presets-label"><i class="bi bi-stars text-warning me-1"></i>Mẫu gợi ý:</span>
        <div class="presets-buttons">
          <button 
            type="button" 
            :class="['preset-chip', { active: activePreset === 'default' }]" 
            @click="applyPreset('default')"
            title="Nhận định vĩ mô cân bằng toàn diện"
          >
            <span class="preset-icon">🌐</span>
            <span>Toàn diện vĩ mô</span>
          </button>
          <button 
            type="button" 
            :class="['preset-chip', { active: activePreset === 'vn_market' }]" 
            @click="applyPreset('vn_market')"
            title="Ưu tiên nhóm ngành chứng khoán VN & Bất động sản"
          >
            <span class="preset-icon">🇻🇳</span>
            <span>CK & BĐS Việt Nam</span>
          </button>
          <button 
            type="button" 
            :class="['preset-chip', { active: activePreset === 'forex_gold' }]" 
            @click="applyPreset('forex_gold')"
            title="Tập trung DXY, Vàng thế giới, Lợi suất US & Forex"
          >
            <span class="preset-icon">🥇</span>
            <span>Vàng & Forex</span>
          </button>
          <button 
            type="button" 
            :class="['preset-chip', { active: activePreset === 'crypto_rwa' }]" 
            @click="applyPreset('crypto_rwa')"
            title="Tập trung Crypto & Token RWA phòng thủ"
          >
            <span class="preset-icon">⚡</span>
            <span>Crypto & RWA</span>
          </button>
        </div>
      </div>

      <!-- Body -->
      <div class="ai-modal-body">
        <div class="ai-help-banner mb-3">
          <i class="bi bi-info-circle-fill text-info me-2 fs-6"></i>
          <span>
            Prompt này sẽ định hướng AI khi tổng hợp dữ liệu tin tức vĩ mô, cảnh báo giá, lãi suất và đưa ra tư vấn danh mục. Bạn có thể sử dụng <code>{{NEWS_ITEMS}}</code> nếu muốn chỉ định vị trí tin tức.
          </span>
        </div>

        <div class="position-relative">
          <textarea
            v-model="promptContent"
            class="ai-textarea form-control"
            rows="13"
            placeholder="Nhập prompt tùy chỉnh cho AI..."
            spellcheck="false"
            @input="activePreset = ''"
          ></textarea>
          
          <div class="char-counter">
            {{ promptContent.length.toLocaleString() }} ký tự
          </div>
        </div>

        <div v-if="statusMessage" :class="['status-alert mt-2', statusType === 'success' ? 'status-success' : 'status-error']">
          <i :class="statusType === 'success' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill'" class="me-1"></i>
          {{ statusMessage }}
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="ai-modal-footer">
        <!-- Left Utility Buttons -->
        <div class="footer-left">
          <button 
            type="button" 
            class="btn-action-ghost" 
            @click="resetToDefault"
            title="Khôi phục về prompt ban đầu của hệ thống"
          >
            <i class="bi bi-arrow-counterclockwise"></i>
            <span>Mặc định</span>
          </button>
          <button 
            type="button" 
            :class="['btn-action-ghost', { copied }]" 
            @click="copyPrompt"
            title="Sao chép nội dung prompt vào clipboard"
          >
            <i :class="copied ? 'bi bi-check2 text-success' : 'bi bi-clipboard'"></i>
            <span>{{ copied ? 'Đã sao chép' : 'Sao chép' }}</span>
          </button>
        </div>

        <!-- Right Main Buttons -->
        <div class="footer-right">
          <button 
            type="button" 
            class="btn-modal-close" 
            @click="close"
          >
            Đóng
          </button>
          <button 
            type="button" 
            class="btn-modal-save" 
            :disabled="saving || running"
            @click="savePrompt(false)"
            title="Lưu cấu hình prompt vào hệ thống"
          >
            <span v-if="saving" class="spinner-border spinner-border-sm" role="status"></span>
            <i v-else class="bi bi-floppy2-fill"></i>
            <span>Lưu Prompt</span>
          </button>
          <button 
            type="button" 
            class="btn-modal-execute" 
            :disabled="saving || running"
            @click="savePrompt(true)"
            title="Lưu prompt mới và kích hoạt AI phân tích ngay lập tức"
          >
            <span v-if="running" class="spinner-border spinner-border-sm" role="status"></span>
            <i v-else class="bi bi-lightning-charge-fill"></i>
            <span>Lưu & Chạy phân tích ngay</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'saved', 'run-analysis'])

const promptContent = ref('')
const activePreset = ref('default')
const saving = ref(false)
const running = ref(false)
const copied = ref(false)
const statusMessage = ref('')
const statusType = ref('success')

const defaultPrompt = `Bạn là một nhà quản lý quỹ định lượng (Quant Fund Manager) và chuyên gia phân tích chu kỳ dòng tiền tài chính vĩ mô.
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

---

YÊU CẦU PHÂN TÍCH BẤT ĐỘNG SẢN VIỆT NAM (real_estate_vn):
Dựa trên tín hiệu vĩ mô (đặc biệt là lãi suất SBV, tăng trưởng tín dụng, CPI Việt Nam, FDI, chính sách nhà ở, đầu tư công, v.v.), hãy phân tích:

- Tổng quan thị trường BĐS VN: Xu hướng giá, thanh khoản, tâm lý thị trường.
- Phân khúc hấp dẫn nhất trong bối cảnh hiện tại:
  + Nếu lãi suất VN GIẢM & tín dụng BĐS NỚI: Căn hộ trung cấp, đất nền vùng ven, BĐS công nghiệp.
  + Nếu lãi suất VN TĂNG & tín dụng BĐS SIẾT: Hạn chế BĐS, ưu tiên giữ tiền mặt hoặc kênh khác.
  + Nếu đầu tư công & hạ tầng ĐẨY MẠNH (cao tốc, metro, sân bay): BĐS vùng ven hưởng lợi hạ tầng.
- Rủi ro cần lưu ý: pháp lý (sổ đỏ, giải phóng mặt bằng), thanh khoản, định giá quá cao, chính sách thuế BĐS...
- Khuyến nghị cụ thể: NÊN hay KHÔNG NÊN đầu tư BĐS VN lúc này? Nếu có, phân khúc nào, khu vực nào?

**QUAN TRỌNG - LIỆT KÊ recommended_properties chi tiết nhất có thể (ít nhất 3-5 đề xuất):**
Điền đầy đủ vào mảng 'recommended_properties' - mỗi phần tử gồm:
- 'property_type': Loại hình BĐS cụ thể (Chung cư, Nhà phố, Đất nền, Biệt thự, Shophouse, BĐS công nghiệp, BĐS nghỉ dưỡng, Nhà ở xã hội, Đất nông nghiệp...)
- 'area': Khu vực/quận/huyện cụ thể, KHÔNG nói chung chung. Ví dụ: 'Bán đảo Thanh Đa (Quận Bình Thạnh)', 'Huyện Hóc Môn', 'Quận 9 (TP.Thủ Đức)', 'Huyện Bình Chánh', 'Quận Long Biên - Hà Nội', 'TP. Dĩ An - Bình Dương', 'Huyện Nhà Bè'.
- 'project': Tên dự án cụ thể nếu có. BAO GỒM CẢ CÁC DỰ ÁN SẮP MỞ BÁN hoặc ĐANG TRIỂN KHAI GIAI ĐOẠN ĐẦU. Bạn BẮT BUỘC phải ưu tiên đề xuất các dự án của những chủ đầu tư danh tiếng/uy tín như: 'Dự án Bán đảo Thanh Đa (Bình Quới - Thanh Đa)', 'Vinhomes Saigon Park (Hóc Môn) - sắp mở bán', 'Vinhomes Grand Park', 'The Global City', 'KĐT Đông Tăng Long', 'KĐT Sala', 'KĐT Vinhomes Ocean Park 2-3'. Với dự án sắp mở bán, ghi rõ trạng thái (vd: 'sắp mở bán', 'đang giải phóng mặt bằng', 'đang triển khai hạ tầng').
- 'price_range': Khoảng giá tham khảo (ví dụ: '2-3 tỷ/căn hộ 2PN', '15-25 triệu/m2 đất nền', '40-60 triệu/m2 chung cư cao cấp', '800 triệu-1.5 tỷ/lô đất nền'). Với dự án sắp mở bán, ghi giá dự kiến nếu có thông tin (vd: 'Dự kiến 35-45 triệu/m2', 'Giá chưa công bố - tham khảo khu vực lân cận').
- 'reason': Lý do chọn khu vực/dự án này trong bối cảnh hiện tại (ví dụ: 'Được phát triển bởi chủ đầu tư lớn có tiếng và uy tín như Vingroup/Bitexco, đảm bảo tiến độ và tính pháp lý', 'Hưởng lợi từ quy hoạch siêu đô thị sinh thái Bán đảo Thanh Đa', 'Đón đầu quy hoạch lên quận của Hóc Môn và hạ tầng Vinhomes Saigon Park', 'Gần metro Bến Thành - Suối Tiên', 'Hưởng lợi từ cao tốc Bến Lức - Long Thành', 'hưởng lợi từ vành đai 3',...).

---

YÊU CẦU PHÂN TÍCH PHÂN BỔ TIỀN MẶT: VND vs USD (cash_allocation):
Dựa trên bối cảnh vĩ mô, hãy phân tích chi tiết chiến lược giữ tiền mặt:

1. TỶ GIÁ VND/USD:
   - Xu hướng tỷ giá: SBV đang bảo vệ VND hay để trượt giá? Dự trữ ngoại hối ra sao?
   - Nếu VND được dự báo MẤT GIÁ >3%/năm: Nên ưu tiên giữ USD.
   - Nếu VND ỔN ĐỊNH hoặc SBV đang thắt chặt để bảo vệ tỷ giá: Có thể giữ một phần VND.

2. SO SÁNH LÃI SUẤT:
   - Lãi suất tiền gửi ngân hàng VN (VND): Ưu tiên sử dụng số liệu thực tế được cập nhật từ bảng Cake.vn ở trên (ví dụ: khoảng 6.0 - 7.4%/năm cho kỳ hạn 6-12 tháng tại các ngân hàng thương mại). Nếu không có bảng dữ liệu thực tế, sử dụng số liệu mặc định khoảng 4.5-5.5%/năm cho kỳ hạn 6-12 tháng. Có bảo hiểm tiền gửi (tối đa 75 triệu VND). An toàn cao, thanh khoản tốt.
   - Lợi suất stablecoin USD (USDT/USDC) trên các sàn:
     + Binance Earn Flexible: ~5-10% APY (thay đổi theo thị trường)
     + OKX Simple Earn: ~5-10% APY
     + Bybit Earn: ~4-8% APY
     + Lending trên AAVE/Compound (on-chain): ~3-6% APY (tùy utilization rate)
     + Rủi ro: Rủi ro sàn (exchange default, hack), rủi ro smart contract, rủi ro depeg stablecoin, không có bảo hiểm tiền gửi.
   - Lãi suất USD gửi ngân hàng VN: ~0% (gần như không có lãi suất cho USD gửi tại NH VN)

3. PHÂN BỔ KHUYẾN NGHỊ:
   - Trong bối cảnh lãi suất FED CAO: USD mạnh -> nên giữ tỷ trọng USD/USDT cao (60-80%), VND thấp (20-40%).
   - Trong bối cảnh FED HẠ LÃI SUẤT: USD yếu đi -> có thể tăng tỷ trọng VND lên để hưởng lãi suất cao hơn.
   - Nếu chấp nhận rủi ro để tối ưu lợi suất: stake USDT/USDC trên Binance/OKX (lợi suất 5-10% APY, vượt trội so với gửi VND 4.5-5.5% sau khi trừ trượt giá ~2-3%/năm).
   - Nếu ƯU TIÊN AN TOÀN: gửi VND tại ngân hàng lớn (Vietcombank, BIDV, VietinBank) hưởng 4.5-5.5%, có bảo hiểm tiền gửi.
   - Kết hợp cả hai: một phần VND gửi NH (an toàn), một phần USDT stake trên sàn lớn (sinh lời cao hơn).
   - Thế chấp sổ tiết kiệm ngoại tệ (USD) để vay VND (80-100% giá trị sổ tiết kiệm tùy bank) rồi dùng chính số tiền vay đó gửi tiết kiệm ngược lại để ăn chênh lệch lãi suất. lãi vay USD ~5%/năm, lãi gửi VND ~6-7%/năm, ăn chênh lệch 1-2%/năm. Rủi ro: tỷ giá VND/USD biến động, lãi suất thay đổi, thanh khoản sổ tiết kiệm. Vừa được lời từ lãi suất chênh lệch và trượt giá VND/USD mà vẫn giữ được USD.

YÊU CẦU PHÂN TÍCH KHUYẾN NGHỊ GIAO DỊCH FOREX (recommended_forex_pairs):
Dựa trên xu hướng DXY, lợi suất trái phiếu Mỹ, giá dầu mỏ, và tâm lý thị trường (Risk-On / Risk-Off), hãy đề xuất các vị thế giao dịch Forex phù hợp (liệt kê tối thiểu 3 cặp tiền cụ thể kèm theo hướng đi Mua/Bán rõ ràng, ví dụ: 'Mua EURUSD', 'Bán USDJPY', 'Bán USDCAD', 'Mua AUDUSD'):
- Nếu USD mạnh (DXY tăng, lợi suất Mỹ tăng): Mua USDJPY, Mua USDCAD, Bán EURUSD, Bán GBPUSD.
- Nếu tâm lý Risk-On: Mua AUDUSD, Mua NZDUSD, Bán USDCHF.
- Nếu tâm lý Risk-Off (lo sợ, chiến tranh): Mua USDCHF, Mua XAUUSD.
- Nếu giá dầu tăng: Bán USDCAD (CAD mạnh lên).

YÊU CẦU ĐỊNH DẠNG:
- Điền chính xác các nhóm tài sản cần tăng/giảm vào 'increase_weight' và 'decrease_weight' (bao gồm 'Bất động sản VN' nếu phù hợp).
- Điền đầy đủ thông tin vào 'cash_allocation' (currency_distribution, vn_bank_interest_rate, stablecoin_platform_yields, recommendation).
- Điền đầy đủ thông tin vào 'real_estate_vn' (market_outlook, attractive_segments, recommended_properties, risks, recommendation). Mảng 'recommended_properties' là BẮT BUỘC, phải có ít nhất 3-5 đề xuất với property_type, area, project, price_range, reason cụ thể.
- Điền đầy đủ thông tin các cặp tiền Forex khuyến nghị giao dịch vào 'recommended_forex_pairs' (tối thiểu 3 cặp cụ thể kèm hành động Mua/Bán).
- Toàn bộ phần mô tả lý do (reason, thesis, recommendation, market_outlook) BẮT BUỘC viết bằng Tiếng Việt.`

const presets = {
  default: defaultPrompt,
  vn_market: `Bạn là chuyên gia kinh tế trưởng tập trung sâu vào thị trường tài chính Việt Nam. Hãy phân tích các tín hiệu vĩ mô quốc tế và trong nước:
{{NEWS_ITEMS}}

Trọng tâm phân tích:
1. Tác động của chính sách tiền tệ NHNN (SBV), tỷ giá USD/VND và thanh khoản hệ thống liên ngân hàng đến TTCK Việt Nam.
2. Đánh giá nhóm ngành cổ phiếu dẫn dắt (Bất động sản, Ngân hàng, Chứng khoán, Thép, Bán lẻ, Xuất khẩu) có điểm mua an toàn.
3. Thị trường Bất động sản Việt Nam: Triển vọng phân khúc chung cư, đất nền ven đô, BĐS công nghiệp; gợi ý các dự án hoặc khu vực có dòng tiền thật và tiềm năng tăng trưởng (Thanh Đa, Hóc Môn, Quận 9, Long Biên, Dĩ An...).
4. Quản trị rủi ro danh mục và khuyến nghị phân bổ tỷ trọng Tiền mặt / Cổ phiếu / Vàng / BĐS.`,
  forex_gold: `Bạn là chuyên gia giao dịch FX & Kim loại quý hàng đầu thế giới. Dựa trên các dữ liệu vĩ mô và cảnh báo kích hoạt:
{{NEWS_ITEMS}}

Trọng tâm phân tích:
1. Xu hướng DXY (Chỉ số Dollar) và Lợi suất trái phiếu Mỹ (US02Y, US10Y, US30Y) - Đánh giá kỳ vọng lãi suất Fed (Hawkish vs Dovish).
2. Phân tích giá Vàng (XAU/USD) & Dầu thô (WTI/Brent) dưới góc nhìn địa chính trị và lạm phát.
3. Đề xuất chi tiết chiến lược giao dịch FX cho các cặp chính (EURUSD, GBPUSD, USDJPY, USDCAD, AUDUSD, USDCHF) với hướng đi Long/Short rõ ràng.
4. Khuyến nghị phân bổ dòng tiền nhàn rỗi và các kênh trú ẩn rủi ro an toàn nhất.`,
  crypto_rwa: `Bạn là nhà quản lý danh mục Crypto & Real World Assets (RWA) Web3. Dựa trên bối cảnh thanh khoản vĩ mô toàn cầu:
{{NEWS_ITEMS}}

Trọng tâm phân tích:
1. Đánh giá chu kỳ thanh khoản toàn cầu (Global M2 Liquidity) và tác động trực tiếp đến Bitcoin & thị trường Crypto.
2. Phân khúc RWA (Real World Assets): Phân tích chiến lược phân bổ vào Treasury RWA (ONDO, USDY), Gold RWA (PAXG, XAUT) và Private Credit (CFG, MPL).
3. So sánh lợi suất Stablecoin staking/lending (5-10% APY) so với gửi tiết kiệm ngân hàng truyền thống (VND).
4. Đề xuất danh mục tài sản số phòng thủ và chiến lược tối ưu dòng tiền on-chain.`
}

function authHeader() {
  const token = localStorage.getItem('token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

async function loadPrompt() {
  try {
    const r = await fetch('/api/settings', { headers: authHeader() })
    if (r.ok) {
      const data = await r.json()
      if (data.ai_prompt_template && typeof data.ai_prompt_template === 'string' && data.ai_prompt_template.trim()) {
        promptContent.value = data.ai_prompt_template
        activePreset.value = ''
      } else {
        promptContent.value = defaultPrompt
        activePreset.value = 'default'
      }
    } else {
      promptContent.value = defaultPrompt
      activePreset.value = 'default'
    }
  } catch (e) {
    console.error('Error loading AI prompt settings:', e)
    promptContent.value = defaultPrompt
    activePreset.value = 'default'
  }
}

function applyPreset(key) {
  if (presets[key]) {
    promptContent.value = presets[key]
    activePreset.value = key
    showMessage(`Đã áp dụng mẫu: ${getPresetName(key)}`, 'success')
  }
}

function getPresetName(key) {
  switch (key) {
    case 'default': return 'Toàn diện vĩ mô'
    case 'vn_market': return 'CK & BĐS Việt Nam'
    case 'forex_gold': return 'Vàng & Forex'
    case 'crypto_rwa': return 'Crypto & RWA'
    default: return key
  }
}

function resetToDefault() {
  promptContent.value = defaultPrompt
  activePreset.value = 'default'
  showMessage('Đã khôi phục prompt về mặc định', 'success')
}

async function copyPrompt() {
  try {
    await navigator.clipboard.writeText(promptContent.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
    showMessage('Đã sao chép prompt vào clipboard', 'success')
  } catch (e) {
    console.error('Copy failed:', e)
  }
}

function showMessage(msg, type = 'success') {
  statusMessage.value = msg
  statusType.value = type
  setTimeout(() => {
    if (statusMessage.value === msg) {
      statusMessage.value = ''
    }
  }, 3500)
}

async function savePrompt(andRun = false) {
  if (andRun) {
    running.value = true
  } else {
    saving.value = true
  }
  
  try {
    const res = await fetch('/api/settings/update', {
      method: 'POST',
      headers: {
        ...authHeader(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        key: 'ai_prompt_template',
        value: promptContent.value
      })
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.message || 'Lưu thất bại')
    }

    emit('saved', promptContent.value)
    showMessage('Đã lưu cấu hình prompt thành công!', 'success')

    if (andRun) {
      close()
      emit('run-analysis')
    }
  } catch (e) {
    console.error('Save prompt error:', e)
    showMessage(`Lỗi lưu prompt: ${e.message}`, 'error')
  } finally {
    saving.value = false
    running.value = false
  }
}

function close() {
  emit('update:modelValue', false)
  statusMessage.value = ''
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    loadPrompt()
    statusMessage.value = ''
  }
})

onMounted(() => {
  if (props.modelValue) {
    loadPrompt()
  }
})
</script>

<style scoped>
/* ==========================================================================
   AI PROMPT MODAL – DARK CYBER GLASSMORPHISM DESIGN
   ========================================================================== */

.ai-prompt-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 2050;
  background: rgba(6, 9, 18, 0.82);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  animation: modalFadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.ai-prompt-modal-container {
  background: linear-gradient(170deg, #131929 0%, #0c101c 100%);
  border: 1px solid rgba(0, 242, 254, 0.22);
  border-radius: 20px;
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.75), 0 0 40px rgba(0, 242, 254, 0.08);
  width: 100%;
  max-width: 860px;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modalSlideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalSlideUp {
  from { transform: translateY(22px) scale(0.98); }
  to { transform: translateY(0) scale(1); }
}

/* ── Header ─────────────────────────────────────────────── */
.ai-modal-header {
  padding: 1.35rem 1.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.015);
}

.ai-modal-badge-icon {
  font-size: 1.5rem;
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.15) 0%, rgba(79, 172, 254, 0.05) 100%);
  border: 1px solid rgba(0, 242, 254, 0.3);
  border-radius: 12px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 15px rgba(0, 242, 254, 0.15);
}

.ai-modal-title {
  color: #f8fafc;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.ai-modal-subtitle {
  color: #94a3b8;
  font-size: 0.8rem;
  font-weight: 400;
}

.ai-close-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ai-close-btn:hover {
  color: #ffffff;
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.3);
}

/* ── Presets Bar ─────────────────────────────────────────── */
.ai-presets-bar {
  padding: 0.85rem 1.75rem;
  background: rgba(0, 0, 0, 0.28);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  gap: 0.85rem;
  flex-wrap: wrap;
}

.presets-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #cbd5e1;
  white-space: nowrap;
}

.presets-buttons {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.preset-chip {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  font-size: 0.78rem;
  font-weight: 500;
  padding: 0.35rem 0.8rem;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  outline: none;
}

.preset-chip:hover {
  background: rgba(0, 242, 254, 0.1);
  border-color: rgba(0, 242, 254, 0.35);
  color: #00f2fe;
  transform: translateY(-1px);
}

.preset-chip.active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.18) 0%, rgba(79, 172, 254, 0.12) 100%);
  border-color: #00f2fe;
  color: #00f2fe;
  font-weight: 600;
  box-shadow: 0 0 12px rgba(0, 242, 254, 0.22);
}

.preset-icon {
  font-size: 0.85rem;
}

/* ── Modal Body ─────────────────────────────────────────── */
.ai-modal-body {
  padding: 1.35rem 1.75rem;
  overflow-y: auto;
  flex: 1;
}

.ai-help-banner {
  background: rgba(0, 242, 254, 0.04);
  border: 1px solid rgba(0, 242, 254, 0.14);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  font-size: 0.82rem;
  line-height: 1.55;
  color: #cbd5e1;
  display: flex;
  align-items: flex-start;
}

.ai-help-banner code {
  background: rgba(0, 242, 254, 0.15);
  color: #38bdf8;
  padding: 0.15rem 0.4rem;
  border-radius: 5px;
  font-size: 0.78rem;
  font-family: 'JetBrains Mono', Consolas, monospace;
}

.ai-textarea {
  background: rgba(8, 12, 20, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 12px;
  color: #e2e8f0 !important;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, monospace;
  font-size: 0.84rem;
  line-height: 1.65;
  padding: 1rem 1.15rem;
  resize: vertical;
  min-height: 240px;
  max-height: 500px;
  transition: all 0.2s ease;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
}

.ai-textarea:focus {
  border-color: #00f2fe !important;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4), 0 0 0 3px rgba(0, 242, 254, 0.15) !important;
  outline: none;
}

.char-counter {
  position: absolute;
  bottom: 12px;
  right: 16px;
  font-size: 0.72rem;
  font-weight: 500;
  color: #94a3b8;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 2px 8px;
  border-radius: 6px;
  pointer-events: none;
  backdrop-filter: blur(4px);
}

.status-alert {
  font-size: 0.82rem;
  padding: 0.55rem 0.9rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  animation: modalFadeIn 0.2s ease;
}

.status-success {
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #34d399;
}

.status-error {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}

/* ── Footer Actions ──────────────────────────────────────── */
.ai-modal-footer {
  padding: 1.1rem 1.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.85rem;
  background: rgba(0, 0, 0, 0.2);
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

/* ── Unified Custom Button Styles ────────────────────────── */

/* 1. Ghost Action Buttons (Left) */
.btn-action-ghost {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #94a3b8;
  font-size: 0.82rem;
  font-weight: 500;
  padding: 0.5rem 0.95rem;
  border-radius: 9px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.2s ease;
  outline: none;
}

.btn-action-ghost:hover {
  background: rgba(255, 255, 255, 0.09);
  border-color: rgba(255, 255, 255, 0.22);
  color: #f1f5f9;
  transform: translateY(-1px);
}

.btn-action-ghost.copied {
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.4);
  color: #34d399;
}

/* 2. Close Button (Right) */
.btn-modal-close {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
  font-size: 0.82rem;
  font-weight: 500;
  padding: 0.5rem 1.1rem;
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
}

.btn-modal-close:hover {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.35);
  color: #f87171;
  transform: translateY(-1px);
}

/* 3. Save Button (Right) */
.btn-modal-save {
  background: rgba(0, 242, 254, 0.1);
  border: 1px solid #00f2fe;
  color: #00f2fe;
  font-size: 0.82rem;
  font-weight: 600;
  padding: 0.5rem 1.15rem;
  border-radius: 9px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  transition: all 0.2s ease;
  outline: none;
}

.btn-modal-save:hover:not(:disabled) {
  background: #00f2fe;
  color: #0c101c;
  box-shadow: 0 0 16px rgba(0, 242, 254, 0.4);
  transform: translateY(-1px);
}

.btn-modal-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 4. Save & Execute Button (Right) */
.btn-modal-execute {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: 1px solid #10b981;
  color: #ffffff;
  font-size: 0.82rem;
  font-weight: 600;
  padding: 0.5rem 1.25rem;
  border-radius: 9px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  transition: all 0.2s ease;
  outline: none;
  box-shadow: 0 2px 10px rgba(16, 185, 129, 0.25);
}

.btn-modal-execute:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  border-color: #34d399;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
  transform: translateY(-1px);
}

.btn-modal-execute:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 680px) {
  .ai-prompt-modal-container {
    max-height: 96vh;
    border-radius: 16px;
  }
  
  .ai-modal-header,
  .ai-presets-bar,
  .ai-modal-body,
  .ai-modal-footer {
    padding-left: 1.15rem;
    padding-right: 1.15rem;
  }
  
  .ai-modal-footer {
    flex-direction: column;
    align-items: stretch;
  }
  
  .footer-left,
  .footer-right {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
