<template>
  <div class="pending-changes-card" v-if="changes && changes.length > 0">
    <h3 class="pc-title">🔔 Pending AI Proposals</h3>
    <div class="pc-list">
      <div v-for="change in changes" :key="change.id" class="pc-item">
        <div class="pc-info">
          <div class="pc-target"><strong>{{ change.target_entity.toUpperCase() }}</strong>: {{ change.field_name }}</div>
          <div class="pc-diff">
            <span class="old-val">{{ change.old_value || 'None' }}</span> ➡️ <span class="new-val">{{ change.new_value }}</span>
          </div>
          <div class="pc-reason">{{ change.reason }} <span class="conf">(Conf: {{ (change.confidence * 100).toFixed(0) }}%)</span></div>
        </div>
        <div class="pc-actions">
          <button @click="$emit('approve', change.id)" class="btn-approve">✓</button>
          <button @click="$emit('reject', change.id)" class="btn-reject">✕</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  changes: {
    type: Array,
    default: () => []
  }
});
defineEmits(['approve', 'reject']);
</script>

<style scoped>
.pending-changes-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f59e0b;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(245,158,11,0.1);
}
.pc-title {
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #d97706;
}
.pc-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.pc-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
}
.pc-target {
  font-size: 0.95rem;
  color: #92400e;
  margin-bottom: 0.25rem;
}
.pc-diff {
  font-size: 1.05rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}
.old-val { color: #ef4444; text-decoration: line-through; }
.new-val { color: #10b981; }
.pc-reason {
  font-size: 0.85rem;
  color: #b45309;
}
.conf {
  font-weight: 600;
  color: #d97706;
}
.pc-actions {
  display: flex;
  gap: 0.5rem;
}
.btn-approve {
  background: #10b981; color: white; border: none; border-radius: 6px; width: 36px; height: 36px; font-weight: bold; cursor: pointer; transition: 0.2s;
}
.btn-approve:hover { background: #059669; }
.btn-reject {
  background: #ef4444; color: white; border: none; border-radius: 6px; width: 36px; height: 36px; font-weight: bold; cursor: pointer; transition: 0.2s;
}
.btn-reject:hover { background: #dc2626; }
</style>
