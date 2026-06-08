<template>
  <div class="hub-container-wrapper">
    <NavBar />
    <div class="macro-hub-container">
      <!-- Header -->
      <div class="hub-header">
        <div class="hub-header-left">
          <h1 class="hub-title">Macro Intelligence Hub</h1>
          <p class="hub-subtitle">Quß║ún l├╜ v├á ph├ón t├¡ch c├íc sß╗▒ kiß╗çn v─⌐ m├┤ ß║únh h╞░ß╗ƒng ─æß║┐n thß╗ï tr╞░ß╗¥ng</p>
          <div v-if="lastUpdatedText" class="hub-last-updated">
            <span class="pulse-indicator"></span>
            Cß║¡p nhß║¡t mß╗¢i nhß║Ñt: {{ lastUpdatedText }}
          </div>
        </div>
        <div class="hub-header-actions" v-if="isLoggedIn && targetGroup && targetGroup.name !== 'Telegram News'">
          <button @click="addNews(targetGroup)" class="macro-btn macro-btn-blue">
            + Thêm tin tức
          </button>
        </div>
      </div>

      <!-- World State (OSINT) -->
      <WorldStateComponent :worldState="worldState" :loading="loadingState" />

      <!-- Loading -->
      <div v-if="loading" class="hub-loading">
        <div class="spinner-border text-primary mb-3" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="text-muted">─Éang tß║úi dß╗» liß╗çu...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="hub-error">
        <span class="hub-error-icon">ΓÜá∩╕Å</span>
        <div>
          <strong>Lß╗ùi:</strong>
          <p class="mb-0 small">{{ error }}</p>
        </div>
      </div>

      <!-- Main Content Layout (Single-Column Premium Dashboard) -->
      <div v-else class="hub-content-section">
        <div v-if="targetGroup" class="news-dashboard-card">
          <!-- Header -->
          <div class="nd-card-header">
            <div class="nd-header-title">
              <span class="nd-title-emoji">≡ƒô░</span>
              <h2 class="nd-title-text">News</h2>
            </div>
            <span class="nd-badge">Live Feed</span>
          </div>

          <!-- Body -->
          <div class="nd-card-body">
            <div v-if="targetNews && targetNews.length" class="news-list-container">
              <NewsItem v-for="item in targetNews" :key="item.id" :item="item" :show-actions="isLoggedIn && targetGroup.name !== 'Telegram News'"
                @toggle="toggleStatus(item)" @edit="editNews(item)" @delete="deleteNews(item)" />
            </div>
            <div v-else class="news-empty-state">
              <span class="empty-emoji">≡ƒô¡</span>
              <p class="empty-text">Ch╞░a c├│ tin tß╗⌐c n├áo ─æ╞░ß╗úc cß║¡p nhß║¡t</p>
            </div>
          </div>

          <!-- Footer / Personal Insights -->
          <div class="nd-card-footer">
            <div class="insight-label-row">
              <span class="insight-emoji">≡ƒÆ¡</span>
              <label class="insight-label">Ghi ch├║ / Nhß║¡n ─æß╗ïnh v─⌐ m├┤</label>
            </div>
            <textarea 
              v-model="localConclusion" 
              @blur="saveConclusion" 
              :disabled="!isLoggedIn"
              rows="3"
              class="insight-textarea" 
              :placeholder="isLoggedIn ? 'Nhß║¡p nhß║¡n ─æß╗ïnh, ph├ón t├¡ch c├í nh├ón cß╗ºa bß║ín vß╗ü diß╗àn biß║┐n tin tß╗⌐c v─⌐ m├┤ hiß╗çn tß║íi...' : '─É─âng nhß║¡p ─æß╗â nhß║¡p nhß║¡n ─æß╗ïnh c├í nh├ón...'"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- Forms & Modal -->
      <div class="macro-modal-overlay" v-if="showNewsForm">
        <div class="macro-modal-box">
          <button @click="resetNewsForm();" class="macro-modal-close">Γ£ò</button>
          <NewsItemForm v-if="showNewsForm" :modelValue="editingNews" @submit="saveNews" @cancel="resetNewsForm" />
        </div>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'

