<template>
  <NavBar />
  <div class="container mt-4">
    <h2>Forex</h2>
    <v-tabs>
      <v-tab>Currency Prices</v-tab>
      <v-tab>Economic Calendar</v-tab>

      <v-tab-item>
        <CurrencyPrices />
      </v-tab-item>
      <v-tab-item>
        <div v-if="isLoading" class="d-flex justify-content-center">
            <div class="spinner"></div>
        </div>
        <table v-else class="table table-striped">
          <thead>
            <tr>
              <th>Date</th>
              <th>Country</th>
              <th>Title</th>
              <th>Impact</th>
              <th>Forecast</th>
              <th>Previous</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sortedData" :key="item.date + item.title">
              <td>{{ formatDate(item.date) }}</td>
              <td><strong>{{ item.country }}</strong></td>
              <td style="text-align: left;"><strong>{{ item.title }}</strong></td>
              <td>{{ item.impact }}</td>
              <td>{{ item.forecast }}</td>
              <td>{{ item.previous }}</td>
            </tr>
          </tbody>
        </table>
      </v-tab-item>
    </v-tabs>
  </div>
  <AppFooter />
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import CurrencyPrices from './CurrencyPrices.vue';
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

export default {
  components: {
    NavBar,
    AppFooter,
    CurrencyPrices
  },
  setup() {
    const data = ref([]);
    const isLoading = ref(false);

    onMounted(async () => {
      isLoading.value = true;
      try {
        const response = await axios.get('/ff_calendar_thisweek.json');
        data.value = response.data;
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        isLoading.value = false;
      }
    });

    const sortedData = computed(() => {
      return [...data.value].sort((a, b) => new Date(a.date) - new Date(b.date));
    });

    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleString(); // Or any other desired format
    }

    return {
      data,
      sortedData,
      formatDate,
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