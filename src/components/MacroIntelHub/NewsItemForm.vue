<template>
  <div class="news-form-container">
    <!-- Header with Title & Tab Switcher -->
    <div class="form-header">
      <div class="header-main">
        <h2 class="form-title">
          <span>{{ form.id ? '✏️ Chỉnh Sửa Tin Tức' : '📰 Thêm Tin Tức Vĩ Mô' }}</span>
        </h2>
        <p class="form-subtitle">Cập nhật dữ liệu và nhận định vĩ mô mới nhất vào hệ thống</p>
      </div>

      <!-- Tab Switcher (Only show for new items) -->
      <div v-if="!form.id" class="tab-switcher">
        <button 
          type="button" 
          @click="activeTab = 'manual'" 
          :class="['tab-btn', { active: activeTab === 'manual' }]"
        >
          <span class="tab-icon">📝</span>
          <span>Nhập thủ công</span>
        </button>
        <button 
          type="button" 
          @click="activeTab = 'youtube'" 
          :class="['tab-btn', { active: activeTab === 'youtube' }]"
        >
          <span class="tab-icon">🎥</span>
          <span>YouTube AI Extract</span>
          <span class="tab-badge">AI</span>
        </button>
      </div>
    </div>

    <!-- Group Selector (if groups provided) -->
    <div v-if="groups && groups.length > 0" class="form-group mb-3">
      <label class="form-label">
        <span>📂 Nhóm sự kiện / Chủ đề</span>
        <span class="required">*</span>
      </label>
      <select v-model="form.group_id" class="form-select custom-select" required>
        <option value="" disabled>-- Chọn nhóm sự kiện --</option>
        <option v-for="g in groups" :key="g.id" :value="g.id">
          {{ g.name }} {{ g.description ? `(${g.description})` : '' }}
        </option>
      </select>
    </div>

    <!-- ==================== TAB 2: YOUTUBE AI EXTRACT ==================== -->
    <div v-if="activeTab === 'youtube' && !form.id" class="youtube-tab-section">
      <div class="yt-input-card">
        <label class="form-label">
          <span>🔗 Link Video YouTube</span>
          <span class="required">*</span>
        </label>
        <div class="yt-input-wrapper">
          <input 
            v-model="youtubeUrl" 
            @input="onYoutubeUrlChange"
            placeholder="Dán link YouTube (VD: https://www.youtube.com/watch?v=... hoặc youtu.be/...)" 
            class="form-input yt-input"
            :disabled="aiLoading"
          />
          <button 
            type="button" 
            @click="fetchAndSummarizeYoutube" 
            :disabled="!isValidYoutubeUrl || aiLoading"
            class="yt-extract-btn"
          >
            <span v-if="aiLoading" class="spinner-border spinner-border-sm me-1" role="status"></span>
            <span v-else>⚡ Phân tích AI</span>
          </button>
        </div>
        <p class="yt-hint">
          Hỗ trợ link video dài, livestream recording, Shorts. Hệ thống sẽ bóc tách nội dung phụ đề và AI sẽ tóm tắt các luận điểm vĩ mô cốt lõi.
        </p>
      </div>

      <!-- YouTube Video Preview Card -->
      <div v-if="extractedVideoId" class="yt-preview-card">
        <div class="yt-thumbnail-wrapper">
          <img 
            :src="videoMetadata.thumbnail_url || `https://img.youtube.com/vi/${extractedVideoId}/hqdefault.jpg`" 
            alt="Thumbnail" 
            class="yt-thumbnail" 
          />
          <div class="yt-play-badge">▶ YouTube</div>
        </div>
        <div class="yt-meta-info">
          <div class="yt-channel-badge">
            <span>📺 {{ videoMetadata.video_author || 'YouTube Channel' }}</span>
          </div>
          <h4 class="yt-video-title">{{ videoMetadata.video_title || 'Video YouTube' }}</h4>
          <a :href="`https://www.youtube.com/watch?v=${extractedVideoId}`" target="_blank" rel="noopener noreferrer" class="yt-external-link">
            Mở video gốc ↗
          </a>
        </div>
      </div>

      <!-- AI Loading State -->
      <div v-if="aiLoading" class="ai-loading-box">
        <div class="ai-pulse-indicator"></div>
        <div class="ai-loading-text">
          <h5>{{ aiLoadingStep }}</h5>
          <p>Đang bóc tách transcript có timestamp và xử lý mô hình AI Vĩ mô...</p>
        </div>
      </div>

      <!-- AI Error Alert -->
      <div v-if="aiError" class="ai-error-alert">
        <span class="error-icon">⚠️</span>
        <div class="error-text">
          <strong>Không thể phân tích video:</strong>
          <p class="mb-0">{{ aiError }}</p>
        </div>
      </div>

      <!-- AI Success Alert -->
      <div v-if="aiExtractedSuccess" class="ai-success-alert">
        <span class="success-icon">✨</span>
        <div class="success-text">
          <strong>AI đã bóc tách & tóm tắt thành công!</strong>
          <p class="mb-0">Dữ liệu đã được điền vào form bên dưới. Bạn có thể kiểm tra và chỉnh sửa nội dung trước khi bấm lưu.</p>
        </div>
      </div>
    </div>

    <!-- ==================== COMMON / MANUAL FORM FIELDS ==================== -->
    <form @submit.prevent="onSubmit" class="news-main-form">
      <div class="form-group mb-3">
        <label class="form-label">
          <span>Tiêu đề tin tức</span>
          <span class="required">*</span>
        </label>
        <input 
          v-model="form.title" 
          required 
          placeholder="VD: FED giữ nguyên lãi suất ở mức 5.25% - 5.5%, phát tín hiệu thận trọng" 
          class="form-input" 
        />
      </div>

      <div class="form-group mb-3">
        <div class="label-with-hint">
          <label class="form-label mb-0">
            <span>Nội dung chi tiết & Nhận định</span>
            <span class="required">*</span>
          </label>
          <span class="text-hint">Hỗ trợ Bullet points & Markdown</span>
        </div>
        <textarea 
          v-model="form.content" 
          required 
          placeholder="Tóm tắt nội dung chi tiết, các số liệu kinh tế quan trọng, tác động tới thị trường Vàng, DXY, Cổ phiếu, BĐS..." 
          class="form-textarea" 
          rows="6"
        ></textarea>
      </div>

      <div class="form-row mb-3">
        <div class="form-group flex-1">
          <label class="form-label">
            <span>Nguồn tin (URL)</span>
          </label>
          <input 
            v-model="form.source_url" 
            placeholder="https://..." 
            class="form-input" 
          />
        </div>

        <div class="form-group flex-1">
          <label class="form-label">
            <span>Mức độ quan trọng</span>
            <span class="required">*</span>
          </label>
          <div class="importance-selector">
            <button 
              v-for="n in 5" 
              :key="n" 
              type="button" 
              @click="form.importance = n" 
              :class="['importance-btn', { active: form.importance === n }]"
            >
              {{ n }}⭐
            </button>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="form-actions">
        <button type="button" @click="handleCancel" class="form-btn cancel-btn">
          Hủy bỏ
        </button>
        <button 
          type="submit" 
          :disabled="!form.title || !form.content || !form.group_id || aiLoading" 
          class="form-btn submit-btn"
        >
          <span>{{ form.id ? '💾 Cập Nhật' : '💾 Thêm Tin Tức' }}</span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'

