<template>
  <div class="page-wrapper">
    <NavBar />
    <div class="container mt-4 flex-grow-1 pb-5">
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2 pt-2">
        <h2 class="mb-0 fw-bold d-flex align-items-center gap-2 text-white">
          <span>💱</span> Forex Calendar & Signals
        </h2>
        <span class="badge bg-primary px-3 py-2 shadow-sm" style="background-color: #3b82f6 !important; font-size: 0.88rem; font-weight: 600;">
          Macro Terminal
        </span>
      </div>
    
    <!-- Bootstrap Tabs -->
    <ul class="nav nav-tabs" role="tablist">
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'calendar' }" @click="activeTab = 'calendar'" type="button">
          Economic Calendar
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'prices' }" @click="activeTab = 'prices'" type="button">
          Commodity Prices
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'potential' }" @click="activeTab = 'potential'" type="button">
          Potential Forex Pairs
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" :class="{ active: activeTab === 'rrg' }" @click="activeTab = 'rrg'" type="button">
          RRG chart
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
                  <td>
                    <span class="impact-badge" :class="'impact--' + String(item.impact).toLowerCase()">
                      {{ item.impact }}
                    </span>
                  </td>
                  <td>{{ item.forecast || '-' }}</td>
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

        <div class="text-center my-4 d-flex justify-content-center gap-3">
          <button class="btn btn-primary btn-lg" @click="scanForexPairs" :disabled="isScanning">
            <span v-if="isScanning" class="spinner-border spinner-border-sm me-2"></span>
            {{ isScanning ? 'Scanning...' : 'Start to scan...' }}
          </button>
          <button class="btn btn-outline-primary btn-lg" @click="runSSHScript('forex_potential')" :disabled="isRunningPotentialScript">
            <span v-if="isRunningPotentialScript" class="spinner-border spinner-border-sm me-2"></span>
            Run script
          </button>
        </div>
      </div>

      <!-- RRG Chart Tab -->
      <div v-if="activeTab === 'rrg'">
        <div class="text-center mt-4">
          <div class="mb-3">
            <button class="btn btn-primary btn-lg" @click="runSSHScript('forex_rrg')" :disabled="isRunningRrgScript">
              <span v-if="isRunningRrgScript" class="spinner-border spinner-border-sm me-2"></span>
              Generate RRG Chart
            </button>
          </div>
          <img :src="forexRRGUrl" alt="Forex RRG Chart" class="img-fluid rounded shadow-lg" style="max-width: 100%; border: 1px solid #ddd;" />
          <p class="mt-2 text-muted">
            Relative Rotation Graph (RRG) for major Forex pairs against USD.
            <br>
            Updated daily.
          </p>
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

    // SSH script execution states
    const isRunningPotentialScript = ref(false);
    const isRunningRrgScript = ref(false);
    const forexRRGKey = ref(Date.now());
    const forexRRGUrl = computed(() => `/forex_rrgchart?t=${forexRRGKey.value}`);

    const runSSHScript = async (scriptType) => {
      const isRrg = scriptType === 'forex_rrg';
      if (isRrg) {
        isRunningRrgScript.value = true;
      } else {
        isRunningPotentialScript.value = true;
      }

      try {
        const response = await fetch('/runSSHScript', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ script_type: scriptType }),
        });
        const data = await response.json();
        if (response.ok && data.success) {
          alert(isRrg ? 'Forex RRG Chart has been updated successfully!' : 'Forex scanner script executed successfully!');
          if (isRrg) {
            forexRRGKey.value = Date.now();
          } else {
            scanForexPairs();
          }
        } else {
          throw new Error(data.error || 'Server returned an error');
        }
      } catch (error) {
        console.error('Error running SSH script:', error);
        alert(error.message || 'Failed to connect or run the SSH script.');
      } finally {
        if (isRrg) {
          isRunningRrgScript.value = false;
        } else {
          isRunningPotentialScript.value = false;
        }
      }
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
      closeChart,
      isRunningPotentialScript,
      isRunningRrgScript,
      forexRRGUrl,
      runSSHScript
    };
  },
};
</script>
<style scoped>
.page-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #ffffff;
  color: #1e293b;
}

.flex-grow-1 {
  flex: 1;
}

