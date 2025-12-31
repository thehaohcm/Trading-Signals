<template>
  <div>
    <h2>Oil & Commodity Prices</h2>
    <input type="text" v-model="filterText" placeholder="Filter by commodity..." style="text-align: center; margin: 0 0 10px 0;"/>
    
    <!-- TradingView Chart Popup -->
    <div v-if="selectedSymbol" class="chart-overlay" @click.self="closeChart">
      <div class="chart-container">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h4 class="mb-0">{{ selectedSymbol }} Chart</h4>
          <button class="btn btn-sm btn-danger" @click="closeChart">
            ✕ Close
          </button>
        </div>
        <TradingViewChart :coin="getTradingViewSymbol(selectedSymbol)" />
      </div>
    </div>
    
    <div v-if="isLoading" class="d-flex justify-content-center">
        <div class="spinner"></div>
    </div>
    <div style="overflow-x: auto;" v-else class="table table-striped">
        <table>
        <thead>
            <tr>
            <th>Commodity</th>
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
            <tr v-for="item in filteredCurrencyData" :key="item.currency" 
                @click="selectSymbol(item.currency)"
                class="cursor-pointer">
            <td><strong>{{ item.currency }}</strong></td>
            <td>{{ item.rate }}</td>
            <td>{{ item.bid }}</td>
            <td>{{ item.ask }}</td>
            <td>{{ item.high }}</td>
            <td>{{ item.low }}</td>
            <td>{{ item.open }}</td>
            <td>{{ item.close }}</td>
            <td>{{ formatTimestamp(item.timestamp) }}</td>
            </tr>
        </tbody>
        </table>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import TradingViewChart from './TradingViewChart.vue';

export default {
  components: {
    TradingViewChart
  },
  setup() {
    const currencyData = ref([]);
    const isLoading = ref(false);
    const filterText = ref('');
    const selectedSymbol = ref(null);

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
    
    const filteredCurrencyData = computed(() => {
      return currencyData.value.filter(item =>
        item.currency.toLowerCase().includes(filterText.value.toLowerCase())
      );
    });

    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'N/A';
      const date = new Date(parseInt(timestamp));
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
    };

    const selectSymbol = (symbol) => {
      selectedSymbol.value = symbol;
    };

    const closeChart = () => {
      selectedSymbol.value = null;
    };

    const getTradingViewSymbol = (symbol) => {
      // Map to forex pairs
      if (symbol.includes('/')) {
        return `FX:${symbol.replace(/\//g, '')}`;
      }
      
      // Map to NASDAQ symnols
      if (symbol.includes('#')) {
        return `NASDAQ:${symbol.replace('#', '')}`;
      }

      // Map commodity names to TradingView symbols
      const symbolMap = {
        'CrudeOIL': 'TVC:USOIL',
        'BRENT_OIL': 'TVC:UKOIL',
        'HEATING_OIL': 'NYMEX:HO1!',
        'USOil': 'TVC:USOIL',
        'UKOil': 'TVC:UKOIL'
      };
      return symbolMap[symbol] || `FX:${symbol}`;
    };

    return {
      currencyData,
      isLoading,
      filterText,
      filteredCurrencyData,
      formatTimestamp,
      selectedSymbol,
      selectSymbol,
      closeChart,
      getTradingViewSymbol
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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  z-index: 1050;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

.chart-container {
  background: white;
  padding: 20px;
  border-radius: 12px;
  width: 90%;
  max-width: 1200px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  -webkit-overflow-scrolling: touch;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .chart-container {
    width: 95%;
    max-height: 90vh;
    padding: 15px;
  }
}

@media (max-width: 480px) {
  .chart-container {
    width: 98%;
    max-height: 95vh;
    padding: 10px;
  }
  
  .chart-container h4 {
    font-size: 1rem;
  }
}
</style>