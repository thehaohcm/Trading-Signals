<template>
  <div v-if="modelValue" class="ai-prompt-modal-overlay" @click.self="close">
    <div class="ai-prompt-modal-container">
      <!-- Header -->
      <div class="ai-modal-header">
        <div class="d-flex align-items-center gap-3">
          <div class="ai-modal-badge-icon">🤖</div>
          <div>
            <h4 class="ai-modal-title mb-0">Trung tâm Cấu hình AI Prompts</h4>
            <span class="ai-modal-subtitle">Tùy chỉnh toàn bộ hệ thống Prompt của AI trên nền tảng</span>
          </div>
        </div>
        <button class="ai-close-btn" @click="close" title="Đóng modal">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <!-- Main Category Tabs -->
      <div class="ai-category-tabs">
        <button 
          type="button" 
          :class="['category-tab-btn', { active: currentCategory === 'theses' }]"
          @click="switchCategory('theses')"
        >
          <span class="tab-icon">🧠</span>
          <div class="text-start">
            <div class="tab-title">Platform Intelligence</div>
            <div class="tab-desc">Nhận định Vĩ mô & Danh mục</div>
          </div>
        </button>

        <button 
          type="button" 
          :class="['category-tab-btn', { active: currentCategory === 'world_state' }]"
          @click="switchCategory('world_state')"
        >
          <span class="tab-icon">🌐</span>
          <div class="text-start">
            <div class="tab-title">Current World State</div>
            <div class="tab-desc">Cập nhật Trạng thái OSINT</div>
          </div>
        </button>

        <button 
          type="button" 
          :class="['category-tab-btn', { active: currentCategory === 'extraction' }]"
          @click="switchCategory('extraction')"
        >
          <span class="tab-icon">⚡</span>
          <div class="text-start">
            <div class="tab-title">Signal Extraction</div>
            <div class="tab-desc">Trích xuất Tín hiệu từ Tin tức</div>
          </div>
        </button>
      </div>

      <!-- Presets Toolbar (Only for categories with presets) -->
      <div class="ai-presets-bar" v-if="currentPresetsList.length > 0">
        <span class="presets-label"><i class="bi bi-stars text-warning me-1"></i>Mẫu gợi ý:</span>
        <div class="presets-buttons">
          <button 
            v-for="p in currentPresetsList"
            :key="p.key"
            type="button" 
            :class="['preset-chip', { active: activePresetKey === p.key }]" 
            @click="applyPreset(p.key)"
            :title="p.description"
          >
            <span class="preset-icon">{{ p.icon }}</span>
            <span>{{ p.label }}</span>
          </button>
        </div>
      </div>

      <!-- Body -->
      <div class="ai-modal-body">
        <div class="ai-help-banner mb-3">
          <i class="bi bi-info-circle-fill text-info me-2 fs-6"></i>
          <span>
            {{ categoryHelpText }}
          </span>
        </div>

        <!-- Module Selection Box (Tùy chọn bật/tắt từng mục để tiết kiệm Token & Chi phí) -->
        <div class="ai-modules-selection-box mb-3">
          <div class="d-flex align-items-center justify-content-between mb-2 flex-wrap gap-2">
            <div class="modules-heading">
              <i class="bi bi-toggles text-info me-1"></i>
              <span>Chọn các mục phân tích (Bỏ chọn để AI bỏ qua, tiết kiệm 50-70% Token & Chi phí):</span>
            </div>
            <div class="modules-token-badge">
              <i class="bi bi-speedometer2 text-warning me-1"></i>
              <span>{{ activeModulesCostEstimate }}</span>
            </div>
          </div>

          <div class="modules-chips-grid">
            <div 
              v-for="item in currentCategoryModulesList" 
              :key="item.key"
              :class="['module-select-card', { active: isModuleActive(item.key) }]"
              @click="toggleModule(item.key)"
            >
              <div class="module-card-header">
                <span class="module-check-icon">
                  <i :class="isModuleActive(item.key) ? 'bi bi-check-square-fill text-info' : 'bi bi-square text-secondary'"></i>
                </span>
                <span class="module-icon">{{ item.icon }}</span>
                <span class="module-name">{{ item.label }}</span>
              </div>
              <div class="module-saving">{{ item.saving }}</div>
            </div>
          </div>
        </div>

        <div class="position-relative">
          <div class="textarea-label mb-1 d-flex justify-content-between align-items-center">
            <span class="text-secondary small"><i class="bi bi-pencil-square me-1"></i>Prompt chỉ dẫn / Góc nhìn phân tích tùy chỉnh:</span>
            <span class="char-counter">
              {{ (activePromptText || '').length.toLocaleString() }} ký tự
            </span>
          </div>
          <textarea
            v-model="activePromptText"
            class="ai-textarea form-control"
            rows="10"
            :placeholder="`Nhập prompt tùy chỉnh cho ${currentCategoryName}...`"
            spellcheck="false"
            @input="activePresetKey = ''"
          ></textarea>
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
            @click="saveCurrentPrompt(false)"
            title="Lưu cấu hình prompt & modules vào hệ thống"
          >
            <span v-if="saving" class="spinner-border spinner-border-sm" role="status"></span>
            <i v-else class="bi bi-floppy2-fill"></i>
            <span>Lưu Cấu Hình</span>
          </button>
          <button 
            type="button" 
            class="btn-modal-execute" 
            :disabled="saving || running"
            @click="saveCurrentPrompt(true)"
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
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'saved', 'run-analysis'])

