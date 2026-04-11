<template>
  <div class="bg-white rounded-lg shadow p-4 mb-4 border border-gray-100">
    <div class="flex justify-between items-center mb-2">
      <div>
        <h3 class="font-bold text-lg">{{ group.name }}</h3>
        <p class="text-gray-500 text-sm">{{ group.description }}</p>
      </div>
      <div>
        <button @click="$emit('edit')" class="text-blue-500 hover:underline mr-2">Sửa</button>
        <button @click="$emit('delete')" class="text-red-500 hover:underline">Xóa</button>
      </div>
    </div>
    <div>
      <slot></slot>
    </div>
    <div class="mt-4">
      <label class="block text-xs text-gray-500 mb-1">Ghi chú/Nhận định cá nhân</label>
      <textarea v-model="localConclusion" @blur="updateConclusion" rows="2" class="w-full border rounded p-2 text-sm"></textarea>
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
