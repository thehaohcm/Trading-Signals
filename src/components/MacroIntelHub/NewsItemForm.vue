<template>
  <form @submit.prevent="onSubmit">
    <div class="mb-3">
      <label class="form-label fw-semibold">Tiêu đề</label>
      <input v-model="form.title" required placeholder="Tiêu đề" class="form-control" />
    </div>
    <div class="mb-3">
      <label class="form-label">Nội dung</label>
      <textarea v-model="form.content" required placeholder="Nội dung" class="form-control" rows="2"></textarea>
    </div>
    <div class="mb-3">
      <label class="form-label">Nguồn (URL)</label>
      <input v-model="form.source_url" placeholder="Nguồn (URL)" class="form-control" />
    </div>
    <div class="mb-3">
      <label class="form-label">Mức độ quan trọng</label>
      <select v-model.number="form.importance" class="form-select w-auto d-inline-block ms-2">
        <option v-for="n in 5" :key="n" :value="n">{{ n }} sao</option>
      </select>
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
const emit = defineEmits(['update:modelValue', 'submit', 'cancel'])
const form = reactive({
  title: '',
  content: '',
  source_url: '',
  importance: 3
})
watch(() => props.modelValue, val => {
  if (val) Object.assign(form, val)
}, { immediate: true })
function onSubmit() {
  emit('submit', { ...form })
}
</script>
