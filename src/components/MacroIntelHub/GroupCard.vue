<template>
  <div class="group-card">
    <div class="group-card-header">
      <div class="flex-1">
        <h3 class="group-title">{{ group.name }}</h3>
        <p class="group-description">{{ group.description }}</p>
      </div>
      <div class="group-actions">
        <button @click="$emit('edit')" class="action-btn edit-btn" title="Sửa">✏️</button>
        <button @click="$emit('delete')" class="action-btn delete-btn" title="Xóa">🗑️</button>
      </div>
    </div>
    <div class="mt-4">
      <slot></slot>
    </div>
    <div class="conclusion-section">
      <label class="conclusion-label">💭 Ghi chú/Nhận định cá nhân</label>
      <textarea v-model="localConclusion" @blur="updateConclusion" rows="2" class="conclusion-textarea"></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({
  group: Object
})
const emit = defineEmits(['updateConclusion', 'edit', 'delete'])
const localConclusion = ref(props.group.conclusion || '')
watch(() => props.group.conclusion, val => localConclusion.value = val)
function updateConclusion() {
  emit('updateConclusion', localConclusion.value)
}
</script>

<style scoped>
.group-card {
  background: #fff;
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: cardIn 0.3s ease-out;
}

@keyframes cardIn {
  0% {
    opacity: 0;
    transform: translateY(10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.group-card:hover {
  box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.12);
  border-color: #cbd5e1;
  transform: translateY(-4px);
}

.group-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.group-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.5rem 0;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.group-description {
  color: #64748b;
  font-size: 0.9rem;
  margin: 0;
  line-height: 1.4;
}

.group-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  transform: scale(1.05);
}

.edit-btn:hover {
  border-color: #3b82f6;
}

.delete-btn:hover {
  border-color: #ef4444;
}

.conclusion-section {
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.conclusion-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.75rem;
}

.conclusion-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  font-family: inherit;
  background: #f8fafc;
  color: #334155;
  transition: all 0.2s;
  resize: vertical;
  line-height: 1.5;
}

.conclusion-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.conclusion-textarea::placeholder {
  color: #94a3b8;
}

@media (max-width: 640px) {
  .group-card {
    padding: 1rem;
  }

  .group-title {
    font-size: 1.1rem;
  }

  .group-card-header {
    flex-direction: column;
  }

  .group-actions {
    margin-top: 0.75rem;
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
