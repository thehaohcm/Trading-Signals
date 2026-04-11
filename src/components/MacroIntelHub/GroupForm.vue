<template>
  <form @submit.prevent="$emit('submit', group)" class="">
    <div class="mb-3">
      <label class="form-label fw-semibold">Tên nhóm</label>
      <input v-model="group.name" required placeholder="VD: FED, Địa chính trị" class="form-control" />
    </div>
    <div class="mb-3">
      <label class="form-label">Mô tả</label>
      <textarea v-model="group.description" placeholder="Mô tả" class="form-control" rows="2"></textarea>
    </div>
    <div class="d-flex gap-2 justify-content-end mt-3">
      <button type="submit" class="btn btn-primary">Lưu</button>
      <button type="button" @click="$emit('cancel')" class="btn btn-outline-secondary">Hủy</button>
    </div>
  </form>
</template>

<script setup>
import { reactive, watch } from 'vue'
const props = defineProps({
  modelValue: Object
})
const group = reactive({
  name: '',
  description: ''
})
watch(() => props.modelValue, val => {
  if (val) Object.assign(group, val)
}, { immediate: true })
</script>
