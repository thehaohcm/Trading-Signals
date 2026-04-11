<template>
  <div class="flex items-start gap-2 border-b py-2">
    <div class="flex-1">
      <div class="font-semibold">{{ item.title }}</div>
      <div class="text-xs text-gray-500 mb-1">{{ item.content }}</div>
      <div class="text-xs text-blue-500" v-if="item.source_url">
        <a :href="item.source_url" target="_blank">Nguồn</a>
      </div>
    </div>
    <div class="flex flex-col items-end gap-1">
      <span class="text-yellow-500 text-xs">{{ '★'.repeat(item.importance) }}</span>
      <button @click="$emit('toggle')" class="text-xs px-2 py-1 rounded border" :class="item.status === 'active' ? 'bg-green-100 border-green-400' : 'bg-gray-100 border-gray-300'">
        {{ item.status === 'active' ? 'Active' : 'Expired' }}
      </button>
      <button @click="$emit('edit')" class="text-blue-400 text-xs">Sửa</button>
      <button @click="$emit('delete')" class="text-red-400 text-xs">Xóa</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  item: Object
})
</script>
