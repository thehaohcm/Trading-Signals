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
      </div>

      <!-- World State & Pending Changes (OSINT) -->
      <PendingChangesComponent :changes="pendingChanges" @approve="approveChange" @reject="rejectChange" />
      <WorldStateComponent :worldState="worldState" :loading="loadingState" />
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue'
import AppFooter from '../components/AppFooter.vue'

import { ref, onMounted } from 'vue'
import WorldStateComponent from '../components/MacroIntelHub/WorldState.vue'
import PendingChangesComponent from '../components/MacroIntelHub/PendingChanges.vue'

// OSINT State
const worldState = ref({})
const pendingChanges = ref([])
const loadingState = ref(false)

function authHeader() {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

onMounted(() => {
  fetchWorldState()
  fetchPendingChanges()
})

function fetchWorldState() {
  loadingState.value = true
  fetch('/api/osint/world-state', { headers: authHeader() })
    .then(r => r.json())
    .then(data => worldState.value = data || {})
    .catch(e => console.error('fetchWorldState error:', e))
    .finally(() => loadingState.value = false)
}

function fetchPendingChanges() {
  fetch('/api/osint/changes/pending', { headers: authHeader() })
    .then(r => r.json())
    .then(data => pendingChanges.value = data || [])
    .catch(e => console.error('fetchPendingChanges error:', e))
}

function approveChange(id) {
  fetch(`/api/osint/changes/${id}/approve`, { method: 'POST', headers: authHeader() })
    .then(r => {
      if (r.ok) {
        fetchWorldState();
        fetchPendingChanges();
      }
    })
}

function rejectChange(id) {
  fetch(`/api/osint/changes/${id}/reject`, { method: 'POST', headers: authHeader() })
    .then(r => {
      if (r.ok) {
        fetchPendingChanges();
      }
    })
}
</script>

<style scoped>
/* ======================================= */
/*  MACRO HUB – Premium Terminal Theme     */
/* ======================================= */

.hub-container-wrapper {
  background: #f8fafc;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ── Container ── */
.macro-hub-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem;
  color: #1e293b;
}

/* ── Header ── */
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

/* ── Responsive ── */
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
}
</style>
