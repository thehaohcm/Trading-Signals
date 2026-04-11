<template>
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
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30" v-if="showGroupForm || showNewsForm">
      <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative mx-2">
        <button @click="resetGroupForm(); resetNewsForm();" class="absolute top-2 right-2 text-gray-400 hover:text-black">✕</button>
        <GroupForm v-if="showGroupForm" :modelValue="editingGroup" @submit="saveGroup" @cancel="resetGroupForm" />
        <NewsItemForm v-if="showNewsForm" :modelValue="editingNews" @submit="saveNews" @cancel="resetNewsForm" />
      </div>
    </div>
    <PromptModal v-if="showPromptModal" :prompt="promptText" @close="showPromptModal = false" />
  </div>
</template>

<script setup>

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
    .then(r => r.json())
    .then(data => {
      groups.value = data
      data.forEach(g => fetchNews(g.id))
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
