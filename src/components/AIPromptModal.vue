<template>
  <div v-if="modelValue" class="ai-prompt-modal-overlay" @click.self="close">
    <div class="ai-prompt-modal-container">
      <!-- Header -->
      <div class="ai-modal-header">
        <div class="d-flex align-items-center gap-2">
          <div class="ai-modal-badge-icon">🤖</div>
          <div>
            <h4 class="ai-modal-title mb-0">Chỉnh sửa Prompt AI Platform Intelligence</h4>
            <span class="ai-modal-subtitle">Tùy chỉnh chỉ dẫn và logic phân tích vĩ mô của AI</span>
          </div>
        </div>
        <button class="ai-close-btn" @click="close" title="Đóng">✕</button>
      </div>

      <!-- Presets Toolbar -->
      <div class="ai-presets-bar">
        <span class="presets-label"><i class="bi bi-stars text-warning me-1"></i>Mẫu gợi ý:</span>
        <div class="presets-buttons">
          <button 
            type="button" 
            class="preset-chip" 
            @click="applyPreset('default')"
            title="Nhận định vĩ mô cân bằng toàn diện"
          >
            🌐 Toàn diện vĩ mô
          </button>
          <button 
            type="button" 
            class="preset-chip" 
            @click="applyPreset('vn_market')"
            title="Ưu tiên nhóm ngành chứng khoán VN & Bất động sản"
          >
            🇻🇳 CK & BĐS Việt Nam
          </button>
          <button 
            type="button" 
            class="preset-chip" 
            @click="applyPreset('forex_gold')"
            title="Tập trung DXY, Vàng thế giới, Lợi suất US & Forex"
          >
            🥇 Vàng & Forex
          </button>
          <button 
            type="button" 
            class="preset-chip" 
            @click="applyPreset('crypto_rwa')"
            title="Tập trung Crypto & Token RWA phòng thủ"
          >
            ⚡ Crypto & RWA
          </button>
        </div>
      </div>

      <!-- Body -->
      <div class="ai-modal-body">
        <div class="ai-help-banner mb-3">
          <i class="bi bi-info-circle-fill text-info me-2"></i>
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
          ></textarea>
          
          <div class="char-counter">
            {{ promptContent.length }} ký tự
          </div>
        </div>

        <div v-if="statusMessage" :class="['status-alert mt-2', statusType === 'success' ? 'status-success' : 'status-error']">
          <i :class="statusType === 'success' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill'" class="me-1"></i>
          {{ statusMessage }}
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="ai-modal-footer">
        <div class="footer-left">
          <button 
            type="button" 
            class="stk-btn stk-btn--outline d-flex align-items-center gap-1 text-muted" 
            @click="resetToDefault"
            title="Khôi phục về prompt ban đầu của hệ thống"
          >
            <i class="bi bi-arrow-counterclockwise"></i>
            <span>Mặc định</span>
          </button>
          <button 
            type="button" 
            class="stk-btn stk-btn--outline d-flex align-items-center gap-1" 
            @click="copyPrompt"
            title="Sao chép nội dung prompt vào clipboard"
          >
            <i :class="copied ? 'bi bi-check2 text-success' : 'bi bi-clipboard'"></i>
            <span>{{ copied ? 'Đã chép' : 'Sao chép' }}</span>
          </button>
        </div>

        <div class="footer-right d-flex gap-2">
          <button 
            type="button" 
            class="stk-btn stk-btn--outline" 
            @click="close"
          >
            Đóng
          </button>
          <button 
            type="button" 
            class="stk-btn btn-save d-flex align-items-center gap-1" 
            :disabled="saving || running"
            @click="savePrompt(false)"
          >
            <span v-if="saving" class="spinner-border spinner-border-sm" role="status"></span>
            <i v-else class="bi bi-floppy"></i>
            <span>Lưu Prompt</span>
          </button>
          <button 
            type="button" 
            class="stk-btn btn-save-run d-flex align-items-center gap-1" 
            :disabled="saving || running"
            @click="savePrompt(true)"
            title="Lưu prompt mới và kích hoạt AI phân tích ngay lập tức"
          >
            <span v-if="running" class="spinner-border spinner-border-sm" role="status"></span>
            <i v-else class="bi bi-play-circle-fill"></i>
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
const saving = ref(false)
const running = ref(false)
const copied = ref(false)
const statusMessage = ref('')
const statusType = ref('success')