.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
}

/* economic calendar styles */
.highlight {
  border: 2px solid #3b82f6 !important;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.3) !important;
}

/* Tabs */
.nav-tabs {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  flex-wrap: nowrap;
  overflow-x: auto;
  overflow-y: hidden;
  display: flex;
  justify-content: flex-start;
  gap: 0.5rem;
  margin-bottom: 20px;
  -webkit-overflow-scrolling: touch;
}
.nav-tabs::-webkit-scrollbar {
  height: 4px;
}
.nav-tabs::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
}
.nav-tabs::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
.nav-tabs .nav-item {
  flex: 0 0 auto;
}
.nav-tabs .nav-link {
  color: #94a3b8;
  background-color: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px 8px 0 0;
  padding: 10px 20px;
  font-weight: 600;
  transition: all 0.25s ease;
  white-space: nowrap;
  font-size: 0.9rem;
  min-width: 160px;
}
.nav-tabs .nav-link:hover {
  background-color: rgba(255, 255, 255, 0.06);
  color: #f1f5f9;
}
.nav-tabs .nav-link.active {
  color: #3b82f6 !important;
  background-color: rgba(17, 22, 34, 0.85) !important;
  border-color: rgba(255, 255, 255, 0.08) rgba(255, 255, 255, 0.08) transparent !important;
  border-bottom: 2px solid transparent !important;
}

/* Date filter */
.form-label {
  font-weight: 600;
  color: #94a3b8;
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.form-control {
  background-color: rgba(13, 16, 27, 0.8) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #f1f5f9 !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
}
.form-control:focus {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25) !important;
}
.input-group .btn-outline-secondary {
  color: #cbd5e1 !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  background: rgba(255, 255, 255, 0.03) !important;
}
.input-group .btn-outline-secondary:hover {
  background: rgba(255, 255, 255, 0.08) !important;
  color: #fff !important;
}

/* Table overrides inside Forex */
.forex-table tbody tr {
  transition: all 0.2s;
}
.forex-table tbody tr:hover {
  background-color: rgba(255, 255, 255, 0.02) !important;
}
.cursor-pointer {
  cursor: pointer;
}

/* Economic Impact Badges */
.impact-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.impact--low {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
}
.impact--medium {
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.25);
}
.impact--high {
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.25);
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.15);
}

/* Alert panel */
.alert-info {
  background-color: rgba(59, 130, 246, 0.08) !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
  color: #93c5fd !important;
  border-radius: 12px !important;
}

/* Chart Overlay and Container */
.chart-overlay {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  max-width: 1200px;
  max-height: 85vh;
  background: rgba(13, 16, 27, 0.8) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  z-index: 1050;
  padding: 20px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
  animation: fadeIn 0.3s ease;
}

.chart-container {
  background: #111422 !important;
  color: #f1f5f9 !important;
  padding: 20px;
  border-radius: 12px;
  max-height: calc(85vh - 40px);
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.chart-container h4 {
  color: #fff !important;
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
}

.chart-container::-webkit-scrollbar {
  width: 6px;
}
.chart-container::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.02);
}
.chart-container::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
  border-radius: 3px;
}

.spinner {
  border: 4px solid rgba(255, 255, 255, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #3b82f6;
  animation: spin 1s ease infinite;
  margin: 20px auto;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
  font-weight: 600;
}
.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35) !important;
}

.btn-outline-primary {
  border-color: #3b82f6 !important;
  color: #3b82f6 !important;
  background: transparent !important;
  font-weight: 600;
}
.btn-outline-primary:hover {
  background: rgba(59, 130, 246, 0.1) !important;
  color: #fff !important;
}

/* Badges Buy / Sell */
.forex-table .badge {
  padding: 4px 10px;
  font-weight: 700;
  border-radius: 20px;
  font-size: 0.72rem;
  letter-spacing: 0.3px;
}
.forex-table .bg-success {
  background: rgba(16, 185, 129, 0.12) !important;
  color: #34d399 !important;
  border: 1px solid rgba(16, 185, 129, 0.25);
}
.forex-table .bg-danger {
  background: rgba(239, 68, 68, 0.12) !important;
  color: #f87171 !important;
  border: 1px solid rgba(239, 68, 68, 0.25);
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