import { ref, reactive, onMounted, computed, watch } from 'vue'
import NewsItem from '../components/MacroIntelHub/NewsItem.vue'
import NewsItemForm from '../components/MacroIntelHub/NewsItemForm.vue'
import WorldStateComponent from '../components/MacroIntelHub/WorldState.vue'

const groups = ref([])
const news = reactive({})
const loading = ref(true)
const error = ref('')
const showNewsForm = ref(false)
const editingNews = ref(null)

// OSINT State
const worldState = ref({})
const loadingState = ref(false)

const isLoggedIn = computed(() => !!localStorage.getItem('token'))

const targetGroup = computed(() => {
  return groups.value.find(g => g.name === 'Telegram News') || groups.value[0]
})

const targetNews = computed(() => {
  const g = targetGroup.value
  return g ? (news[g.id] || []) : []
})

const localConclusion = ref('')
watch(() => targetGroup.value, (newGroup) => {
  if (newGroup) {
    localConclusion.value = newGroup.conclusion || ''
  }
}, { immediate: true })

function saveConclusion() {
  if (targetGroup.value) {
    updateConclusion(targetGroup.value, localConclusion.value)
  }
}

const lastUpdatedText = computed(() => {
  let latestDate = null
  
  // Check news items
  for (const groupId in news) {
    const items = news[groupId]
    if (Array.isArray(items)) {
      items.forEach(item => {
        if (item.created_at) {
          const d = new Date(item.created_at)
          if (!latestDate || d > latestDate) {
            latestDate = d
          }
        }
      })
    }
  }
  
  // Check groups
  if (Array.isArray(groups.value)) {
    groups.value.forEach(g => {
      if (g.created_at) {
        const d = new Date(g.created_at)
        if (!latestDate || d > latestDate) {
          latestDate = d
        }
      }
    })
  }
  
  if (!latestDate) return null
  
  return latestDate.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
})

function getUserId() {
  try {
    const stored = localStorage.getItem('userInfo')
    if (stored) {
      const info = JSON.parse(stored)
      return info.id || info.custodyCode || ''
    }
  } catch (e) {
    console.error('Error reading userInfo:', e)
  }
  return ''
}

function fetchGroups() {
  loading.value = true
  error.value = ''
  const uid = getUserId()
  fetch(`/api/news-groups${uid ? '?user_id=' + encodeURIComponent(uid) : ''}`, { headers: authHeader() })
    .then(async r => {
      if (!r.ok) {
        const err = await r.text();
        error.value = `API Error: ${r.status} - ${err}`
        throw new Error('API returned error')
      }
      try {
        const text = await r.text()
        const data = text ? JSON.parse(text) : null
        return Array.isArray(data) ? data : []
      } catch (e) {
        error.value = `Parse error: ${e.message}`
        return []
      }
    })
    .then(data => {
      groups.value = data || []
      if (data && data.length > 0) {
        data.forEach(g => {
          fetchNews(g.id)
        })
      }
    })
    .catch(e => {
      console.error('fetchGroups error:', e)
      if (!error.value) {
        error.value = `Error: ${e.message}`
      }
      groups.value = []
    })
    .finally(() => {
      loading.value = false
    })
}

function fetchNews(groupId) {
  fetch(`/api/news-items?group_id=${groupId}`, { headers: authHeader() })
    .then(r => {
      if (!r.ok) {
        return []
      }
      return r.json().catch(() => [])
    })
    .then(data => {
      if (Array.isArray(data)) {
        news[groupId] = data
      } else {
        news[groupId] = []
      }
    })
    .catch(e => {
      console.error(`fetchNews error for groupId ${groupId}:`, e)
      news[groupId] = []
    })
}

function addNews(group) {
  editingNews.value = { group_id: group.id, importance: 3, status: 'active' }
  showNewsForm.value = true
}

function editNews(item) {
  editingNews.value = { ...item }
  showNewsForm.value = true
}