const currentCategory = ref('theses') // 'theses' | 'world_state' | 'extraction'
const activePresetKey = ref('default')
const saving = ref(false)
const running = ref(false)
const copied = ref(false)
const statusMessage = ref('')
const statusType = ref('success')

// Local prompt states for each category
const prompts = ref({
  theses: '',
  world_state: '',
  extraction: ''
})

// Module toggles state per category
const analysisModules = ref({
  theses: {
    real_estate_vn: true,
    cash_allocation: true,
    rwa_strategy: true,
    forex_pairs: true,
    asset_weights: true
  },
  world_state: {
    central_banks: true,
    energy_commodities: true,
    global_liquidity: true
  },
  extraction: {
    policy: true,
    liquidity: true,
    inflation: true,
    growth: true,
    sentiment: true
  }
})

/* ── Module Definitions ── */
const modulesDefinition = {
  theses: [
    { key: 'real_estate_vn', label: 'BĐS Việt Nam', icon: '🏢', saving: 'Tiết kiệm ~600 tokens' },
    { key: 'cash_allocation', label: 'Tiền mặt & Lãi suất VND/USD', icon: '💵', saving: 'Tiết kiệm ~350 tokens' },
    { key: 'rwa_strategy', label: 'Tài sản Phòng thủ & RWA', icon: '🛡️', saving: 'Tiết kiệm ~250 tokens' },
    { key: 'forex_pairs', label: 'Khuyến nghị Cặp tiền Forex', icon: '💱', saving: 'Tiết kiệm ~200 tokens' },
    { key: 'asset_weights', label: 'Tăng / Giảm Tỷ trọng', icon: '⚖️', saving: 'Tiết kiệm ~150 tokens' }
  ],
  world_state: [
    { key: 'central_banks', label: 'Ngân hàng TW (FED, SBV, ECB...)', icon: '🏛️', saving: 'Tiết kiệm ~300 tokens' },
    { key: 'energy_commodities', label: 'Năng lượng & Vàng (OPEC, Oil)', icon: '🛢️', saving: 'Tiết kiệm ~250 tokens' },
    { key: 'global_liquidity', label: 'Thanh khoản & Vĩ mô', icon: '🌊', saving: 'Tiết kiệm ~200 tokens' }
  ],
  extraction: [
    { key: 'policy', label: 'Chính sách & Lãi suất', icon: '📜', saving: 'Nhóm Policy' },
    { key: 'liquidity', label: 'Thanh khoản & Dòng vốn', icon: '💧', saving: 'Nhóm Liquidity' },
    { key: 'inflation', label: 'Lạm phát & CPI', icon: '📈', saving: 'Nhóm Inflation' },
    { key: 'growth', label: 'Tăng trưởng & Việc làm', icon: '🏭', saving: 'Nhóm Growth' },
    { key: 'sentiment', label: 'Tâm lý thị trường', icon: '📊', saving: 'Nhóm Sentiment' }
  ]
}

