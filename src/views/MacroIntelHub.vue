<template>
  <div>
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

      <!-- Empty -->
      <div v-else-if="groups && groups.length === 0" class="hub-empty">
        <div class="hub-empty-inner">
          <div class="hub-empty-icon">📊</div>
          <h5>Chưa có nhóm sự kiện nào</h5>
          <p class="text-muted mb-4">Hãy tạo nhóm mới để bắt đầu quản lý tin tức vĩ mô</p>
          <button @click="showGroupForm = true" class="macro-btn macro-btn-blue">+ Tạo nhóm đầu tiên</button>
        </div>
      </div>

      <!-- Groups Grid -->
      <div v-else-if="groups && groups.length > 0" class="hub-grid">
        <GroupCard v-for="group in groups" :key="group.id" :group="group"
          @edit="editGroup(group)" @delete="deleteGroup(group)" @updateConclusion="updateConclusion(group, $event)">
          <div>
            <div class="news-section-header">
              <span class="news-section-title">📰 Tin tức</span>
              <button @click="addNews(group)" class="macro-btn macro-btn-green macro-btn-sm">+ Thêm</button>
            </div>
            <div v-if="news[group.id] && news[group.id].length" class="news-list">
              <NewsItem v-for="item in news[group.id]" :key="item.id" :item="item"
                @toggle="toggleStatus(item)" @edit="editNews(item)" @delete="deleteNews(item)" />
            </div>
            <div v-else class="news-empty">
              📭 Chưa có tin tức nào
            </div>
          </div>
        </GroupCard>
      </div>

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

const groups = ref([])
const news = reactive({})
const loading = ref(true)
const error = ref('')
const showGroupForm = ref(false)
const showNewsForm = ref(false)
const editingGroup = ref(null)
const editingNews = ref(null)
const showPromptModal = ref(false)
const promptText = ref('')

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
  fetchGroups()
})
</script>

<style scoped>
/* ── Container ── */
.macro-hub-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
  min-height: 100vh;
  background: #f8fafc;
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
  border-bottom: 1px solid #e2e8f0;
}

.hub-title {
  font-size: 2rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 0.4rem 0;
  letter-spacing: -0.5px;
}

.hub-subtitle {
  color: #64748b;
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
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  outline: none;
  border: none;
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
  background: #2563eb;
  color: #fff;
}
.macro-btn-blue:hover {
  background: #1d4ed8;
  box-shadow: 0 4px 14px rgba(37,99,235,0.35);
}
.macro-btn-yellow {
  background: #f59e0b;
  color: #fff;
}
.macro-btn-yellow:hover {
  background: #d97706;
  box-shadow: 0 4px 14px rgba(245,158,11,0.35);
}
.macro-btn-green {
  background: #10b981;
  color: #fff;
}
.macro-btn-green:hover {
  background: #059669;
  box-shadow: 0 4px 14px rgba(16,185,129,0.35);
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
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
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
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 3rem 3.5rem;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
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
  border-bottom: 1px solid #f1f5f9;
}
.news-section-title {
  font-weight: 700;
  font-size: 0.85rem;
  color: #475569;
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
  color: #94a3b8;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 0.9rem;
  border: 1px dashed #e2e8f0;
}

/* ── Modal ── */
.macro-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  animation: fadeIn .2s ease;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.macro-modal-box {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  padding: 2rem 1.75rem 1.75rem;
  max-width: 460px;
  width: 100%;
  position: relative;
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
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 50%;
  width: 34px;
  height: 34px;
  font-size: 1.2rem;
  color: #475569;
  cursor: pointer;
  transition: background .15s;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
}
.macro-modal-close:hover {
  background: #e2e8f0;
  color: #1e293b;
}

/* ── Modal form overrides ── */
.macro-modal-box input,
.macro-modal-box textarea,
.macro-modal-box select {
  border-radius: 8px !important;
  border: 1.5px solid #e2e8f0 !important;
  padding: 0.65rem 1rem !important;
  font-size: 0.95rem !important;
  width: 100%;
  background: #f8fafc;
  transition: border-color .15s, box-shadow .15s;
}
.macro-modal-box input:focus,
.macro-modal-box textarea:focus,
.macro-modal-box select:focus {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
  outline: none;
  background: #fff;
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
</style>