const props = defineProps({
  modelValue: Object,
  groups: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'cancel'])

const activeTab = ref('manual')
const youtubeUrl = ref('')
const extractedVideoId = ref('')
const aiLoading = ref(false)
const aiLoadingStep = ref('Đang kết nối...')
const aiError = ref('')
const aiExtractedSuccess = ref(false)

const videoMetadata = reactive({
  video_title: '',
  video_author: '',
  thumbnail_url: ''
})

const form = reactive({
  id: null,
  group_id: '',
  title: '',
  content: '',
  source_url: '',
  importance: 3,
  status: 'active'
})

// Regex for extracting YouTube ID
function extractYoutubeId(url) {
  if (!url) return null
  url = url.trim()
  const patterns = [
    /(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})/,
    /(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})/,
    /(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})/,
    /(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,
    /(?:https?:\/\/)?(?:www\.)?youtube\.com\/live\/([a-zA-Z0-9_-]{11})/
  ]
  for (const p of patterns) {
    const match = url.match(p)
    if (match && match[1]) return match[1]
  }
  return null
}

const isValidYoutubeUrl = computed(() => {
  return !!extractYoutubeId(youtubeUrl.value)
})

function onYoutubeUrlChange() {
  aiError.value = ''
  aiExtractedSuccess.value = false
  const vid = extractYoutubeId(youtubeUrl.value)
  if (vid) {
    extractedVideoId.value = vid
    videoMetadata.thumbnail_url = `https://img.youtube.com/vi/${vid}/hqdefault.jpg`
    // Fetch basic title via oEmbed
    fetch(`https://noembed.com/embed?url=${encodeURIComponent(`https://www.youtube.com/watch?v=${vid}`)}`)
      .then(res => res.json())
      .then(data => {
        if (data && data.title) {
          videoMetadata.video_title = data.title
          videoMetadata.video_author = data.author_name || 'YouTube'
        }
      })
      .catch(() => {})
  } else {
    extractedVideoId.value = ''
    videoMetadata.video_title = ''
    videoMetadata.video_author = ''
    videoMetadata.thumbnail_url = ''
  }
}

async function fetchAndSummarizeYoutube() {
  const vid = extractYoutubeId(youtubeUrl.value)
  if (!vid) {
    aiError.value = 'URL YouTube không hợp lệ. Vui lòng kiểm tra lại.'
    return
  }

  aiLoading.value = true
  aiError.value = ''
  aiExtractedSuccess.value = false
  aiLoadingStep.value = 'Đang trích xuất transcript & timestamps...'

  try {
    const token = localStorage.getItem('token') || ''
    const headers = { 'Content-Type': 'application/json' }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    aiLoadingStep.value = 'AI đang phân tích tác động vĩ mô & tóm tắt...'

    const response = await fetch('/api/news-items/youtube-summary', {
      method: 'POST',
      headers,
      body: JSON.stringify({ url: youtubeUrl.value })
    })

    const rawText = await response.text()
    let data = {}
    try {
      data = JSON.parse(rawText)
    } catch {
      data = { message: rawText }
    }

    if (!response.ok) {
      const errMsg = data.message || data.error || rawText || `Lỗi ${response.status}: ${response.statusText}`
      throw new Error(errMsg)
    }

    // Populate form fields
    if (data.title) form.title = data.title
    if (data.summary) form.content = data.summary
    if (data.importance) form.importance = Number(data.importance)
    form.source_url = data.source_url || `https://www.youtube.com/watch?v=${vid}`

    if (data.video_title) videoMetadata.video_title = data.video_title
    if (data.video_author) videoMetadata.video_author = data.video_author
    if (data.thumbnail_url) videoMetadata.thumbnail_url = data.thumbnail_url

    aiExtractedSuccess.value = true
  } catch (err) {
    console.error('YouTube summary failed:', err)
    aiError.value = err.message || 'Không thể lấy dữ liệu phân tích từ video này.'
  } finally {
    aiLoading.value = false
  }
}

watch(() => props.modelValue, val => {
  if (val) {
    Object.assign(form, val)
    if (!form.group_id && props.groups && props.groups.length > 0) {
      form.group_id = props.groups[0].id
    }
  } else if (props.groups && props.groups.length > 0) {
    form.group_id = props.groups[0].id
  }
}, { immediate: true })

function onSubmit() {
  if (!form.group_id) {
    alert('Vui lòng chọn nhóm sự kiện')
    return
  }
  emit('submit', { ...form })
}

function handleCancel() {
  emit('cancel')
}
</script>

<style scoped>
.news-form-container {
  width: 100%;
}

.form-header {
  margin-bottom: 1.25rem;
  padding-right: 2.5rem;
}

.form-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: #f8fafc;
  margin: 0 0 0.35rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-subtitle {
  color: #94a3b8;
  font-size: 0.88rem;
  margin: 0;
}

/* Tab Switcher */
.tab-switcher {
  display: flex;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 4px;
  margin-top: 1rem;
  gap: 4px;
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.tab-btn:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.04);
}

