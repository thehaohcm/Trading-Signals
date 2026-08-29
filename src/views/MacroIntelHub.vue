<template>
  <div class="hub-container-wrapper">
    <NavBar />
    <div class="macro-hub-container">
      <!-- Header -->
      <div class="hub-header">
        <div class="hub-header-left">
          <h1 class="hub-title">Macro Intelligence Hub</h1>
          <p class="hub-subtitle">Quản lý và phân tích các sự kiện vĩ mô ảnh hưởng đến thị trường</p>
        </div>
        <div class="hub-header-actions">
          <button @click="showGroupForm = true" class="macro-btn macro-btn-blue">
            + Nhóm mới
          </button>
          <button @click="generatePrompt" class="macro-btn macro-btn-yellow">
            🤖 AI Strategy
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="hub-loading">
        <div class="spinner-border text-primary mb-3" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="text-muted">Đang tải dữ liệu...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="hub-error">
        <span class="hub-error-icon">⚠️</span>
        <div>
          <strong>Lỗi:</strong>
          <p class="mb-0 small">{{ error }}</p>
        </div>
      </div>

      <template v-else>
        <!-- AI Settings (only for logged-in users) -->
        <AISettingsModal v-if="isLoggedIn" />

        <!-- Macro Audio Podcast (Pre-market Squawk) -->
        <PodcastPlayer />

        <!-- World State (OSINT) -->
        <WorldState :worldState="worldState" :loading="loadingState" />


        <!-- Empty -->
        <div v-if="groups && groups.length === 0" class="hub-empty">
        <div class="hub-empty-inner">
          <div class="hub-empty-icon">📊</div>
          <h5>Chưa có nhóm sự kiện nào</h5>
          <p class="text-muted mb-4">Hãy tạo nhóm mới để bắt đầu quản lý tin tức vĩ mô</p>
          <button @click="showGroupForm = true" class="macro-btn macro-btn-blue">+ Tạo nhóm đầu tiên</button>
        </div>
      </div>

      <!-- Groups Grid -->
      <div v-else-if="groups && groups.length > 0" class="hub-grid">
        <GroupCard v-for="group in groups" :key="group.id" :group="group" :isReadOnly="group.name === 'Telegram News'"
          @edit="editGroup(group)" @delete="deleteGroup(group)" @updateConclusion="updateConclusion(group, $event)">
          <div>
            <div class="news-section-header">
              <span class="news-section-title">📰 Tin tức</span>
              <button v-if="group.name !== 'Telegram News'" @click="addNews(group)" class="macro-btn macro-btn-green macro-btn-sm">+ Thêm</button>
            </div>
            <div v-if="news[group.id] && news[group.id].length" class="news-list">
              <NewsItem v-for="item in news[group.id]" :key="item.id" :item="item" :show-actions="group.name !== 'Telegram News'"
                @toggle="toggleStatus(item)" @edit="editNews(item)" @delete="deleteNews(item)" />
            </div>
            <div v-else class="news-empty">
              📭 Chưa có tin tức nào
            </div>
          </div>
        </GroupCard>
      </div>
      </template>

      <!-- Forms & Modal -->
      <div class="macro-modal-overlay" v-if="showGroupForm || showNewsForm">
        <div class="macro-modal-box">
          <button @click="resetGroupForm(); resetNewsForm();" class="macro-modal-close">✕</button>
          <GroupForm v-if="showGroupForm" :modelValue="editingGroup" @submit="saveGroup" @cancel="resetGroupForm" />
          <NewsItemForm v-if="showNewsForm" :modelValue="editingNews" @submit="saveNews" @cancel="resetNewsForm" />
        </div>
      </div>
      <PromptModal v-if="showPromptModal" :prompt="promptText" @close="showPromptModal = false" />
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'

import { ref, reactive, onMounted } from 'vue'
import GroupCard from '../components/MacroIntelHub/GroupCard.vue'
import NewsItem from '../components/MacroIntelHub/NewsItem.vue'
import NewsItemForm from '../components/MacroIntelHub/NewsItemForm.vue'
import GroupForm from '../components/MacroIntelHub/GroupForm.vue'
import PromptModal from '../components/MacroIntelHub/PromptModal.vue'
import WorldState from '../components/MacroIntelHub/WorldState.vue'
import AISettingsModal from '../components/MacroIntelHub/AISettingsModal.vue'
import PodcastPlayer from '../components/MacroIntelHub/PodcastPlayer.vue'
const groups = ref([])
const isLoggedIn = ref(false)
const news = reactive({})
const loading = ref(true)
const error = ref('')
const showGroupForm = ref(false)
const showNewsForm = ref(false)
const editingGroup = ref(null)
const editingNews = ref(null)
const showPromptModal = ref(false)
const promptText = ref('')

