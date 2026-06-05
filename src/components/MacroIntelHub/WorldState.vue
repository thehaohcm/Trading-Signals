<template>
  <div class="world-state-card">
    <div class="ws-header">
      <h3 class="ws-title">🌍 Current World State</h3>
      <span class="ws-updated" v-if="worldState.updated_at">Cập nhật: {{ new Date(worldState.updated_at).toLocaleString() }}</span>
    </div>
    <div v-if="loading" class="text-center py-4">Đang tải...</div>
    <div v-else-if="Object.keys(stateData).length === 0" class="text-muted text-center py-4">Chưa có dữ liệu World State</div>
    <div v-else class="ws-grid">
      <div v-for="(fields, entity) in stateData" :key="entity" class="ws-entity-card">
        <h4 class="entity-title">{{ entity.toUpperCase() }}</h4>
        <div class="field-list">
          <div v-for="(value, key) in fields" :key="key" class="field-item">
            <span class="field-key">{{ key }}:</span>
            <span class="field-value">{{ value }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  worldState: {
    type: Object,
    default: () => ({})
  },
  loading: Boolean
});

const stateData = computed(() => {
  if (!props.worldState.state_json) return {};
  try {
    return props.worldState.state_json;
  } catch(e) {
    return {};
  }
});
</script>

<style scoped>
.world-state-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.08);
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
}
.ws-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  padding-bottom: 1rem;
}
.ws-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}
.ws-updated {
  font-size: 0.85rem;
  color: #64748b;
}
.ws-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}
.ws-entity-card {
  background: #f8fafc;
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 8px;
  padding: 1rem;
}
.entity-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #334155;
  margin: 0 0 0.75rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px dashed rgba(0,0,0,0.1);
}
.field-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.4rem;
  font-size: 0.9rem;
}
.field-key {
  color: #64748b;
  text-transform: capitalize;
}
.field-value {
  font-weight: 600;
  color: #0f172a;
}
</style>
