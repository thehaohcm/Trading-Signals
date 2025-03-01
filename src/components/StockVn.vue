<template>
  <div>
    <v-select v-model="selectedStock" :options="stocks" label="code" @input="onStockSelected" :filter-options="filterOptions"></v-select>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue';
import vSelect from 'vue3-select';

export default {
  name: 'StockVn',
  components: {
    vSelect
  },
  props: {
    searchText: String,
  },
  emits: ['update:searchText', 'update:selectedStock'],
  setup(props, { emit }) {
    const selectedStock = ref(null);
    const stocks = ref([]);

    onMounted(async () => {
      const response = await fetch('https://api-finfo.vndirect.com.vn/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000');
      const data = await response.json();
      stocks.value = data.data;
      emit('update:stocks', stocks.value);
    });

    watch(selectedStock, (newStock) => {
      if (newStock) {
        emit('update:searchText', newStock.code);
      }
      
    })

    const onStockSelected = (value) => {
        emit('update:selectedStock', value);
    }

    const filterOptions = (options, search) => {
      if (!search) {
        return options;
      }
      return options.filter(option =>
        option.code.toLowerCase().includes(search.toLowerCase())
      );
    };

    return {
      selectedStock,
      stocks,
      onStockSelected,
      filterOptions
    };
  },
};
</script>

<style scoped>
/* Add component-specific styles here */
</style>