// OSINT State
const worldState = ref({})
const loadingState = ref(false)

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
  console.log('Fetching news groups for user:', uid)
  fetch(`/api/news-groups${uid ? '?user_id=' + encodeURIComponent(uid) : ''}`, { headers: authHeader() })
    .then(async r => {
      console.log('Response status:', r.status, r.ok)
      if (!r.ok) {
        const err = await r.text();
        console.error('API error response:', err)
        error.value = `API Error: ${r.status} - ${err}`
        throw new Error('API returned error')
      }
      try {
        const text = await r.text()
        console.log('Raw response:', text)
        const data = text ? JSON.parse(text) : null
        console.log('Parsed data:', data)
        return Array.isArray(data) ? data : []
      } catch (e) {
        console.error('JSON parse error:', e)
        error.value = `Parse error: ${e.message}`
        return []
      }
    })
    .then(data => {
      console.log('Processing data:', data, Array.isArray(data), data.length)
      groups.value = data || []
      if (data && data.length > 0) {
        data.forEach(g => {
          console.log('Fetching news for group:', g.id)
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
      console.log('Fetch complete, groups:', groups.value)
    })
}
function fetchNews(groupId) {
  fetch(`/api/news-items?group_id=${groupId}`, { headers: authHeader() })
    .then(r => {
      if (!r.ok) {
        console.error(`Fetch news items for group ${groupId} failed:`, r.status)
        return []
      }
      return r.json().catch(e => {
        console.error(`JSON parse error for group ${groupId}:`, e)
        return []
      })
    })
    .then(data => {
      if (Array.isArray(data)) {
        news[groupId] = data
      } else {
        console.warn(`Invalid data for group ${groupId}:`, data)
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
        console.error('saveNews failed:', r.status)
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
        console.error('deleteNews failed:', r.status)
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
        console.error('toggleStatus failed:', r.status)
        return
      }
      fetchNews(item.group_id)
    })
    .catch(e => {
      console.error('toggleStatus error:', e)
    })
}
function editGroup(group) {
  editingGroup.value = { ...group }
  showGroupForm.value = true
}
function saveGroup(group) {
  if (!group.name || !group.name.trim()) {
    alert('Tên nhóm không được để trống!')
    return
  }
  const uid = getUserId()
  const method = group.id ? 'PUT' : 'POST'
  const url = group.id ? `/api/news-groups?id=${group.id}` : '/api/news-groups'
  const payload = { ...group, user_id: uid }
  fetch(url, {
    method,
    headers: { ...authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
    .then(r => {
      if (!r.ok) {
        console.error('saveGroup failed:', r.status)
        return
      }
      fetchGroups()
      resetGroupForm()
    })
    .catch(e => {
      console.error('saveGroup error:', e)
    })
}
function deleteGroup(group) {
  fetch(`/api/news-groups?id=${group.id}`, { method: 'DELETE', headers: authHeader() })
    .then(r => {
      if (!r.ok) {
        console.error('deleteGroup failed:', r.status)
        return
      }
      fetchGroups()
    })
    .catch(e => {
      console.error('deleteGroup error:', e)
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
function resetGroupForm() {
  editingGroup.value = null
  showGroupForm.value = false
}
function resetNewsForm() {
  editingNews.value = null
  showNewsForm.value = false
}
function generatePrompt() {
  fetch('/api/news-groups/generate-prompt', { headers: authHeader() })
    .then(r => {
      if (!r.ok) {
        console.error('generatePrompt failed:', r.status)
        return {}
      }
      return r.json()
    })
    .then(data => {
      if (data && data.prompt) {
        promptText.value = data.prompt
        showPromptModal.value = true
      } else {
        console.warn('generatePrompt returned invalid data:', data)
      }
    })
    .catch(e => {
      console.error('generatePrompt error:', e)
    })
}
function authHeader() {
  // Đồng bộ với Community/MyPortfolio: truyền token đăng nhập
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

onMounted(() => {
  console.log('MacroIntelHub component mounted')
  // Check if user is logged in
  const token = localStorage.getItem('token')
  const userInfo = localStorage.getItem('userInfo')
  isLoggedIn.value = !!(token && userInfo)

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
/*  MACRO HUB – Premium Terminal Theme     */
/* ======================================= */

.hub-container-wrapper {
  background: #0a0d14;
  min-height: 100vh;
}

/* ── Container ── */
.macro-hub-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem 2rem;
  color: #e2e8f0;
}

/* ── Header ── */
.hub-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.hub-title {
  font-size: 2rem;
  font-weight: 800;
  color: #ffffff;
  margin: 0 0 0.4rem 0;
  letter-spacing: -0.5px;
  font-family: 'Outfit', sans-serif;
  background: linear-gradient(135deg, #ffffff 0%, #00f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hub-subtitle {
  color: #94a3b8;
  font-size: 0.95rem;
  margin: 0;
}

.hub-header-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* ── Buttons ── */
.macro-btn {
  font-weight: 600;
  border-radius: 8px;
  padding: 0.6rem 1.2rem;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.25);
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
.macro-btn-sm {
  padding: 0.35rem 0.85rem;
  font-size: 0.8rem;
}
.macro-btn-blue {
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  color: #0a0d14;
  font-weight: 700;
}
.macro-btn-blue:hover {
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.4);
  transform: translateY(-1px);
}
.macro-btn-yellow {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  color: #0a0d14;
  font-weight: 700;
}
.macro-btn-yellow:hover {
  box-shadow: 0 6px 20px rgba(246, 211, 101, 0.4);
  transform: translateY(-1px);
}
.macro-btn-green {
  background: rgba(0, 245, 160, 0.12);
  color: #00f5a0;
  border: 1px solid rgba(0, 245, 160, 0.3);
}
.macro-btn-green:hover {
  background: #00f5a0;
  color: #0a0d14;
  box-shadow: 0 4px 14px rgba(0, 245, 160, 0.3);
}

/* ── Loading ── */
.hub-loading {
  text-align: center;
  padding: 5rem 1rem;
}

/* ── Error ── */
.hub-error {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  background: rgba(255, 75, 114, 0.1);
  border: 1px solid rgba(255, 75, 114, 0.3);
  color: #ff4b72;
  padding: 1.25rem 1.5rem;
  border-radius: 10px;
  margin-bottom: 1.5rem;
}
.hub-error-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

/* ── Empty state ── */
.hub-empty {
  text-align: center;
  padding: 4rem 1rem;
}
.hub-empty-inner {
  display: inline-block;
  background: rgba(18, 24, 38, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 3rem 3.5rem;
  box-shadow: 0 8px 32px rgba(0,0,0,0.35);
  backdrop-filter: blur(16px);
}
.hub-empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

/* ── Groups Grid ── */
.hub-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}
@media (min-width: 992px) {
  .hub-grid {
    grid-template-columns: 1fr 1fr;
  }
}

/* ── News section inside cards ── */
.news-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.75rem;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.news-section-title {
  font-weight: 700;
  font-size: 0.82rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.news-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.news-empty {
  text-align: center;
  padding: 2rem 1rem;
  color: #64748b;
  background: rgba(10, 13, 20, 0.4);
  border-radius: 8px;
  font-size: 0.9rem;
  border: 1px dashed rgba(255, 255, 255, 0.08);
}

/* ── Modal ── */
.macro-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  backdrop-filter: blur(8px);
  animation: fadeIn .2s ease;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.macro-modal-box {
  background: #111726;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
  padding: 2rem 1.75rem 1.75rem;
  max-width: 460px;
  width: 100%;
  position: relative;
  color: #e2e8f0;
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  width: 34px;
  height: 34px;
  font-size: 1.2rem;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
}
.macro-modal-close:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

/* ── Modal form overrides ── */
:deep(.macro-modal-box input),
:deep(.macro-modal-box textarea),
:deep(.macro-modal-box select) {
  border-radius: 8px !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  padding: 0.65rem 1rem !important;
  font-size: 0.95rem !important;
  width: 100%;
  background: rgba(10, 13, 20, 0.8) !important;
  color: #ffffff !important;
  transition: border-color .15s, box-shadow .15s;
}
:deep(.macro-modal-box input:focus),
:deep(.macro-modal-box textarea:focus),
:deep(.macro-modal-box select:focus) {
  border-color: #00f2fe !important;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15) !important;
  outline: none;
  background: rgba(10, 13, 20, 0.95) !important;
  color: #ffffff !important;
}

/* ── Responsive ── */
@media (max-width: 640px) {
  .macro-hub-container {
    padding: 1rem 0.75rem;
  }
  .hub-header {
    flex-direction: column;
    gap: 1rem;
  }
  .hub-title {
    font-size: 1.4rem;
  }
  .hub-header-actions {
    width: 100%;
  }
  .hub-header-actions .macro-btn {
    flex: 1;
    justify-content: center;
  }
  .macro-modal-box {
    padding: 1.5rem 1rem 1.25rem;
  }
  .hub-empty-inner {
    padding: 2rem 1.5rem;
  }
}

/* ── Deep sub-components dark overrides ── */
:deep(.group-card) {
  background: rgba(18, 24, 38, 0.75) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35) !important;
  color: #e2e8f0 !important;
  backdrop-filter: blur(16px);
  transition: all 0.25s ease;
}
:deep(.group-card:hover) {
  border-color: rgba(0, 242, 254, 0.3) !important;
  box-shadow: 0 8px 32px rgba(0, 242, 254, 0.1) !important;
}
:deep(.group-title) {
  color: #ffffff !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
}
:deep(.group-desc) {
  color: #94a3b8 !important;
}
:deep(.group-card-footer) {
  border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
}
:deep(.gc-action-btn) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #94a3b8 !important;
}
:deep(.gc-action-btn:hover) {
  background: rgba(0, 242, 254, 0.12) !important;
  color: #00f2fe !important;
  border-color: rgba(0, 242, 254, 0.3) !important;
}
:deep(.gc-action-danger:hover) {
  background: rgba(255, 75, 114, 0.12) !important;
  color: #ff4b72 !important;
  border-color: rgba(255, 75, 114, 0.3) !important;
}
:deep(.conclusion-label) {
  color: #94a3b8 !important;
}
:deep(.conclusion-textarea) {
  background: rgba(10, 13, 20, 0.8) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
}
:deep(.conclusion-textarea:focus) {
  background: rgba(10, 13, 20, 0.95) !important;
  border-color: #00f2fe !important;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15) !important;
  color: #ffffff !important;
}

:deep(.news-item) {
  background: rgba(10, 13, 20, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  color: #e2e8f0 !important;
  border-radius: 8px !important;
}
:deep(.news-item-title) {
  color: #ffffff !important;
}
:deep(.ni-active) {
  background: rgba(0, 245, 160, 0.1) !important;
  border-color: rgba(0, 245, 160, 0.25) !important;
  color: #00f5a0 !important;
}
:deep(.ni-active:hover) {
  background: rgba(0, 245, 160, 0.16) !important;
}
:deep(.ni-inactive) {
  background: rgba(148, 163, 184, 0.08) !important;
  border-color: rgba(148, 163, 184, 0.18) !important;
  color: #94a3b8 !important;
}
:deep(.ni-inactive:hover) {
  background: rgba(148, 163, 184, 0.12) !important;
}
:deep(.ni-action-btn) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #94a3b8 !important;
}
:deep(.ni-action-btn:hover) {
  background: rgba(0, 242, 254, 0.12) !important;
  color: #00f2fe !important;
}
:deep(.ni-action-danger:hover) {
  background: rgba(255, 75, 114, 0.12) !important;
  color: #ff4b72 !important;
}

:deep(.macro-modal-box) {
  background: #111726 !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: #e2e8f0 !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6) !important;
}
:deep(.form-label), :deep(label) {
  color: #94a3b8 !important;
  font-weight: 600 !important;
}
:deep(.macro-modal-title) {
  color: #ffffff !important;
  font-family: 'Outfit', sans-serif !important;
}
:deep(.hub-empty-inner) {
  background: rgba(18, 24, 38, 0.75) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #e2e8f0 !important;
}
:deep(.hub-empty-inner h5) {
  color: #ffffff !important;
}
</style>
