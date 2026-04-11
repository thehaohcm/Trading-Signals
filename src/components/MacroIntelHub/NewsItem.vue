<template>
  <div class="card mb-2 shadow-sm">
    <div class="card-body p-3 d-flex flex-column flex-md-row align-items-md-center justify-content-between">
      <div class="flex-grow-1">
        <div class="fw-bold mb-1">{{ item.title }}</div>
        <div class="text-muted small mb-1">{{ item.content }}</div>
        <div v-if="item.source_url" class="mb-1">
          <a :href="item.source_url" target="_blank" class="badge bg-info text-dark">Nguồn</a>
        </div>
        <span class="badge bg-warning text-dark">{{ item.importance }} ★</span>
      </div>
      <div class="d-flex flex-column align-items-end gap-1 mt-2 mt-md-0 ms-md-3">
        <button @click="$emit('toggle')" class="btn btn-sm" :class="item.status === 'active' ? 'btn-success' : 'btn-outline-secondary'">
          {{ item.status === 'active' ? 'Active' : 'Expired' }}
        </button>
        <button @click="$emit('edit')" class="btn btn-outline-primary btn-sm">Sửa</button>
        <button @click="$emit('delete')" class="btn btn-outline-danger btn-sm">Xóa</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  item: Object
})
</script>
