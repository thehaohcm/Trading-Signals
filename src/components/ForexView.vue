<template>
  <div class="page-wrapper">
    <NavBar />
    <div class="container mt-4 flex-grow-1">
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
        <div v-if="forexPairs.length > 0" class="mt-4">
          <div class="alert alert-info">
            <strong>Latest Updated:</strong> {{ formatDateTime(latestUpdated) }}
          </div>

          <!-- TradingView Chart - Fixed Position Overlay -->
          <div v-if="selectedPair" class="chart-overlay">
            <div class="chart-container">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <h4 class="mb-0">{{ selectedPair }} Chart</h4>
                <button class="btn btn-sm btn-danger" @click="closeChart">
                  ✕ Close
                </button>
              </div>
              <TradingViewChart :coin="`FX:${selectedPair}`" />
              
              <!-- Price Alert Widget for Forex -->
              <PriceAlertWidget 
                v-if="selectedPair"
                :symbol="selectedPair" 
                assetType="forex" 
              />
            </div>
          </div>
          
          <div style="overflow-x: auto;">
            <table class="table table-striped table-hover forex-table">
              <thead>
                <tr>
                  <th class="text-center">Pair</th>
                  <th class="text-center">Action</th>
                  <th class="text-center">Score Diff</th>
                  <th class="text-center">Note</th>
                  <th class="text-center">Updated At</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="pair in forexPairs" :key="pair.pair" @click="selectPair(pair)" class="cursor-pointer">
                  <td class="text-center"><strong>{{ pair.pair }}</strong></td>
                  <td class="text-center">
                    <span class="badge" :class="pair.action === 'Buy' ? 'bg-success' : 'bg-danger'">
                      {{ pair.action }}
                    </span>
                  </td>
                  <td class="text-center">{{ pair.score_diff.toFixed(2) }}%</td>
                  <td class="text-center">{{ pair.note || '-' }}</td>
                  <td class="text-center">{{ formatDateTime(pair.updated_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-else-if="!isScanning && scanAttempted" class="alert alert-warning">
          No forex pairs found. Please run the scan.
        </div>

        <div class="text-center my-4">
          <button class="btn btn-primary btn-lg" @click="scanForexPairs" :disabled="isScanning">
            <span v-if="isScanning" class="spinner-border spinner-border-sm me-2"></span>
            {{ isScanning ? 'Scanning...' : 'Start to scan...' }}
          </button>
        </div>
      </div>
    </div>
    </div>
    <AppFooter />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import CurrencyPrices from './CurrencyPrices.vue';
import TradingViewChart from './TradingViewChart.vue';
import PriceAlertWidget from './PriceAlertWidget.vue';
import { ref, onMounted, computed, onUnmounted } from 'vue';
import axios from 'axios';

export default {
  components: {
    NavBar,
    AppFooter,
    CurrencyPrices,
    TradingViewChart,
    PriceAlertWidget
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
    const selectedPair = ref(null);

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
        const response = await axios.get('/getPotentialForexPairs');
        forexPairs.value = response.data.data || [];
        latestUpdated.value = response.data.latest_updated;
        
        // Show notification based on data
        if (forexPairs.value.length === 0) {
          alert('No forex pairs available at the moment.');
        }
      } catch (error) {
        console.error('Error fetching forex pairs:', error);
        forexPairs.value = [];
        alert('Failed to fetch forex pairs. Please try again later.');
      } finally {
        isScanning.value = false;
      }
    };

    const formatDateTime = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString();
    };

    const selectPair = (pair) => {
      selectedPair.value = pair.pair;
    };

    const closeChart = () => {
      selectedPair.value = null;
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
      formatDateTime,
      selectedPair,
      selectPair,
      closeChart
    };
  },
};
</script>
<style scoped>
.page-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.flex-grow-1 {
  flex: 1;
}

.nav-tabs {
  border-bottom: 2px solid #dee2e6;
  flex-wrap: nowrap;
  overflow-x: auto;
  display: flex;
  justify-content: flex-start;
  gap: 0.5rem;
}

.nav-tabs .nav-item {
  flex: 1 1 0;
  min-width: 200px;
}

.nav-tabs .nav-link {
  color: #6c757d;
  background-color: #f8f9fa;
  border: 1px solid transparent;
  border-radius: 0.375rem 0.375rem 0 0;
  margin-right: 0;
  padding: 0.875rem 1.5rem;
  font-weight: 500;
  transition: all 0.3s ease;
  white-space: nowrap;
  flex-shrink: 0;
  font-size: 1rem;
  width: 100%;
  text-align: center;
}

.nav-tabs .nav-link:hover {
  background-color: #e9ecef;
  color: #495057;
  border-color: #dee2e6 #dee2e6 transparent;
}

.nav-tabs .nav-link.active {
  color: #0d6efd;
  background-color: #ffffff;
  border-color: #dee2e6 #dee2e6 #ffffff;
  border-bottom: 2px solid #ffffff;
  margin-bottom: -2px;
}

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
  border: 2px solid black;
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

.cursor-pointer {
  cursor: pointer;
}

.cursor-pointer:hover {
  background-color: #e9ecef !important;
}

.chart-overlay {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  max-width: 1200px;
  max-height: 85vh;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  z-index: 1050;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  animation: fadeIn 0.3s ease;
}

.chart-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  max-height: calc(85vh - 40px);
  overflow-y: auto;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translate(-50%, -45%);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%);
  }
}
</style>