const defaultPrompt = `Bạn là chuyên gia phân tích vĩ mô và nhà quản lý quỹ định lượng. Hãy xác thực các sự kiện kinh tế vĩ mô đang diễn ra, đánh giá tác động của chúng đến thanh khoản toàn cầu và các thị trường tài chính:
{{NEWS_ITEMS}}

Yêu cầu phân tích:
1. Phân tích tác động chéo và chu kỳ dòng tiền (flow of funds) giữa: Vàng thế giới, Chỉ số USD (DXY), Lợi suất trái phiếu chính phủ Mỹ (US10Y, US30Y), Dầu mỏ, Crypto, Thị trường chứng khoán Mỹ.
2. Thị trường Việt Nam: Nhận định tác động đến VN-Index, các nhóm ngành hưởng lợi/chịu rủi ro, thị trường Bất động sản Việt Nam (phân khúc triển vọng, dự án cụ thể, rủi ro pháp lý/thanh khoản).
3. Lãi suất & Dòng tiền nhàn rỗi (Cash Allocation): So sánh lãi suất gửi tiết kiệm ngân hàng VN (VND) vs Lợi suất Stablecoin (USDT/USDC) trên sàn quốc tế để đưa ra tỷ trọng phân bổ tiền mặt tối ưu.
4. Đề xuất vị thế giao dịch Forex cụ thể (tối thiểu 3 cặp tiền với xu hướng Mua/Bán rõ ràng dựa trên DXY và tâm lý Risk-On / Risk-Off).
5. Chiến lược tài sản phòng thủ & RWA token (ONDO, USDY, PAXG, XAUT, CFG) nếu bối cảnh vĩ mô phù hợp.
6. Cảnh báo phân kỳ (Divergence) nếu có giữa tin tức vĩ mô và xu hướng kỹ thuật. Nếu có vốn khả dụng lúc này, nên phân bổ vào đâu là tối ưu nhất?`