function saveNews(item) {
  const method = item.id ? 'PUT' : 'POST'
  const url = item.id
    ? `/api/news-items?id=${item.id}`
    : `/api/news-items?group_id=${item.group_id}`
  fetch(url, {
    method,
    headers: { ...authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify(item)
  })
    .then(r => {
      if (!r.ok) {
        return
      }
      fetchNews(item.group_id)
      resetNewsForm()
    })
    .catch(e => {
      console.error('saveNews error:', e)
    })
}

function deleteNews(item) {
  fetch(`/api/news-items?id=${item.id}`, { method: 'DELETE', headers: authHeader() })
    .then(r => {
      if (!r.ok) {
        return
      }
      fetchNews(item.group_id)
    })
    .catch(e => {
      console.error('deleteNews error:', e)
    })
}

function toggleStatus(item) {
  fetch(`/api/news-items/toggle?id=${item.id}`, { method: 'POST', headers: authHeader() })
    .then(r => {
      if (!r.ok) {
        return
      }
      fetchNews(item.group_id)
    })
    .catch(e => {
      console.error('toggleStatus error:', e)
    })
}

function updateConclusion(group, conclusion) {
  fetch(`/api/news-groups?id=${group.id}`, {
    method: 'PUT',
    headers: { ...authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...group, conclusion })
  })
    .then(r => {
      if (!r.ok) {
        console.error('updateConclusion failed:', r.status)
      }
    })
    .catch(e => {
      console.error('updateConclusion error:', e)
    })
}

function resetNewsForm() {
  editingNews.value = null
  showNewsForm.value = false
}

function authHeader() {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

onMounted(() => {
  fetchGroups()
  fetchWorldState()
})

function fetchWorldState() {
  loadingState.value = true
  fetch('/api/osint/world-state', { headers: authHeader() })
    .then(r => r.json())
    .then(data => worldState.value = data || {})
    .catch(e => console.error('fetchWorldState error:', e))
    .finally(() => loadingState.value = false)
}

</script>

<style scoped>
/* ======================================= */
/*  MACRO HUB ΓÇô Premium Terminal Theme     */
/* ======================================= */

.hub-container-wrapper {
  background: #f8fafc;
  min-height: 100vh;
}

/* ΓöÇΓöÇ Container ΓöÇΓöÇ */
.macro-hub-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem;
  color: #1e293b;
}

/* ΓöÇΓöÇ Header ΓöÇΓöÇ */
.hub-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.hub-title {
  font-size: 2.2rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 0.4rem 0;
  letter-spacing: -0.5px;
  font-family: 'Outfit', sans-serif;
  background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hub-subtitle {
  color: #475569;
  font-size: 0.95rem;
  margin: 0;
}

.hub-last-updated {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #475569;
  margin-top: 0.55rem;
  background: rgba(16, 185, 129, 0.06);
  border: 1px solid rgba(16, 185, 129, 0.12);
  padding: 0.25rem 0.65rem;
  border-radius: 6px;
  font-weight: 500;
}

.pulse-indicator {
  width: 6px;
  height: 6px;
  background-color: #10b981;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  animation: pulse 1.8s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 5px rgba(16, 185, 129, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
  }
}

.hub-header-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* ΓöÇΓöÇ Buttons ΓöÇΓöÇ */
.macro-btn {
  font-weight: 600;
  border-radius: 8px;
  padding: 0.6rem 1.2rem;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  outline: none;
  border: 1px solid transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
  white-space: nowrap;
}
.macro-btn:active {
  transform: scale(0.97);
}
.macro-btn-blue {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.08);
}
.macro-btn-blue:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  box-shadow: 0 4px 14px rgba(37,99,235,0.2);
}

/* ΓöÇΓöÇ Loading ΓöÇΓöÇ */
.hub-loading {
  text-align: center;
  padding: 5rem 1rem;
}

/* ΓöÇΓöÇ Error ΓöÇΓöÇ */
.hub-error {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  background: rgba(244, 63, 94, 0.08);
  border: 1px solid rgba(244, 63, 94, 0.15);
  color: #be123c;
  padding: 1.25rem 1.5rem;
  border-radius: 10px;
  margin-bottom: 1.5rem;
}
.hub-error-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

