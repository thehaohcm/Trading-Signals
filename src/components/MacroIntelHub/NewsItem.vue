<template>
  <div class="news-item" :class="{ 'news-expired': item.status !== 'active' }">
    <div class="ni-top">
      <div class="ni-info">
        <h4 class="ni-title">{{ item.title }}</h4>
        <p class="ni-content" :class="{ 'ni-expanded': isExpanded }">{{ item.content }}</p>
        <div class="ni-meta-actions">
          <a v-if="item.source_url" :href="item.source_url" target="_blank" rel="noopener noreferrer" class="ni-source">
            Nguồn
          </a>
          <button 
            v-if="item.content && item.content.length > 100" 
            @click="isExpanded = !isExpanded" 
            class="ni-expand-btn"
          >
            <span>{{ isExpanded ? 'Thu gọn' : 'Xem thêm' }}</span>
            <svg class="chevron-icon" :class="{ 'rotate-180': isExpanded }" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width: 10px; height: 10px;">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
        </div>
      </div>
      <span class="ni-importance" :class="'ni-imp-' + item.importance">
        {{ item.importance }}
      </span>
    </div>
    <div class="ni-bottom">
      <button v-if="showActions" @click="$emit('toggle')" class="ni-status-btn" :class="item.status === 'active' ? 'ni-active' : 'ni-inactive'">
        {{ item.status === 'active' ? 'Active' : 'Expired' }}
      </button>
      <span v-else class="ni-status-badge" :class="item.status === 'active' ? 'badge-active' : 'badge-inactive'">
        {{ item.status === 'active' ? 'Active' : 'Expired' }}
      </span>

      <div v-if="showActions" class="ni-actions">
        <button @click="$emit('edit')" class="ni-act-btn" title="Sửa">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M11.5 1.5l3 3L5 14H2v-3L11.5 1.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button @click="$emit('delete')" class="ni-act-btn ni-act-danger" title="Xóa">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M5.33 4V2.67a1.33 1.33 0 011.34-1.34h2.66a1.33 1.33 0 011.34 1.34V4m2 0v9.33a1.33 1.33 0 01-1.34 1.34H4.67a1.33 1.33 0 01-1.34-1.34V4h9.34z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  item: Object,
  showActions: {
    type: Boolean,
    default: true
  }
})
defineEmits(['toggle', 'edit', 'delete'])

const isExpanded = ref(false)
</script>

<style scoped>
.news-item {
  background: rgba(10, 13, 20, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 0.85rem 1rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.news-item:hover {
  border-color: rgba(0, 242, 254, 0.25);
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}
.news-expired {
  opacity: 0.55;
  background: rgba(10, 13, 20, 0.3);
}

/* ── Top row ── */
.ni-top {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  margin-bottom: 0.65rem;
}
.ni-info {
  flex: 1;
  min-width: 0;
}
.ni-title {
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 0.3rem;
  font-size: 0.9rem;
  line-height: 1.35;
}
.ni-content {
  font-size: 0.82rem;
  color: #cbd5e1;
  margin: 0;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: max-height 0.25s ease;
}
.ni-content.ni-expanded {
  display: block;
  -webkit-line-clamp: unset;
  line-clamp: unset;
  overflow: visible;
}
.ni-meta-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.4rem;
}
.ni-source {
  display: inline-block;
  font-size: 0.78rem;
  color: #00f2fe;
  text-decoration: none;
  font-weight: 500;
}
.ni-source:hover {
  color: #38bdf8;
  text-decoration: underline;
}

/* ── Importance badge ── */
.ni-importance {
  flex-shrink: 0;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
}
.ni-imp-1 { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
.ni-imp-2 { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.ni-imp-3 { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.ni-imp-4 { background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.3); }
.ni-imp-5 { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }

/* ── Bottom row ── */
.ni-bottom {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.ni-status-btn {
  flex: 1;
  padding: 0.35rem 0.6rem;
  border: none;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  text-align: left;
}
.ni-active {
  background: rgba(0, 245, 160, 0.1);
  color: #00f5a0;
  border: 1px solid rgba(0, 245, 160, 0.25);
}
.ni-active:hover { background: rgba(0, 245, 160, 0.2); }
.ni-inactive {
  background: rgba(148, 163, 184, 0.08);
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.18);
}
.ni-inactive:hover { background: rgba(148, 163, 184, 0.15); }

.ni-actions {
  display: flex;
  gap: 0.35rem;
}
.ni-act-btn {
  width: 30px;
  height: 30px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.04);
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.ni-act-btn:hover {
  background: rgba(0, 242, 254, 0.12);
  color: #00f2fe;
  border-color: rgba(0, 242, 254, 0.3);
}
.ni-act-danger:hover {
  background: rgba(255, 75, 114, 0.12);
  color: #ff4b72;
  border-color: rgba(255, 75, 114, 0.3);
}

@media (max-width: 640px) {
  .news-item {
    padding: 0.7rem 0.8rem;
  }
  .ni-title {
    font-size: 0.85rem;
  }
}

.ni-status-badge {
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
}
.badge-active {
  background: rgba(0, 245, 160, 0.1);
  color: #00f5a0;
  border: 1px solid rgba(0, 245, 160, 0.25);
}
.badge-inactive {
  background: rgba(148, 163, 184, 0.08);
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.ni-expand-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: none;
  border: none;
  padding: 0;
  font-size: 0.78rem;
  color: #00f2fe;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.15s ease;
}
.ni-expand-btn:hover {
  color: #38bdf8;
}
.chevron-icon {
  transition: transform 0.2s ease;
}
.chevron-icon.rotate-180 {
  transform: rotate(180deg);
}
</style>