const presets = {
  default: defaultPrompt,
  vn_market: `Bạn là chuyên gia kinh tế trưởng tập trung sâu vào thị trường tài chính Việt Nam. Hãy phân tích các tín hiệu vĩ mô quốc tế và trong nước:
{{NEWS_ITEMS}}

Trọng tâm phân tích:
1. Tác động của chính sách tiền tệ NHNN (SBV), tỷ giá USD/VND và thanh khoản hệ thống liên ngân hàng đến TTCK Việt Nam.
2. Đánh giá nhóm ngành cổ phiếu dẫn dắt (Bất động sản, Ngân hàng, Chứng khoán, Thép, Bán lẻ, Xuất khẩu) có điểm mua an toàn.
3. Thị trường Bất động sản Việt Nam: Triển vọng phân khúc chung cư, đất nền ven đô, BĐS công nghiệp; gợi ý các dự án hoặc khu vực có dòng tiền thật và tiềm năng tăng trưởng.
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
      } else {
        promptContent.value = defaultPrompt
      }
    } else {
      promptContent.value = defaultPrompt
    }
  } catch (e) {
    console.error('Error loading AI prompt settings:', e)
    promptContent.value = defaultPrompt
  }
}

function applyPreset(key) {
  if (presets[key]) {
    promptContent.value = presets[key]
    showMessage(`Đã áp dụng mẫu: ${key}`, 'success')
  }
}

function resetToDefault() {
  promptContent.value = defaultPrompt
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
.ai-prompt-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1050;
  background: rgba(10, 15, 29, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  animation: modalFadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.ai-prompt-modal-container {
  background: linear-gradient(165deg, #151d30 0%, #0d1220 100%);
  border: 1px solid rgba(0, 242, 254, 0.25);
  border-radius: 18px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6), 0 0 30px rgba(0, 242, 254, 0.08);
  width: 100%;
  max-width: 820px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modalSlideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalSlideUp {
  from {
    transform: translateY(20px) scale(0.98);
  }
  to {
    transform: translateY(0) scale(1);
  }
}

/* Header */
.ai-modal-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.02);
}

.ai-modal-badge-icon {
  font-size: 1.6rem;
  background: rgba(0, 242, 254, 0.1);
  border: 1px solid rgba(0, 242, 254, 0.25);
  border-radius: 12px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-modal-title {
  color: #f1f5f9;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.ai-modal-subtitle {
  color: #94a3b8;
  font-size: 0.8rem;
}

.ai-close-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.ai-close-btn:hover {
  color: #fff;
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
}

/* Presets Bar */
.ai-presets-bar {
  padding: 0.75rem 1.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.presets-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #94a3b8;
  white-space: nowrap;
}

.presets-buttons {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.preset-chip {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.65rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.preset-chip:hover {
  background: rgba(0, 242, 254, 0.12);
  border-color: rgba(0, 242, 254, 0.35);
  color: #00f2fe;
}

/* Body */
.ai-modal-body {
  padding: 1.25rem 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.ai-help-banner {
  background: rgba(0, 242, 254, 0.05);
  border: 1px solid rgba(0, 242, 254, 0.15);
  border-radius: 8px;
  padding: 0.65rem 0.9rem;
  font-size: 0.8rem;
  line-height: 1.5;
  color: #cbd5e1;
  display: flex;
  align-items: flex-start;
}

.ai-help-banner code {
  background: rgba(0, 242, 254, 0.15);
  color: #38bdf8;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.ai-textarea {
  background: rgba(10, 14, 23, 0.85) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 10px;
  color: #e2e8f0 !important;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, monospace;
  font-size: 0.85rem;
  line-height: 1.6;
  padding: 1rem;
  resize: vertical;
  min-height: 220px;
  max-height: 480px;
  transition: all 0.2s;
}

.ai-textarea:focus {
  border-color: #00f2fe !important;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15) !important;
}

.char-counter {
  position: absolute;
  bottom: 10px;
  right: 15px;
  font-size: 0.72rem;
  color: #64748b;
  background: rgba(15, 23, 42, 0.7);
  padding: 2px 6px;
  border-radius: 4px;
  pointer-events: none;
}

.status-alert {
  font-size: 0.8rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
}

.status-success {
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #34d399;
}

.status-error {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}

/* Footer */
.ai-modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  background: rgba(255, 255, 255, 0.02);
}

.footer-left {
  display: flex;
  gap: 0.5rem;
}

.btn-save {
  background: rgba(0, 242, 254, 0.12) !important;
  border: 1px solid #00f2fe !important;
  color: #00f2fe !important;
  font-weight: 600;
  font-size: 0.82rem;
  padding: 0.45rem 0.9rem;
  border-radius: 8px;
  transition: all 0.2s;
}

.btn-save:hover:not(:disabled) {
  background: #00f2fe !important;
  color: #0d1220 !important;
  box-shadow: 0 0 15px rgba(0, 242, 254, 0.4);
}

.btn-save-run {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  border: 1px solid #10b981 !important;
  color: #ffffff !important;
  font-weight: 600;
  font-size: 0.82rem;
  padding: 0.45rem 1rem;
  border-radius: 8px;
  transition: all 0.2s;
}

.btn-save-run:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
  box-shadow: 0 0 18px rgba(16, 185, 129, 0.45);
}

@media (max-width: 640px) {
  .ai-prompt-modal-container {
    max-height: 95vh;
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
