<template>
  <div class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-xl relative">
      <button @click="$emit('close')" class="absolute top-2 right-2 text-gray-400 hover:text-black">✕</button>
      <h2 class="font-bold text-lg mb-2">AI Strategy Prompt</h2>
      <textarea readonly :value="prompt" class="w-full border rounded p-2 text-sm mb-2" rows="10"></textarea>
      <button @click="copy" class="bg-blue-500 text-white px-4 py-2 rounded">Copy</button>
      <span v-if="copied" class="ml-2 text-green-500 text-xs">Đã copy!</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({ prompt: String })
const copied = ref(false)
function copy() {
  navigator.clipboard.writeText(props.prompt)
  copied.value = true
  setTimeout(() => copied.value = false, 1200)
}
</script>
