<template>
  <form @submit.prevent="onSubmit" class="space-y-2">
    <input v-model="form.title" required placeholder="Tiêu đề" class="w-full border rounded p-2 text-sm" />
    <textarea v-model="form.content" required placeholder="Nội dung" class="w-full border rounded p-2 text-sm"></textarea>
    <input v-model="form.source_url" placeholder="Nguồn (URL)" class="w-full border rounded p-2 text-sm" />
    <div class="flex items-center gap-2">
      <label class="text-xs">Mức độ quan trọng:</label>
      <select v-model.number="form.importance" class="border rounded p-1">
        <option v-for="n in 5" :key="n" :value="n">{{ n }} sao</option>
      </select>
    </div>
    <div class="flex gap-2">
      <button type="submit" class="bg-blue-500 text-white px-3 py-1 rounded">Lưu</button>
      <button type="button" @click="$emit('cancel')" class="bg-gray-200 px-3 py-1 rounded">Hủy</button>
    </div>
  </form>
</template>

<script setup>
import { reactive, watch, toRefs } from 'vue'
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
