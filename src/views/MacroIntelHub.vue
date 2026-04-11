<template>
  <div>
    <NavBar />
    <div class="macro-hub-container mx-auto px-2 sm:px-6 py-8 max-w-6xl">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-6 mb-10">
      <div>
        <h1 class="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-blue-700 bg-clip-text text-transparent mb-2">Macro Intelligence Hub</h1>
        <p class="text-gray-500 text-sm">Quản lý và phân tích các sự kiện vĩ mô ảnh hưởng đến thị trường</p>
      </div>
      <div class="flex gap-3 flex-wrap">
        <button @click="showGroupForm = true" class="macro-btn macro-btn-blue">
          <span class="hidden sm:inline">+ Nhóm mới</span>
          <span class="sm:hidden">+</span>
        </button>
        <button @click="generatePrompt" class="macro-btn macro-btn-yellow">
          <span class="hidden sm:inline">🤖 AI Strategy</span>
          <span class="sm:hidden">AI</span>
        </button>
      </div>
    </div>
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="text-center">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <p class="text-gray-500">Đang tải dữ liệu...</p>
      </div>
    </div>
    <div v-else-if="error" class="bg-gradient-to-r from-red-50 to-pink-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg mb-6 shadow-sm">
      <div class="flex items-start gap-3">
        <span class="text-2xl">⚠️</span>
        <div>
          <strong class="block mb-1">Lỗi:</strong>
          <p class="text-sm">{{ error }}</p>
        </div>
      </div>
    </div>
    <div v-else-if="groups && groups.length === 0" class="text-center py-20">
      <div class="inline-block bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-12 border border-blue-100">
        <p class="text-5xl mb-4">📊</p>
        <p class="text-lg text-gray-600 font-medium mb-2">Chưa có nhóm sự kiện nào</p>
        <p class="text-gray-500 mb-6">Hãy tạo nhóm mới để bắt đầu quản lý tin tức vĩ mô</p>
        <button @click="showGroupForm = true" class="macro-btn macro-btn-blue">+ Tạo nhóm đầu tiên</button>
      </div>
    </div>
    <div v-else-if="groups && groups.length > 0">
      <div class="grid gap-6 lg:grid-cols-2">
        <GroupCard v-for="group in groups" :key="group.id" :group="group"
          @edit="editGroup(group)" @delete="deleteGroup(group)" @updateConclusion="updateConclusion(group, $event)">
          <div>
            <div class="flex justify-between items-center mb-4 pb-3 border-b border-gray-100">
              <span class="font-semibold text-gray-700 text-sm uppercase tracking-wider">📰 Tin tức</span>
              <button @click="addNews(group)" class="macro-btn macro-btn-green text-xs px-3 py-1.5">+ Thêm</button>
            </div>
            <div v-if="news[group.id] && news[group.id].length" class="space-y-2">
              <NewsItem v-for="item in news[group.id]" :key="item.id" :item="item"
                @toggle="toggleStatus(item)" @edit="editNews(item)" @delete="deleteNews(item)" />
            </div>
            <div v-else class="text-center py-8 text-gray-400 bg-gray-50 rounded-lg">
              <p class="text-sm">📭 Chưa có tin tức nào</p>
            </div>
          </div>
        </GroupCard>
      </div>
    </div>
    <!-- Forms & Modal -->
    <div class="macro-modal-overlay" v-if="showGroupForm || showNewsForm">
      <div class="macro-modal-box">
        <button @click="resetGroupForm(); resetNewsForm();" class="macro-modal-close">✕</button>
        <div class="p-2 sm:p-0">
          <GroupForm v-if="showGroupForm" :modelValue="editingGroup" @submit="saveGroup" @cancel="resetGroupForm" />
          <NewsItemForm v-if="showNewsForm" :modelValue="editingNews" @submit="saveNews" @cancel="resetNewsForm" />
        </div>
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

function fetchGroups() {
  loading.value = true
  error.value = ''
  console.log('Fetching news groups...')
  fetch('/api/news-groups', { headers: authHeader() })
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
  const method = group.id ? 'PUT' : 'POST'
  const url = group.id ? `/api/news-groups?id=${group.id}` : '/api/news-groups'
  fetch(url, {
    method,
    headers: { ...authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify(group)
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
/* Modal overlay & box */
.macro-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0,0,0,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
}
.macro-modal-box {
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 8px 32px 0 rgba(0,0,0,0.18);
  padding: 2.5rem 2rem 2rem 2rem;
  max-width: 400px;
  width: 96vw;
  position: relative;
  margin: 0 1rem;
  animation: modalIn .18s cubic-bezier(.4,2,.6,1) both;
}
@keyframes modalIn {
  0% { transform: translateY(40px) scale(.98); opacity: 0; }
  100% { transform: none; opacity: 1; }
}
.macro-modal-close {
  position: absolute;
  top: 14px;
  right: 18px;
  background: #f3f4f6;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  font-size: 1.3rem;
  color: #374151;
  cursor: pointer;
  transition: background .15s;
  z-index: 10;
}
.macro-modal-close:hover {
  background: #e5e7eb;
  color: #111;
}
/* Form input style override */
.macro-modal-box input,
.macro-modal-box textarea,
.macro-modal-box select {
  border-radius: 8px !important;
  border: 1.5px solid #e5e7eb !important;
  padding: 0.6rem 1rem !important;
  font-size: 1rem !important;
  margin-bottom: 0.5rem;
  width: 100%;
  background: #f9fafb;
  transition: border .15s;
}
.macro-modal-box input:focus,
.macro-modal-box textarea:focus,
.macro-modal-box select:focus {
  border-color: #2563eb !important;
  outline: none;
}
.macro-modal-box button[type="submit"],
.macro-modal-box button[type="button"] {
  border-radius: 8px;
  min-width: 70px;
  font-weight: 500;
  border: none;
  box-shadow: none;
  padding: 0.5rem 1.2rem;
  margin-top: 0.2rem;
  margin-right: 0.5rem;
  background: #2563eb;
  color: #fff;
  transition: background .15s;
}
.macro-modal-box button[type="button"] {
  background: #e5e7eb;
  color: #222;
}
.macro-modal-box button[type="submit"]:hover {
  background: #1746a2;
}
.macro-modal-box button[type="button"]:hover {
  background: #cbd5e1;
}
@media (max-width: 640px) {
  .macro-modal-box {
    padding: 1.2rem 0.5rem 1.2rem 0.5rem;
    max-width: 98vw;
  }
}
.macro-hub-container {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 100vh;
  padding-top: 0;
}
.macro-btn {
  font-weight: 500;
  border-radius: 8px;
  padding: 0.625rem 1.25rem;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  outline: none;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
}
.macro-btn-blue {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: #fff;
}
.macro-btn-blue:hover {
  background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
  box-shadow: 0 4px 12px 0 rgba(37, 99, 235, 0.3);
  transform: translateY(-2px);
}
.macro-btn-yellow {
  background: linear-gradient(135deg, #f59e42 0%, #d97706 100%);
  color: #fff;
}
.macro-btn-yellow:hover {
  background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
  box-shadow: 0 4px 12px 0 rgba(217, 119, 6, 0.3);
  transform: translateY(-2px);
}
.macro-btn-green {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
}
.macro-btn-green:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  box-shadow: 0 4px 12px 0 rgba(16, 185, 129, 0.3);
  transform: translateY(-2px);
}
@media (max-width: 640px) {
  .macro-hub-container {
    border-radius: 0;
    padding: 0.5rem;
  }
  h1 {
    font-size: 1.3rem;
  }
}
</style>