/* ── 1. Default Prompts ── */
const defaultThesesPrompt = `Bạn là một nhà quản lý quỹ định lượng (Quant Fund Manager) và chuyên gia phân tích chu kỳ dòng tiền tài chính vĩ mô toàn cầu & Việt Nam.
Nhiệm vụ của bạn là dựa trên các tín hiệu vĩ mô thực tế, lãi suất và các cảnh báo kích hoạt để đưa ra nhận định vĩ mô cốt lõi và chiến lược phân bổ danh mục tài sản tối ưu.`

const defaultWorldStatePrompt = `Bạn là AI Quản lý World State cho nền tảng Macro Intelligence.
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
3. NGƯỠNG THAY ĐỔI: Chỉ đề xuất thay đổi khi có dữ liệu/phát biểu chính sách mới rõ ràng có độ tin cậy cao (confidence >= 0.75). Nếu dữ liệu mới trùng khớp hoặc không đủ trọng số, trả về proposed_changes rỗng [].`

const defaultExtractionPrompt = `Bạn là chuyên gia nghiên cứu định lượng (Quant Researcher) và phân tích kinh tế vĩ mô.
Nhiệm vụ: Phân tích nội dung tin tức được cung cấp và trích xuất các tín hiệu kinh tế vĩ mô có giá trị.

YÊU CẦU QUAN TRỌNG:
1. Tập trung tuyệt đối vào dữ liệu thực tế (Hard Data), phát biểu chính sách chính thức hoặc sự kiện kinh tế đã diễn ra.
2. Trường 'reason' và 'signal' BẮT BUỘC viết bằng Tiếng Việt súc tích.
3. Phân loại trường 'category' CHỈ ĐƯỢC CHỌN trong các nhóm: Policy, Liquidity, Inflation, Growth, Market Sentiment.
4. LỌC TIN RÁC: Nếu bản tin là tin đồn vô căn cứ, giật gân, quảng cáo hoặc không chứa thông tin vĩ mô cụ thể, BẮT BUỘC trả về danh sách tín hiệu rỗng: {"signals": []}.`

/* ── 2. Presets Map ── */
const thesesPresets = {
  default: { 
    key: 'default', 
    label: 'Toàn diện vĩ mô', 
    icon: '🌐', 
    description: 'Nhận định vĩ mô cân bằng toàn diện', 
    prompt: defaultThesesPrompt 
  },
  vn_market: {
    key: 'vn_market', 
    label: 'CK & BĐS Việt Nam', 
    icon: '🇻🇳', 
    description: 'Ưu tiên nhóm ngành chứng khoán VN & Bất động sản',
    prompt: `Bạn là chuyên gia kinh tế trưởng tập trung sâu vào thị trường tài chính Việt Nam. Hãy phân tích các tín hiệu vĩ mô quốc tế và trong nước.
Trọng tâm phân tích:
1. Tác động của chính sách tiền tệ NHNN (SBV), tỷ giá USD/VND và thanh khoản hệ thống liên ngân hàng đến TTCK Việt Nam.
2. Đánh giá nhóm ngành cổ phiếu dẫn dắt (Bất động sản, Ngân hàng, Chứng khoán, Thép, Bán lẻ, Xuất khẩu) có điểm mua an toàn.
3. Thị trường Bất động sản Việt Nam: Triển vọng phân khúc chung cư, đất nền ven đô, BĐS công nghiệp; gợi ý các dự án hoặc khu vực có dòng tiền thật và tiềm năng tăng trưởng.
4. Quản trị rủi ro danh mục và khuyến nghị phân bổ tỷ trọng Tiền mặt / Cổ phiếu / Vàng / BĐS.`
  },
  forex_gold: {
    key: 'forex_gold', 
    label: 'Vàng & Forex', 
    icon: '🥇', 
    description: 'Tập trung DXY, Vàng thế giới, Lợi suất US & Forex',
    prompt: `Bạn là chuyên gia giao dịch FX & Kim loại quý hàng đầu thế giới. Dựa trên các dữ liệu vĩ mô và cảnh báo kích hoạt.
Trọng tâm phân tích:
1. Xu hướng DXY (Chỉ số Dollar) và Lợi suất trái phiếu Mỹ (US02Y, US10Y, US30Y) - Đánh giá kỳ vọng lãi suất Fed (Hawkish vs Dovish).
2. Phân tích giá Vàng (XAU/USD) & Dầu thô (WTI/Brent) dưới góc nhìn địa chính trị và lạm phát.
3. Đề xuất chi tiết chiến lược giao dịch FX cho các cặp chính (EURUSD, GBPUSD, USDJPY, USDCAD, AUDUSD, USDCHF) với hướng đi Long/Short rõ ràng.
4. Khuyến nghị phân bổ dòng tiền nhàn rỗi và các kênh trú ẩn rủi ro an toàn nhất.`
  },
  crypto_rwa: {
    key: 'crypto_rwa', 
    label: 'Crypto & RWA', 
    icon: '⚡', 
    description: 'Tập trung Crypto & Token RWA phòng thủ',
    prompt: `Bạn là nhà quản lý danh mục Crypto & Real World Assets (RWA) Web3. Dựa trên bối cảnh thanh khoản vĩ mô toàn cầu.
Trọng tâm phân tích:
1. Đánh giá chu kỳ thanh khoản toàn cầu (Global M2 Liquidity) và tác động trực tiếp đến Bitcoin & thị trường Crypto.
2. Phân khúc RWA (Real World Assets): Phân tích chiến lược phân bổ vào Treasury RWA (ONDO, USDY), Gold RWA (PAXG, XAUT) và Private Credit (CFG, MPL).
3. So sánh lợi suất Stablecoin staking/lending so với gửi tiết kiệm ngân hàng truyền thống (VND).
4. Đề xuất danh mục tài sản số phòng thủ và chiến lược tối ưu dòng tiền on-chain.`
  }
}

