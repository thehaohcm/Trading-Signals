<template>
  <NavBar />
  <div class="container mt-4">
    <h2>Forex</h2>
    
    <!-- Bootstrap Tabs -->
    <ul class="nav nav-tabs" role="tablist">
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'calendar' }" @click="activeTab = 'calendar'" type="button">
          Economic Calendar
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'prices' }" @click="activeTab = 'prices'" type="button">
          Currency Prices
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'potential' }" @click="activeTab = 'potential'" type="button">
          Potential Forex Pairs
        </button>
      </li>
    </ul>

    <!-- Tab Content -->
    <div class="tab-content mt-3">
      <!-- Currency Prices Tab -->
      <div v-if="activeTab === 'prices'">
        <CurrencyPrices />
      </div>

      <!-- Economic Calendar Tab -->
      <div v-else-if="activeTab === 'calendar'">
        <div v-if="isLoading" class="d-flex justify-content-center">
          <div class="spinner"></div>
        </div>
        <div v-else>
          <div class="mb-3">
            <label for="dateFilter" class="form-label">Filter by Date:</label>
            <div class="input-group">
              <button class="btn btn-outline-secondary" @click="goToPreviousDay" :disabled="isPreviousDisabled">&lt; Previous</button>

              <div style="flex: 1;">
                <input type="date" id="dateFilter" class="form-control" v-model="selectedDate">
                <small style="display:block; margin-top: 5px; font-weight:bold;">
                  {{ formattedDateLong }}
                </small>
              </div>

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

      <!-- Potential Forex Pairs Tab -->
      <div v-else-if="activeTab === 'potential'">
        <div class="text-center mb-4">
          <button class="btn btn-primary btn-lg" @click="scanForexPairs" :disabled="isScanning">
            <span v-if="isScanning" class="spinner-border spinner-border-sm me-2"></span>
            {{ isScanning ? 'Scanning...' : 'Start to scan...' }}
          </button>
        </div>

        <div v-if="forexPairs.length > 0" class="mt-4">
          <div class="alert alert-info">
            <strong>Latest Updated:</strong> {{ formatDateTime(latestUpdated) }}
          </div>
          
          <div style="overflow-x: auto;">
            <table class="table table-striped table-hover">
              <thead>
                <tr>
                  <th>Pair</th>
                  <th>Action</th>
                  <th>Score Diff</th>
                  <th>Note</th>
                  <th>Updated At</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="pair in forexPairs" :key="pair.pair">
                  <td><strong>{{ pair.pair }}</strong></td>
                  <td>
                    <span class="badge" :class="pair.action === 'Buy' ? 'bg-success' : 'bg-danger'">
                      {{ pair.action }}
                    </span>
                  </td>
                  <td>{{ pair.score_diff.toFixed(2) }}%</td>
                  <td>{{ pair.note || '-' }}</td>
                  <td>{{ formatDateTime(pair.updated_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-else-if="!isScanning && scanAttempted" class="alert alert-warning">
          No forex pairs found. Please run the scan.
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
    
    // Forex pairs state
    const forexPairs = ref([]);
    const isScanning = ref(false);
    const scanAttempted = ref(false);
    const latestUpdated = ref(null);

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

    const formattedDateLong = computed(() => {
      if (!selectedDate.value) return '';
      const date = new Date(selectedDate.value);
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    });

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

    const scanForexPairs = async () => {
      isScanning.value = true;
      scanAttempted.value = true;
      try {
        const response = await axios.get('http://localhost:8080/getPotentialForexPairs');
        forexPairs.value = response.data.data || [];
        latestUpdated.value = response.data.latest_updated;
      } catch (error) {
        console.error('Error fetching forex pairs:', error);
        alert('Failed to fetch forex pairs. Please make sure the API server is running.');
      } finally {
        isScanning.value = false;
      }
    };

    const formatDateTime = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString();
    };

    return {
      data,
      sortedData,
      formatDate,
      formattedDateLong,
      isLoading,
      activeTab,
      selectedDate,
      currentDateTime,
      closestItem,
      goToPreviousDay,
      goToNextDay,
      isPreviousDisabled,
      isNextDisabled,
      forexPairs,
      isScanning,
      scanAttempted,
      latestUpdated,
      scanForexPairs,
      formatDateTime
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
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}
</style>