.tab-btn.active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.3) 100%);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.4);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.tab-badge {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #000;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 9999px;
  text-transform: uppercase;
}

/* Form inputs & styles */
.form-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 600;
  color: #cbd5e1;
  margin-bottom: 0.45rem;
  font-size: 0.9rem;
}

.required {
  color: #f87171;
}

.label-with-hint {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.45rem;
}

.text-hint {
  font-size: 0.78rem;
  color: #64748b;
}

.form-input,
.form-textarea,
.custom-select {
  width: 100%;
  padding: 0.7rem 0.9rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  font-size: 0.92rem;
  font-family: inherit;
  background: rgba(15, 23, 42, 0.6);
  color: #f1f5f9;
  transition: all 0.2s;
  outline: none;
}

.form-input:focus,
.form-textarea:focus,
.custom-select:focus {
  border-color: #3b82f6;
  background: rgba(15, 23, 42, 0.9);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.custom-select option {
  background: #0f172a;
  color: #f8fafc;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.flex-1 {
  flex: 1;
}

/* YouTube Tab Section */
.youtube-tab-section {
  background: rgba(30, 41, 59, 0.4);
  border: 1px dashed rgba(239, 68, 68, 0.3);
  border-radius: 12px;
  padding: 1.1rem;
  margin-bottom: 1.25rem;
}

.yt-input-wrapper {
  display: flex;
  gap: 0.5rem;
}

.yt-input {
  flex: 1;
  border-color: rgba(239, 68, 68, 0.3);
}

.yt-input:focus {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
}

.yt-extract-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.65rem 1.1rem;
  font-weight: 700;
  font-size: 0.88rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.yt-extract-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.35);
  transform: translateY(-1px);
}

