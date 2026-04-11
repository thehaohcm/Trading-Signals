<template>
  <div class="news-item">
    <div class="news-item-header">
      <div class="news-item-left">
        <h4 class="news-title">{{ item.title }}</h4>
        <p class="news-content">{{ item.content }}</p>
      </div>
      <div class="news-importance">
        <span class="importance-badge" :class="'importance-' + item.importance">
          {{ item.importance }}⭐
        </span>
      </div>
    </div>
    
    <div v-if="item.source_url" class="news-meta">
      <a :href="item.source_url" target="_blank" rel="noopener noreferrer" class="source-link">
        🔗 Xem nguồn
      </a>
    </div>

    <div class="news-actions">
      <button @click="$emit('toggle')" class="status-btn" :class="statusClass">
        {{ item.status === 'active' ? '✓ Đang theo dõi' : '⏸ Hết hiệu lực' }}
      </button>
      <button @click="$emit('edit')" class="action-icon-btn" title="Sửa">✏️</button>
      <button @click="$emit('delete')" class="action-icon-btn delete" title="Xóa">🗑️</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: Object
})

const emit = defineEmits(['toggle', 'edit', 'delete'])

const statusClass = computed(() => {
  return props.item.status === 'active' ? 'status-active' : 'status-expired'
})
</script>

<style scoped>
.news-item {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.news-item:hover {
  background: linear-gradient(135deg, #f1f5f9 0%, #fff 100%);
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.news-item-header {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.news-item-left {
  flex: 1;
}

.news-title {
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.5rem 0;
  font-size: 0.95rem;
  line-height: 1.4;
}

.news-content {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
  line-height: 1.5;
}

.news-importance {
  display: flex;
  justify-content: flex-end;
}

.importance-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.importance-1 {
  background: #dbeafe;
  color: #0369a1;
}

.importance-2 {
  background: #d1fae5;
  color: #065f46;
}

.importance-3 {
  background: #fef3c7;
  color: #854d0e;
}

.importance-4 {
  background: #fed7aa;
  color: #92400e;
}

.importance-5 {
  background: #fee2e2;
  color: #991b1b;
}

.news-meta {
  margin-bottom: 0.75rem;
}

.source-link {
  display: inline-block;
  padding: 0.4rem 0.8rem;
  background: #3b82f6;
  color: white;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.8rem;
  font-weight: 500;
  transition: all 0.2s;
}

.source-link:hover {
  background: #2563eb;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
  transform: translateY(-1px);
}

.news-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.status-btn {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
}

.status-active {
  background: #d1fae5;
  color: #065f46;
}

.status-active:hover {
  background: #a7f3d0;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

.status-expired {
  background: #f3f4f6;
  color: #6b7280;
}

.status-expired:hover {
  background: #e5e7eb;
}

.action-icon-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-icon-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  transform: scale(1.05);
}

.action-icon-btn.delete:hover {
  background: #fee2e2;
  border-color: #fca5a5;
}

@media (max-width: 640px) {
  .news-item {
    padding: 0.75rem;
  }

  .news-item-header {
    flex-direction: column;
  }

  .news-actions {
    width: 100%;
  }

  .status-btn {
    font-size: 0.75rem;
    padding: 0.4rem 0.6rem;
  }
}
</style>