/* ── Computed Properties ── */
const currentSettingKey = computed(() => {
  if (currentCategory.value === 'theses') return 'ai_prompt_template'
  if (currentCategory.value === 'world_state') return 'ai_world_state_prompt'
  if (currentCategory.value === 'extraction') return 'ai_signal_extraction_prompt'
  return 'ai_prompt_template'
})

const currentCategoryName = computed(() => {
  if (currentCategory.value === 'theses') return 'Platform Intelligence'
  if (currentCategory.value === 'world_state') return 'Current World State'
  if (currentCategory.value === 'extraction') return 'Signal Extraction'
  return 'AI'
})

const categoryHelpText = computed(() => {
  if (currentCategory.value === 'theses') {
    return 'Prompt này định hướng AI khi tổng hợp dữ liệu vĩ mô, cảnh báo giá, lãi suất và đưa ra tư vấn danh mục đầu tư.'
  }
  if (currentCategory.value === 'world_state') {
    return 'Prompt này kiểm soát cách AI đánh giá sự thay đổi của Trạng thái Thế giới (OSINT) và chuẩn hóa ngôn ngữ sang Tiếng Việt.'
  }
  if (currentCategory.value === 'extraction') {
    return 'Prompt này hướng dẫn AI trích xuất các dữ liệu kinh tế vĩ mô cốt lõi từ các bài báo thô thành tín hiệu có cấu trúc.'
  }
  return ''
})

const currentPresetsList = computed(() => {
  if (currentCategory.value === 'theses') {
    return Object.values(thesesPresets)
  }
  return []
})

const currentCategoryModulesList = computed(() => {
  return modulesDefinition[currentCategory.value] || []
})

const activeModulesCostEstimate = computed(() => {
  const current = analysisModules.value[currentCategory.value] || {}
  const total = Object.keys(current).length
  const activeCount = Object.values(current).filter(Boolean).length
  if (activeCount === total) return 'Bật toàn bộ modules'
  if (activeCount === 0) return 'Đã tắt toàn bộ (Tiết kiệm tối đa)'
  return `Đang bật ${activeCount}/${total} modules (Tiết kiệm Token)`
})

const activePromptText = computed({
  get() {
    return prompts.value[currentCategory.value] || ''
  },
  set(val) {
    prompts.value[currentCategory.value] = val
  }
})

function isModuleActive(key) {
  const cat = currentCategory.value
  if (!analysisModules.value[cat]) return true
  return analysisModules.value[cat][key] !== false
}

function toggleModule(key) {
  const cat = currentCategory.value
  if (!analysisModules.value[cat]) {
    analysisModules.value[cat] = {}
  }
  analysisModules.value[cat][key] = !isModuleActive(key)
}

