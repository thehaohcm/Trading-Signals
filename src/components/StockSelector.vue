<template>
  <div>
    <label for="stock-select">Select Stock:</label>
    <select id="stock-select" v-model="selectedStock">
      <option v-for="stock in stocks" :key="stock.symbol" :value="stock.symbol">
        {{ stock.symbol }} - {{ stock.name }}
      </option>
    </select>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';

export default {
  setup() {
    const selectedStock = ref('');
    const stocks = ref([]);

    onMounted(() => {
      // Fetch stocks from VNDirect API here (placeholder)
      stocks.value = [
        { symbol: 'VND', name: 'VNDirect' },
        { symbol: 'FPT', name: 'FPT Corporation' },
        { symbol: 'VIC', name: 'Vingroup' },
      ];
    });

    return {
      selectedStock,
      stocks,
    };
  },
};
</script>

<style scoped>
/* Add component-specific styles here */
</style>