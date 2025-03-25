<template>
  <div>
    <h2>Currency Prices</h2>
    <div v-if="isLoading" class="d-flex justify-content-center">
        <div class="spinner"></div>
    </div>
    <div style="overflow-x: auto;">
        <table v-else class="table table-striped">
        <thead>
            <tr>
            <th>Currency</th>
            <th>Rate</th>
            <th>Bid</th>
            <th>Ask</th>
            <th>High</th>
            <th>Low</th>
            <th>Open</th>
            <th>Close</th>
            <th>Timestamp</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="item in currencyData" :key="item.currency">
            <td>{{ item.currency }}</td>
            <td>{{ item.rate }}</td>
            <td>{{ item.bid }}</td>
            <td>{{ item.ask }}</td>
            <td>{{ item.high }}</td>
            <td>{{ item.low }}</td>
            <td>{{ item.open }}</td>
            <td>{{ item.close }}</td>
            <td>{{ item.timestamp }}</td>
            </tr>
        </tbody>
        </table>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import axios from 'axios';

export default {
  setup() {
    const currencyData = ref([]);
    const isLoading = ref(false);

    onMounted(async () => {
      isLoading.value = true;
      try {
        const response = await axios.get('/api/rates'); // Use proxy
        currencyData.value = response.data;
      } catch (error) {
        console.error('Error fetching currency data:', error);
      } finally {
        isLoading.value = false;
      }
    });

    return {
      currencyData,
      isLoading
    };
  },
};
</script>
<style scoped>
.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #09f;
  animation: spin 1s ease infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}
</style>