function authHeader() {
  const token = localStorage.getItem('token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

async function loadAllSettings() {
  try {
    const r = await fetch('/api/settings', { headers: authHeader() })
    if (r.ok) {
      const data = await r.json()
      // 1. Theses
      if (data.ai_prompt_template && typeof data.ai_prompt_template === 'string' && data.ai_prompt_template.trim()) {
        prompts.value.theses = data.ai_prompt_template
      } else {
        prompts.value.theses = defaultThesesPrompt
      }
      // 2. World State
      if (data.ai_world_state_prompt && typeof data.ai_world_state_prompt === 'string' && data.ai_world_state_prompt.trim()) {
        prompts.value.world_state = data.ai_world_state_prompt
      } else {
        prompts.value.world_state = defaultWorldStatePrompt
      }
      // 3. Extraction
      if (data.ai_signal_extraction_prompt && typeof data.ai_signal_extraction_prompt === 'string' && data.ai_signal_extraction_prompt.trim()) {
        prompts.value.extraction = data.ai_signal_extraction_prompt
      } else {
        prompts.value.extraction = defaultExtractionPrompt
      }
      // 4. Modules Selection
      if (data.ai_analysis_modules) {
        try {
          const parsed = typeof data.ai_analysis_modules === 'string' 
            ? jsonParseSafe(data.ai_analysis_modules) 
            : data.ai_analysis_modules
          if (parsed && typeof parsed === 'object') {
            analysisModules.value = {
              theses: { ...analysisModules.value.theses, ...(parsed.theses || {}) },
              world_state: { ...analysisModules.value.world_state, ...(parsed.world_state || {}) },
              extraction: { ...analysisModules.value.extraction, ...(parsed.extraction || {}) }
            }
          }
        } catch (err) {
          console.warn('Could not parse ai_analysis_modules:', err)
        }
      }
    } else {
      prompts.value.theses = defaultThesesPrompt
      prompts.value.world_state = defaultWorldStatePrompt
      prompts.value.extraction = defaultExtractionPrompt
    }
  } catch (e) {
    console.error('Error loading AI prompt settings:', e)
    prompts.value.theses = defaultThesesPrompt
    prompts.value.world_state = defaultWorldStatePrompt
    prompts.value.extraction = defaultExtractionPrompt
  }
}

function jsonParseSafe(str) {
  try {
    return JSON.parse(str)
  } catch {
    return null
  }
}

function switchCategory(cat) {
  currentCategory.value = cat
  activePresetKey.value = ''
  statusMessage.value = ''
}

function applyPreset(key) {
  if (thesesPresets[key]) {
    prompts.value.theses = thesesPresets[key].prompt
    activePresetKey.value = key
    showMessage(`Đã áp dụng mẫu: ${thesesPresets[key].label}`, 'success')
  }
}

function resetToDefault() {
  if (currentCategory.value === 'theses') {
    prompts.value.theses = defaultThesesPrompt
    activePresetKey.value = 'default'
    analysisModules.value.theses = {
      real_estate_vn: true,
      cash_allocation: true,
      rwa_strategy: true,
      forex_pairs: true,
      asset_weights: true
    }
  } else if (currentCategory.value === 'world_state') {
    prompts.value.world_state = defaultWorldStatePrompt
    analysisModules.value.world_state = {
      central_banks: true,
      energy_commodities: true,
      global_liquidity: true
    }
  } else if (currentCategory.value === 'extraction') {
    prompts.value.extraction = defaultExtractionPrompt
    analysisModules.value.extraction = {
      policy: true,
      liquidity: true,
      inflation: true,
      growth: true,
      sentiment: true
    }
  }
  showMessage(`Đã khôi phục prompt & modules ${currentCategoryName.value} về mặc định`, 'success')
}

async function copyPrompt() {
  try {
    await navigator.clipboard.writeText(activePromptText.value)
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

async function saveCurrentPrompt(andRun = false) {
  if (andRun) {
    running.value = true
  } else {
    saving.value = true
  }
  
  try {
    // 1. Save prompt text
    const resPrompt = await fetch('/api/settings/update', {
      method: 'POST',
      headers: {
        ...authHeader(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        key: currentSettingKey.value,
        value: activePromptText.value
      })
    })

    if (!resPrompt.ok) {
      const err = await resPrompt.json().catch(() => ({}))
      throw new Error(err.message || 'Lưu prompt thất bại')
    }

    // 2. Save modules selection
    await fetch('/api/settings/update', {
      method: 'POST',
      headers: {
        ...authHeader(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        key: 'ai_analysis_modules',
        value: JSON.stringify(analysisModules.value)
      })
    }).catch(e => console.warn('Could not save ai_analysis_modules:', e))

    emit('saved', { key: currentSettingKey.value, value: activePromptText.value })
    showMessage(`Đã lưu cấu hình ${currentCategoryName.value} thành công!`, 'success')

    if (andRun) {
      close()
      emit('run-analysis')
    }
  } catch (e) {
    console.error('Save prompt error:', e)
    showMessage(`Lỗi lưu cấu hình: ${e.message}`, 'error')
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
    loadAllSettings()
    statusMessage.value = ''
  }
})

onMounted(() => {
  if (props.modelValue) {
    loadAllSettings()
  }
})
</script>

<style scoped>
/* ==========================================================================
   AI PROMPT MODAL – UNIFIED CYBER GLASSMORPHISM DESIGN
   ========================================================================== */

.ai-prompt-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 2050;
  background: rgba(6, 9, 18, 0.85);
  backdrop-filter: blur(14px);
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
  border: 1px solid rgba(0, 242, 254, 0.25);
  border-radius: 20px;
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.8), 0 0 40px rgba(0, 242, 254, 0.1);
  width: 100%;
  max-width: 900px;
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

/* ── Main Category Tabs ──────────────────────────────────── */
.ai-category-tabs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  padding: 0.75rem 1.75rem;
  background: rgba(0, 0, 0, 0.35);
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

.category-tab-btn {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 0.65rem 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
}

.category-tab-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-1px);
}

