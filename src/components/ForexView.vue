<template>
  <NavBar />
  <div class="container mt-4">
    <h2>Forex</h2>
    <div>
      <button class="btn btn-primary me-2" @click="activeTab = 'calendar'">Economic Calendar</button>
      <button class="btn btn-primary" @click="activeTab = 'prices'">Currency Prices</button>
    </div>
    <br />

    <div v-if="activeTab === 'prices'">
      <CurrencyPrices />
    </div>
    <div v-else-if="activeTab === 'calendar'">
      <div v-if="isLoading" class="d-flex justify-content-center">
        <div class="spinner"></div>
      </div>
      <div v-else>
        <div class="mb-3">
          <label for="dateFilter" class="form-label">Filter by Date:</label>
          <div class="input-group">
            <button class="btn btn-outline-secondary" @click="goToPreviousDay" :disabled="isPreviousDisabled">&lt; Previous</button>
            <input type="date" id="dateFilter" class="form-control" v-model="selectedDate">
            <button class="btn btn-outline-secondary" @click="goToNextDay" :disabled="isNextDisabled">Next &gt;</button>
          </div>
        </div>
        <div style="overflow-x: auto;">
          <table class="table table-striped">
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
              <tr v-for="item in sortedData" :key="item.date + item.title" :class="{ 'highlight': item === closestItem }">
                <td>{{ formatDate(item.date) }}</td>
                <td><strong>{{ item.country }}</strong></td>
                <td style="text-align: left;"><strong>{{ item.title }}</strong></td>
                <td>{{ item.impact }}</td>
                <td>{{ item.forecast }}</td>
                <td>{{ item.previous }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
  <AppFooter />
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import CurrencyPrices from './CurrencyPrices.vue';
import { ref, onMounted, computed, onUnmounted } from 'vue';
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
    const activeTab = ref('calendar'); // Initialize with 'calendar' as the default
    const currentDateTime = ref(new Date());

    // Initialize selectedDate with the current date in YYYY-MM-DD format
    const today = new Date();
    const formattedToday = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
    const selectedDate = ref(formattedToday);


    let intervalId;

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

      intervalId = setInterval(() => {
        currentDateTime.value = new Date();
      }, 1000);
    });

    onUnmounted(() => {
      clearInterval(intervalId);
    });


    const sortedData = computed(() => {
      let filteredData = [...data.value];

      if (selectedDate.value) {
        const selected = new Date(selectedDate.value);
        filteredData = filteredData.filter(item => {
          const itemDate = new Date(item.date);
          return itemDate.getFullYear() === selected.getFullYear() &&
                 itemDate.getMonth() === selected.getMonth() &&
                 itemDate.getDate() === selected.getDate();
        });
      }

      return filteredData.sort((a, b) => new Date(a.date) - new Date(b.date));
    });

    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleString();
    };

    const closestItem = computed(() => {
      if (sortedData.value.length === 0) {
        return null;
      }

      let minDiff = Infinity;
      let closest = null;

      for (const item of sortedData.value) {
        const itemDate = new Date(item.date);
        const diff = Math.abs(currentDateTime.value - itemDate);
        if (diff < minDiff) {
          minDiff = diff;
          closest = item;
        }
      }
      if (closest) {
        return closest;
      }

      // If no closest item is found in the current filtered data, find the next available date
      const sortedDates = [...new Set(data.value.map(item => item.date))].sort((a, b) => new Date(a) - new Date(b));
      let nextDate = null;

      if (selectedDate.value) {
        const selected = new Date(selectedDate.value);
        for (const dateString of sortedDates) {
          const date = new Date(dateString);
          if (date > selected) {
            nextDate = dateString;
            break;
          }
        }
      } else {
        // If no date is selected, use the earliest date
        nextDate = sortedDates[0];
      }


      // If a next date is found, return the first item from that date
      if (nextDate) {
        return data.value.find(item => item.date === nextDate);
      }

      return null; // Return null if no next date is available
    });
    const isPreviousDisabled = computed(() => {
      if (!selectedDate.value) {
        return false; // Or true, depending on initial state
      }
      const currentDate = new Date(selectedDate.value);
      currentDate.setDate(currentDate.getDate() - 1);
      const prevDateString = currentDate.getFullYear() + '-' + String(currentDate.getMonth() + 1).padStart(2, '0') + '-' + String(currentDate.getDate()).padStart(2, '0');
      return !data.value.some(item => {
        const itemDate = new Date(item.date);
        const itemDateString = itemDate.getFullYear() + '-' + String(itemDate.getMonth() + 1).padStart(2, '0') + '-' + String(itemDate.getDate()).padStart(2, '0');
        return itemDateString === prevDateString;
      });
    });

    const isNextDisabled = computed(() => {
      if (!selectedDate.value) {
        return false;
      }
      const currentDate = new Date(selectedDate.value);
      currentDate.setDate(currentDate.getDate() + 1);
      const nextDateString = currentDate.getFullYear() + '-' + String(currentDate.getMonth() + 1).padStart(2, '0') + '-' + String(currentDate.getDate()).padStart(2, '0');
      return !data.value.some(item => {
        const itemDate = new Date(item.date);
        const itemDateString = itemDate.getFullYear() + '-' + String(itemDate.getMonth() + 1).padStart(2, '0') + '-' + String(itemDate.getDate()).padStart(2, '0');
        return itemDateString === nextDateString;
      });
    });

    const goToPreviousDay = () => {
      if (selectedDate.value) {
        const currentDate = new Date(selectedDate.value);
        currentDate.setDate(currentDate.getDate() - 1);
        selectedDate.value = currentDate.getFullYear() + '-' + String(currentDate.getMonth() + 1).padStart(2, '0') + '-' + String(currentDate.getDate()).padStart(2, '0');
      }
    };

    const goToNextDay = () => {
      if (selectedDate.value) {
        const currentDate = new Date(selectedDate.value);
        currentDate.setDate(currentDate.getDate() + 1);
        selectedDate.value = currentDate.getFullYear() + '-' + String(currentDate.getMonth() + 1).padStart(2, '0') + '-' + String(currentDate.getDate()).padStart(2, '0');
      }
    };

    return {
      data,
      sortedData,
      formatDate,
      isLoading,
      activeTab,
      selectedDate,
      currentDateTime,
      closestItem,
      goToPreviousDay,
      goToNextDay,
      isPreviousDisabled,
      isNextDisabled
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

.highlight {
  border: 2px solid black; /* Or any other desired highlighting style */
}
</style>