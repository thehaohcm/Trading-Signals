<template>
  <div class="currency-prices-container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
      <h2 class="mb-0 fw-bold d-flex align-items-center gap-2" style="color: #ffffff;">
        <span class="fs-4">💱</span> Oil & Commodity Prices
      </h2>
      
      <div class="search-wrapper">
        <i class="bi bi-search search-icon"></i>
        <input 
          type="text" 
          v-model="filterText" 
          class="form-control form-control-lg search-input" 
          placeholder="Filter by commodity or pair..." 
        />
      </div>
    </div>
    
    <!-- TradingView Chart Popup -->
    <div v-if="selectedSymbol" class="chart-overlay" @click.self="closeChart">
      <div class="chart-container">
        <div class="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2" style="border-color: rgba(255, 255, 255, 0.08) !important;">
          <h4 class="mb-0 fw-bold d-flex align-items-center gap-2" style="color: #ffffff;">
            <i class="bi bi-graph-up-arrow" style="color: #00f2fe;"></i> {{ selectedSymbol }} Chart
          </h4>
          <button class="btn btn-sm btn-outline-danger rounded-pill px-3 fw-bold" @click="closeChart">
            <i class="bi bi-x-lg"></i> Close
          </button>
        </div>
        <TradingViewChart :coin="getTradingViewSymbol(selectedSymbol)" />
      </div>
    </div>
    
    <div v-if="isLoading" class="d-flex justify-content-center py-5">
      <div class="spinner-border text-info" role="status" style="width: 3rem; height: 3rem;">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    
    <div v-else class="card shadow-sm border-0 rounded-4 overflow-hidden glass-panel">
      <div class="table-responsive">
        <table class="table table-borderless align-middle mb-0 custom-table">
          <thead>
            <tr>
              <th class="stk-th ps-4">Commodity</th>
              <th class="stk-th">Rate</th>
              <th class="stk-th">Bid</th>
              <th class="stk-th">Ask</th>
              <th class="stk-th">High</th>
              <th class="stk-th">Low</th>
              <th class="stk-th">Open</th>
              <th class="stk-th">Close</th>
              <th class="stk-th pe-4 text-end">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredCurrencyData" :key="item.currency" 
                @click="selectSymbol(item.currency)"
                class="cursor-pointer row-hover-effect">
              <td class="ps-4 py-3">
                <div class="d-flex align-items-center gap-2">
                  <span class="symbol-badge">{{ getSymbolPrefix(item.currency) }}</span>
                  <strong style="color: #ffffff;">{{ item.currency }}</strong>
                </div>
              </td>
              <td class="py-3 fw-bold fs-6" style="color: #00f2fe;">{{ item.rate }}</td>
              <td class="py-3" style="color: #94a3b8;">{{ item.bid }}</td>
              <td class="py-3" style="color: #94a3b8;">{{ item.ask }}</td>
              <td class="py-3 text-success fw-medium">{{ item.high }}</td>
              <td class="py-3 text-danger fw-medium">{{ item.low }}</td>
              <td class="py-3" style="color: #94a3b8;">{{ item.open }}</td>
              <td class="py-3" style="color: #94a3b8;">{{ item.close }}</td>
              <td class="py-3 pe-4 text-end small" style="color: #64748b;">{{ formatTimestamp(item.timestamp) }}</td>
            </tr>
            <tr v-if="filteredCurrencyData.length === 0">
              <td colspan="9" class="text-center py-5" style="color: #94a3b8;">
                <i class="bi bi-inbox fs-2 d-block mb-2 opacity-50"></i>
                No matching commodities found for "{{ filterText }}"
              </td>
            </tr>
          </tbody>
        </table>
      </div>
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

    const fetchCurrencyPrices = async () => {
      isLoading.value = true;
      try {
        const response = await axios.get('/api/currency-prices');
        currencyData.value = response.data;
      } catch (error) {
        console.error('Error fetching currency prices:', error);
      } finally {
        isLoading.value = false;
      }
    };

    onMounted(() => {
      fetchCurrencyPrices();
    });

    const filteredCurrencyData = computed(() => {
      if (!filterText.value) return currencyData.value;
      const lower = filterText.value.toLowerCase();
      return currencyData.value.filter(item => 
        item.currency.toLowerCase().includes(lower)
      );
    });

    const getSymbolPrefix = (sym) => {
      if (!sym) return '';
      return sym.substring(0, 3);
    };

    const formatTimestamp = (ts) => {
      if (!ts) return '';
      try {
        const date = new Date(ts);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      } catch (e) {
        return ts;
      }
    };

    const selectSymbol = (sym) => {
      selectedSymbol.value = sym;
    };

    const closeChart = () => {
      selectedSymbol.value = null;
    };

    const getTradingViewSymbol = (sym) => {
      if (!sym) return 'OANDA:XAUUSD';
      const map = {
        'XAUUSD': 'OANDA:XAUUSD',
        'XAGUSD': 'OANDA:XAGUSD',
        'WTI': 'TVC:USOIL',
        'BRENT': 'TVC:UKOIL',
        'USOIL': 'TVC:USOIL',
        'UKOIL': 'TVC:UKOIL',
        'COPPER': 'COMEX:HG1!',
        'NG': 'NYMEX:NG1!',
        'PLATINUM': 'NYMEX:PL1!'
      };
      return map[sym] || `TVC:${sym}`;
    };

    return {
      currencyData,
      isLoading,
      filterText,
      filteredCurrencyData,
      getSymbolPrefix,
      formatTimestamp,
      selectedSymbol,
      selectSymbol,
      closeChart,
      getTradingViewSymbol
    };
  }
};
</script>

<style scoped>
.currency-prices-container {
  max-width: 100%;
}

.search-wrapper {
  position: relative;
  width: 100%;
  max-width: 350px;
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 1.1rem;
}

.search-input {
  padding-left: 48px;
  border-radius: 50px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background-color: rgba(10, 13, 20, 0.8) !important;
  color: #ffffff !important;
  transition: all 0.3s ease;
  font-size: 0.95rem;
}

.search-input:focus {
  background-color: rgba(10, 13, 20, 0.95) !important;
  border-color: #00f2fe;
  box-shadow: 0 0 0 4px rgba(0, 242, 254, 0.15);
  outline: none;
}

.glass-panel {
  background: rgba(18, 24, 38, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(16px);
}

.custom-table {
  border-collapse: separate;
  border-spacing: 0;
  width: 100%;
}

.stk-th {
  padding: 12px 16px;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #64748b;
  background: rgba(10, 13, 20, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  white-space: nowrap;
}

.row-hover-effect {
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.row-hover-effect:last-child {
  border-bottom: none;
}

.row-hover-effect:hover {
  background-color: rgba(0, 242, 254, 0.06) !important;
  transform: translateY(-1px);
}

.symbol-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(0, 242, 254, 0.12);
  color: #00f2fe;
  border: 1px solid rgba(0, 242, 254, 0.3);
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.8rem;
  letter-spacing: -0.5px;
}

.cursor-pointer {
  cursor: pointer;
}

.chart-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  z-index: 1050;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

.chart-container {
  background: #111726;
  border: 1px solid rgba(255, 255, 255, 0.12);
  padding: 24px;
  border-radius: 20px;
  width: 90%;
  max-width: 1200px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
  color: #ffffff;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 768px) {
  .search-wrapper {
    max-width: 100%;
  }
  .chart-container {
    width: 95%;
    max-height: 90vh;
    padding: 16px;
  }
}
</style>