.category-tab-btn.active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.14) 0%, rgba(79, 172, 254, 0.08) 100%);
  border-color: #00f2fe;
  box-shadow: 0 0 16px rgba(0, 242, 254, 0.18);
}

.category-tab-btn .tab-icon {
  font-size: 1.3rem;
}

.category-tab-btn .tab-title {
  color: #f1f5f9;
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1.2;
}

.category-tab-btn.active .tab-title {
  color: #00f2fe;
}

.category-tab-btn .tab-desc {
  color: #94a3b8;
  font-size: 0.7rem;
  margin-top: 2px;
}

/* ── Presets Bar ─────────────────────────────────────────── */
.ai-presets-bar {
  padding: 0.75rem 1.75rem;
  background: rgba(0, 0, 0, 0.2);
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
  padding: 1.25rem 1.75rem;
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

/* ── Modules Selection Box ──────────────────────────────── */
.ai-modules-selection-box {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(0, 242, 254, 0.18);
  border-radius: 12px;
  padding: 0.85rem 1rem;
}

.modules-heading {
  font-size: 0.8rem;
  font-weight: 600;
  color: #e2e8f0;
}

.modules-token-badge {
  font-size: 0.75rem;
  font-weight: 600;
  color: #facc15;
  background: rgba(250, 204, 21, 0.1);
  border: 1px solid rgba(250, 204, 21, 0.25);
  padding: 2px 8px;
  border-radius: 6px;
}

.modules-chips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.6rem;
  margin-top: 0.35rem;
}

.module-select-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 0.55rem 0.75rem;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.module-select-card:hover {
  background: rgba(0, 242, 254, 0.06);
  border-color: rgba(0, 242, 254, 0.3);
  transform: translateY(-1px);
}

.module-select-card.active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.12) 0%, rgba(79, 172, 254, 0.06) 100%);
  border-color: rgba(0, 242, 254, 0.5);
  box-shadow: 0 0 12px rgba(0, 242, 254, 0.12);
}

.module-card-header {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.module-check-icon {
  font-size: 0.95rem;
  line-height: 1;
  display: flex;
  align-items: center;
}

.module-icon {
  font-size: 0.95rem;
}

.module-name {
  font-size: 0.78rem;
  font-weight: 600;
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.module-select-card.active .module-name {
  color: #00f2fe;
}

.module-saving {
  font-size: 0.68rem;
  color: #94a3b8;
  padding-left: 1.45rem;
}

.module-select-card.active .module-saving {
  color: #38bdf8;
}

.textarea-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  max-height: 480px;
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

/* ── Custom Button Styles ────────────────────────────────── */

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
@media (max-width: 768px) {
  .ai-category-tabs {
    grid-template-columns: 1fr;
  }
  
  .ai-prompt-modal-container {
    max-height: 96vh;
    border-radius: 16px;
  }
  
  .ai-modal-header,
  .ai-category-tabs,
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
