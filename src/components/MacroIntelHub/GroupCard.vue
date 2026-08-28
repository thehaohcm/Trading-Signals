<template>
  <div class="group-card">
    <div class="group-card-header">
      <div class="group-card-info">
        <h3 class="group-title">{{ group.name }}</h3>
        <p v-if="group.description" class="group-desc">{{ group.description }}</p>
      </div>
      <div class="group-card-actions" v-if="!isReadOnly">
        <button @click="$emit('edit')" class="gc-action-btn" title="Sửa">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M11.5 1.5l3 3L5 14H2v-3L11.5 1.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button @click="$emit('delete')" class="gc-action-btn gc-action-danger" title="Xóa">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M5.33 4V2.67a1.33 1.33 0 011.34-1.34h2.66a1.33 1.33 0 011.34 1.34V4m2 0v9.33a1.33 1.33 0 01-1.34 1.34H4.67a1.33 1.33 0 01-1.34-1.34V4h9.34z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>
    </div>

    <div class="group-card-body">
      <slot></slot>
    </div>

    <div class="group-card-footer">
      <label class="conclusion-label">💭 Ghi chú / Nhận định</label>
      <textarea v-model="localConclusion" @blur="updateConclusion" rows="2" :disabled="isReadOnly"
        class="conclusion-textarea" placeholder="Viết nhận định cá nhân của bạn..."></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({
  group: Object,
  isReadOnly: {
    type: Boolean,
    default: false
  }
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
  background: rgba(18, 24, 38, 0.75);
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  transition: all 0.25s ease;
  overflow: hidden;
  backdrop-filter: blur(16px);
}
.group-card:hover {
  box-shadow: 0 12px 35px rgba(0, 242, 254, 0.1);
  border-color: rgba(0, 242, 254, 0.3);
}

/* ── Header ── */
.group-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.25rem 1.25rem 0;
}
.group-card-info {
  flex: 1;
  min-width: 0;
}
.group-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 0.35rem;
  line-height: 1.3;
}
.group-desc {
  color: #94a3b8;
  font-size: 0.88rem;
  margin: 0;
  line-height: 1.45;
}

/* ── Action buttons ── */
.group-card-actions {
  display: flex;
  gap: 0.4rem;
  flex-shrink: 0;
}
.gc-action-btn {
  width: 34px;
  height: 34px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}
.gc-action-btn:hover {
  background: rgba(0, 242, 254, 0.12);
  color: #00f2fe;
  border-color: rgba(0, 242, 254, 0.3);
}
.gc-action-danger:hover {
  background: rgba(255, 75, 114, 0.12);
  color: #ff4b72;
  border-color: rgba(255, 75, 114, 0.3);
}

/* ── Body ── */
.group-card-body {
  padding: 1rem 1.25rem;
}

/* ── Footer / Conclusion ── */
.group-card-footer {
  padding: 0 1.25rem 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 1rem;
}
.conclusion-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-bottom: 0.5rem;
}
.conclusion-textarea {
  width: 100%;
  padding: 0.6rem 0.85rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  font-size: 0.88rem;
  font-family: inherit;
  background: rgba(10, 13, 20, 0.8);
  color: #ffffff;
  transition: border-color 0.15s, box-shadow 0.15s;
  resize: vertical;
  line-height: 1.5;
}
.conclusion-textarea:focus {
  outline: none;
  border-color: #00f2fe;
  background: rgba(10, 13, 20, 0.95);
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15);
}
.conclusion-textarea::placeholder {
  color: #64748b;
}

@media (max-width: 640px) {
  .group-card-header {
    padding: 1rem 1rem 0;
  }
  .group-card-body {
    padding: 0.75rem 1rem;
  }
  .group-card-footer {
    padding: 0 1rem 1rem;
    padding-top: 0.75rem;
  }
  .group-title {
    font-size: 1.05rem;
  }
}
</style>
