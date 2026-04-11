<template>
  <div>
    <NavBar />
    <div class="macro-hub-container mx-auto px-2 sm:px-4 py-6 max-w-5xl">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <h1 class="text-3xl font-bold tracking-tight text-gray-800 mb-2 sm:mb-0">Macro Intelligence Hub</h1>
      <div class="flex gap-2 flex-wrap">
        <button @click="showGroupForm = true" class="macro-btn macro-btn-blue">
          <span class="hidden sm:inline">+ Nhóm mới</span>
          <span class="sm:hidden">+</span>
        </button>
        <button @click="generatePrompt" class="macro-btn macro-btn-yellow">
          <span class="hidden sm:inline">Generate Strategy Prompt</span>
          <span class="sm:hidden">AI</span>
        </button>
      </div>
    </div>
    <div v-if="loading" class="text-center py-12 text-lg text-gray-400">Đang tải dữ liệu...</div>
    <div v-else>
      <div v-if="groups.length === 0" class="text-center text-gray-400 py-12">Chưa có nhóm sự kiện nào. Hãy tạo nhóm mới để bắt đầu quản lý tin tức vĩ mô!</div>
      <div class="grid gap-6 md:grid-cols-2">
        <GroupCard v-for="group in groups" :key="group.id" :group="group"
          @edit="editGroup(group)" @delete="deleteGroup(group)" @updateConclusion="updateConclusion(group, $event)">
          <div>
            <div class="flex justify-between items-center mb-2">
              <span class="font-semibold text-gray-700">Tin tức</span>
              <button @click="addNews(group)" class="macro-btn macro-btn-green text-xs px-2 py-1">+ Thêm tin</button>
            </div>
            <div v-if="news[group.id] && news[group.id].length">
              <NewsItem v-for="item in news[group.id]" :key="item.id" :item="item"
                @toggle="toggleStatus(item)" @edit="editNews(item)" @delete="deleteNews(item)" />
            </div>
            <div v-else class="text-xs text-gray-400">Chưa có tin tức nào.</div>
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
const showGroupForm = ref(false)
const showNewsForm = ref(false)
const editingGroup = ref(null)
const editingNews = ref(null)
const showPromptModal = ref(false)
const promptText = ref('')

function fetchGroups() {
  loading.value = true
  fetch('/api/news-groups', { headers: authHeader() })
    .then(async r => {
      if (!r.ok) {
        const err = await r.text();
        console.error('API /api/news-groups error:', err)
        return [];
      }
      return r.json();
    })
    .then(data => {
      groups.value = data
      data.forEach(g => fetchNews(g.id))
    })
    .catch(e => {
      console.error('fetchGroups error:', e)
    })
    .finally(() => loading.value = false)
}
function fetchNews(groupId) {
  fetch(`/api/news-groups/${groupId}/items`, { headers: authHeader() })
    .then(r => r.json())
    .then(data => news[groupId] = data)
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
  const url = item.id ? `/api/news-items/${item.id}` : `/api/news-groups/${item.group_id}/items`
  fetch(url, {
    method,
    headers: { ...authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify(item)
  }).then(() => {
    fetchNews(item.group_id)
    resetNewsForm()
  })
}
function deleteNews(item) {
  fetch(`/api/news-items/${item.id}`, { method: 'DELETE', headers: authHeader() })
    .then(() => fetchNews(item.group_id))
}
function toggleStatus(item) {
  fetch(`/api/news-items/${item.id}/toggle`, { method: 'POST', headers: authHeader() })
    .then(() => fetchNews(item.group_id))
}
function editGroup(group) {
  editingGroup.value = { ...group }
  showGroupForm.value = true
}
function saveGroup(group) {
  const method = group.id ? 'PUT' : 'POST'
  const url = group.id ? `/api/news-groups/${group.id}` : '/api/news-groups'
  fetch(url, {
    method,
    headers: { ...authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify(group)
  }).then(() => {
    fetchGroups()
    resetGroupForm()
  })
}
function deleteGroup(group) {
  fetch(`/api/news-groups/${group.id}`, { method: 'DELETE', headers: authHeader() })
    .then(() => fetchGroups())
}
function updateConclusion(group, conclusion) {
  fetch(`/api/news-groups/${group.id}`, {
    method: 'PUT',
    headers: { ...authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...group, conclusion })
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
    .then(r => r.json())
    .then(data => {
      promptText.value = data.prompt
      showPromptModal.value = true
    })
}
function authHeader() {
  // TODO: Lấy token hoặc user id từ hệ thống đăng nhập thực tế
  return { 'X-User-ID': localStorage.getItem('user_id') || '' }
}
onMounted(fetchGroups)
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
  background: #f8fafc;
  min-height: 100vh;
  border-radius: 18px;
  box-shadow: 0 2px 16px 0 rgba(0,0,0,0.04);
}
.macro-btn {
  font-weight: 500;
  border-radius: 8px;
  padding: 0.5rem 1.2rem;
  transition: all 0.15s;
  box-shadow: 0 1px 4px 0 rgba(0,0,0,0.04);
  outline: none;
  border: 1.5px solid transparent;
}
.macro-btn-blue {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}
.macro-btn-blue:hover {
  background: #1746a2;
  border-color: #1746a2;
}
.macro-btn-yellow {
  background: #f59e42;
  color: #fff;
  border-color: #f59e42;
}
.macro-btn-yellow:hover {
  background: #d97706;
  border-color: #d97706;
}
.macro-btn-green {
  background: #22c55e;
  color: #fff;
  border-color: #22c55e;
}
.macro-btn-green:hover {
  background: #15803d;
  border-color: #15803d;
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
