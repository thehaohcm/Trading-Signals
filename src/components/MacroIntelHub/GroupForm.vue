<template>
  <form @submit.prevent="$emit('submit', group)" class="space-y-2">
    <input v-model="group.name" required placeholder="Tên nhóm (VD: FED, Địa chính trị)" class="w-full border rounded p-2 text-sm" />
    <textarea v-model="group.description" placeholder="Mô tả" class="w-full border rounded p-2 text-sm"></textarea>
    <div class="flex gap-2">
      <button type="submit" class="bg-blue-500 text-white px-3 py-1 rounded">Lưu</button>
      <button type="button" @click="$emit('cancel')" class="bg-gray-200 px-3 py-1 rounded">Hủy</button>
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
