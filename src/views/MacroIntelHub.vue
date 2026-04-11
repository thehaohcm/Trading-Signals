<template>
  <div class="max-w-4xl mx-auto py-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Macro Intelligence Hub</h1>
      <button @click="showGroupForm = true" class="bg-blue-500 text-white px-4 py-2 rounded">+ Nhóm mới</button>
      <button @click="generatePrompt" class="bg-yellow-500 text-white px-4 py-2 rounded ml-2">Generate Strategy Prompt</button>
    </div>
    <div v-if="loading" class="text-center py-8">Đang tải dữ liệu...</div>
    <div v-else>
      <GroupCard v-for="group in groups" :key="group.id" :group="group"
        @edit="editGroup(group)" @delete="deleteGroup(group)" @updateConclusion="updateConclusion(group, $event)">
        <div>
          <div class="flex justify-between items-center mb-2">
            <span class="font-semibold">Tin tức</span>
            <button @click="addNews(group)" class="text-xs bg-green-100 px-2 py-1 rounded">+ Thêm tin</button>
          </div>
          <div v-if="news[group.id] && news[group.id].length">
            <NewsItem v-for="item in news[group.id]" :key="item.id" :item="item"
              @toggle="toggleStatus(item)" @edit="editNews(item)" @delete="deleteNews(item)" />
          </div>
          <div v-else class="text-xs text-gray-400">Chưa có tin tức nào.</div>
        </div>
      </GroupCard>
    </div>
    <!-- Forms & Modal -->
    <GroupForm v-if="showGroupForm" :modelValue="editingGroup" @submit="saveGroup" @cancel="resetGroupForm" />
    <NewsItemForm v-if="showNewsForm" :modelValue="editingNews" @submit="saveNews" @cancel="resetNewsForm" />
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