/* ΓöÇΓöÇ Premium News Card Design ΓöÇΓöÇ */
.news-dashboard-card {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.02);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  margin-top: 1.5rem;
}

.nd-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
}

.nd-header-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.nd-title-emoji {
  font-size: 1.5rem;
}

.nd-title-text {
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
  font-family: 'Outfit', sans-serif;
  letter-spacing: -0.3px;
}

.nd-badge {
  background: rgba(16, 185, 129, 0.08);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.15);
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.nd-card-body {
  padding: 2rem;
}

.news-list-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.news-empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: rgba(0, 0, 0, 0.01);
  border: 2px dashed rgba(0, 0, 0, 0.06);
  border-radius: 12px;
}

.empty-emoji {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 1rem;
}

.empty-text {
  color: #64748b;
  font-size: 0.95rem;
  margin: 0;
}

.nd-card-footer {
  padding: 1.5rem 2rem 2rem;
  background: #f8fafc;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.insight-label-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.insight-emoji {
  font-size: 1.1rem;
}

.insight-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.insight-textarea {
  width: 100%;
  padding: 0.85rem 1.1rem;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  font-size: 0.92rem;
  font-family: inherit;
  background: #ffffff;
  color: #1e293b;
  transition: all 0.2s ease;
  resize: vertical;
  line-height: 1.6;
}

.insight-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.08);
}

.insight-textarea:disabled {
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

/* ΓöÇΓöÇ Modal ΓöÇΓöÇ */
.macro-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(15, 23, 42, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  backdrop-filter: blur(4px);
  animation: fadeIn .2s ease;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.macro-modal-box {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(15,23,42,0.15);
  padding: 2rem 1.75rem 1.75rem;
  max-width: 460px;
  width: 100%;
  position: relative;
  color: #0f172a;
  animation: slideUp .25s cubic-bezier(.4,0,.2,1);
}
@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: none; opacity: 1; }
}
.macro-modal-close {
  position: absolute;
  top: 12px;
  right: 14px;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 50%;
  width: 34px;
  height: 34px;
  font-size: 1.2rem;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
}
.macro-modal-close:hover {
  background: rgba(0, 0, 0, 0.08);
  color: #0f172a;
}

/* ΓöÇΓöÇ Modal form overrides ΓöÇΓöÇ */
:deep(.macro-modal-box input),
:deep(.macro-modal-box textarea),
:deep(.macro-modal-box select) {
  border-radius: 8px !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  padding: 0.65rem 1rem !important;
  font-size: 0.95rem !important;
  width: 100%;
  background: #f8fafc !important;
  color: #0f172a !important;
  transition: border-color .15s, box-shadow .15s;
}
:deep(.macro-modal-box input:focus),
:deep(.macro-modal-box textarea:focus),
:deep(.macro-modal-box select:focus) {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
  outline: none;
  background: #ffffff !important;
  color: #0f172a !important;
}

/* ΓöÇΓöÇ Responsive ΓöÇΓöÇ */
@media (max-width: 640px) {
  .macro-hub-container {
    padding: 1.5rem 1rem;
  }
  .hub-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  .hub-title {
    font-size: 1.8rem;
  }
  .hub-header-actions {
    width: 100%;
  }
  .hub-header-actions .macro-btn {
    width: 100%;
    justify-content: center;
  }
  .nd-card-header {
    padding: 1.25rem 1.5rem;
  }
  .nd-card-body {
    padding: 1.5rem;
  }
  .nd-card-footer {
    padding: 1.25rem 1.5rem 1.5rem;
  }
}

:deep(.news-item) {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
  color: #0f172a !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.01) !important;
  transition: all 0.2s ease !important;
}
:deep(.news-item:hover) {
  border-color: rgba(59, 130, 246, 0.15) !important;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.03) !important;
}

:deep(.macro-modal-box) {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  color: #0f172a !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1) !important;
}
:deep(.form-label), :deep(label) {
  color: #475569 !important;
  font-weight: 600 !important;
}
:deep(.macro-modal-title) {
  color: #0f172a !important;
  font-family: 'Outfit', sans-serif !important;
}
</style>