.yt-extract-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.yt-hint {
  font-size: 0.78rem;
  color: #94a3b8;
  margin: 0.45rem 0 0 0;
  line-height: 1.4;
}

/* Video Preview Card */
.yt-preview-card {
  display: flex;
  gap: 0.9rem;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 0.75rem;
  margin-top: 0.85rem;
  align-items: center;
}

.yt-thumbnail-wrapper {
  position: relative;
  width: 110px;
  height: 65px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}

.yt-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.yt-play-badge {
  position: absolute;
  bottom: 3px;
  right: 3px;
  background: rgba(0, 0, 0, 0.75);
  color: #ff4d4f;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
}

.yt-meta-info {
  flex: 1;
  min-width: 0;
}

.yt-channel-badge {
  font-size: 0.75rem;
  color: #38bdf8;
  font-weight: 600;
  margin-bottom: 0.2rem;
}

.yt-video-title {
  font-size: 0.86rem;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0 0 0.25rem 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.3;
}

.yt-external-link {
  font-size: 0.75rem;
  color: #60a5fa;
  text-decoration: none;
}

.yt-external-link:hover {
  text-decoration: underline;
}

/* AI State Alerts */
.ai-loading-box {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  padding: 0.85rem 1rem;
  margin-top: 0.85rem;
}

.ai-pulse-indicator {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #3b82f6;
  box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
  animation: pulse-ring 1.5s infinite;
  flex-shrink: 0;
}

@keyframes pulse-ring {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(59, 130, 246, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
}

.ai-loading-text h5 {
  font-size: 0.88rem;
  font-weight: 700;
  color: #93c5fd;
  margin: 0 0 0.15rem 0;
}

.ai-loading-text p {
  font-size: 0.78rem;
  color: #cbd5e1;
  margin: 0;
}

.ai-error-alert {
  display: flex;
  gap: 0.6rem;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.35);
  border-radius: 8px;
  padding: 0.75rem 0.9rem;
  margin-top: 0.85rem;
  color: #fca5a5;
  font-size: 0.85rem;
}

.ai-success-alert {
  display: flex;
  gap: 0.6rem;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  border-radius: 8px;
  padding: 0.75rem 0.9rem;
  margin-top: 0.85rem;
  color: #6ee7b7;
  font-size: 0.85rem;
}

/* Importance Stars */
.importance-selector {
  display: flex;
  gap: 0.35rem;
}

.importance-btn {
  flex: 1;
  padding: 0.6rem 0.4rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.6);
  color: #94a3b8;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s;
}

.importance-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #f1f5f9;
}

.importance-btn.active {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.25);
}

/* Actions */
.form-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.form-btn {
  padding: 0.65rem 1.35rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.submit-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.submit-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(37, 99, 235, 0.4);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #f1f5f9;
}

@media (max-width: 640px) {
  .form-row {
    flex-direction: column;
    gap: 0.75rem;
  }
  .yt-input-wrapper {
    flex-direction: column;
  }
  .yt-extract-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
