<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />
    <notifications />
    <div class="container mt-4 flex-grow-1">
      <div class="nav nav-tabs" id="homeTabs" role="tablist">
        <a class="nav-item nav-link" :class="{ 'active': activeTab === 'Potential coins' }" @click="activeTab = 'Potential coins'">Potential coins</a>
      </div>

      <div class="tab-content" id="homeTabContent">
        <div class="tab-pane fade show active" v-show="activeTab === 'Potential coins'">
          <!-- Coin input section -->
          <div class="mb-3 mt-3">
            <div class="input-group">
              <input 
                type="text" 
                class="form-control" 
                v-model="coinInputText"
                @keydown.enter="updateSelectedCoin"
                @input="coinInputText = $event.target.value.toUpperCase()"
                placeholder="Nhập mã coin để xem chart (VD: BTCUSDT, ETHUSDT...) và nhấn Enter"
              />
              <button 
                class="btn btn-primary" 
                @click="updateSelectedCoin"
                :disabled="!coinInputText || !coinInputText.trim()"
              >
                Xem Chart
              </button>
            </div>
            <small class="text-muted">Coin hiện tại: <strong>{{ selectedCoin }}</strong></small>
          </div>

          <TradingViewChart :coin="selectedCoin" />
          
          <!-- Price Alert Widget -->
          <PriceAlertWidget 
            :symbol="selectedCoin" 
            assetType="crypto" 
          />
          
          <h5 class="mb-0">Potential coins</h5>
            <div class="card-body">
              <!-- Message display -->
              <div v-if="message" class="alert" :class="potentialCoins.data && potentialCoins.data.length > 0 ? 'alert-info' : 'alert-warning'" role="alert">
                {{ message }}
              </div>
              
              <div class="mb-2" v-if="potentialCoins.data && potentialCoins.data.length > 0">
                <input type="text" v-model="filterText" placeholder="Filter coins..." class="form-control" />
              </div>
              <div v-if="potentialCoins.latest_updated" style="text-align: right; font-weight: bold;">
                <strong>Last Updated:</strong> {{ formatDate(potentialCoins.latest_updated) }}
              </div>
              <table class="table table-striped">
                <tbody>
                  <tr v-for="coin in filteredPotentialCoins" :key="coin.crypto"
                    @click="selectedCoin = coin.crypto"
                    style="cursor: pointer;"
                    :class="{ 'highlighted-row': selectedCoin === coin.crypto }">
                    <td style="text-align: left; width: 1%;">
                      <input type="checkbox" @click.stop="toggleStock(coin.crypto)">
                    </td>
                    <td :title="`Click to see more ${coin.crypto} info...`">
                      {{ coin.crypto }}
                    </td>
                  </tr>
                </tbody>
              </table>

              <div v-if="potentialCoins.data && potentialCoins.data.length > 0"
                class="d-flex justify-content-center gap-2 my-2">
                <button @click="exportCSV" class="btn btn-primary">Export CSV file</button>
              </div>
              <button v-if="!loadingPotentialCoins && !startScanning" @click="startScanningCoins"
                class="btn btn-success">Start to scan...</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <AppFooter />
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter  from './AppFooter.vue';
import 'vue3-select/dist/vue3-select.css';
import { ref, onMounted, computed } from 'vue'
import { useNotification } from "@kyvg/vue3-notification";
import 'vue3-select/dist/vue3-select.css';
import TradingViewChart from './TradingViewChart.vue'
import PriceAlertWidget from './PriceAlertWidget.vue'

const { notify } = useNotification();

export default {
  components: {
    NavBar,
    AppFooter,
    TradingViewChart,
    PriceAlertWidget,
  },
  setup() {
    const activeTab = ref('Potential coins'); // Add reactive activeTab variable
    const isMenuOpen = ref(false);
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };
    const selectedCoin = ref('BTCUSDT');
    const coinInputText = ref('');
    const selectedStock = ref(null);
    const stocks = ref([]);
    const symbols = ref(['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'LINKUSDT']); // Example symbols
    // Use individual refs for each signal
    const currentPrices = {};
    const potentialCoins = ref([]);
    const loadingPotentialCoins = ref(false);
    const startScanning = ref(false);
    const filterText = ref(''); // Add filterText
    const isLoading = ref(false);
    const message = ref(''); // Add message ref

    onMounted(async () => {
      notify({
        type: "info",
        title: "Welcome!",
        text: "The application has loaded successfully.",
      });
      
      // Fetch potential coins on mount
      await fetchPotentialCoins();
    });

    const fetchPotentialCoins = async () => {
      loadingPotentialCoins.value = true;
      isLoading.value = true;
      message.value = '';
      try {
        const response = await fetch('/getPotentialCoins');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        potentialCoins.value = data; // Assign directly
        
        // Show message if no data
        if (!data.data || data.data.length === 0) {
          message.value = 'No potential coins available at the moment.';
        } else {
          message.value = `Found ${data.data.length} potential coins.`;
        }
      } catch (error) {
        console.error('Error fetching potential coins:', error);
        potentialCoins.value = { data: [] }; // Clear the list on error
        message.value = 'Failed to load potential coins. Please try again later.';
      } finally {
        loadingPotentialCoins.value = false;
        isLoading.value = false;
      }
    };

    const startScanningCoins = () => {
      startScanning.value = true;
      fetchPotentialCoins();
    }

    const exportCSV = () => {
      if (potentialCoins.value.length === 0) {
        return;
      }

      const csvContent = "data:text/csv;charset=utf-8," + "potential coin pair\n" + potentialCoins.value.join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "potential_coins.csv");
      document.body.appendChild(link); // Required for Firefox

      link.click(); // This will download the data file named "potential_coin.csv".

      document.body.removeChild(link);
    };

    const formatDate = (dateString) => {
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      const seconds = String(date.getSeconds()).padStart(2, '0');

      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    }

    const filteredPotentialCoins = computed(() => {
      if (!filterText.value) {
        return potentialCoins.value.data || [];
      }
      return (potentialCoins.value.data || []).filter(coin =>
      coin.symbol.toLowerCase().includes(filterText.value.toLowerCase())
      );
    });

    const updateSelectedStock = (newStock) => {
      selectedStock.value = newStock ? newStock : null;
    }

    const updateStocks = (newStocks) => {
      stocks.value = newStocks;
    }

    const updateSelectedCoin = () => {
      const input = coinInputText.value.trim().toUpperCase();
      if (input) {
        selectedCoin.value = input;
        notify({
          type: "success",
          title: "Chart Updated",
          text: `Đã chuyển sang chart ${input}`,
        });
      }
    }

    return {
      selectedCoin,
      coinInputText,
      updateSelectedCoin,
      symbols,
      selectedStock,
      updateSelectedStock,
      stocks,
      updateStocks,
      currentPrices,
      potentialCoins,
      startScanningCoins,
      startScanning,
      exportCSV,
      filteredPotentialCoins,
      loadingPotentialCoins,
      formatDate,
      filterText,
      isMenuOpen,
      toggleMenu,
      activeTab,
      isLoading,
      message
    };
  }
}
</script>

<style>
/* Remove default styling */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 0;
  /* Remove top margin */
}

/* Tab styling */
.nav-tabs {
  flex-wrap: nowrap;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: #6cb2eb #edf2f7;
}

.nav-tabs::-webkit-scrollbar {
  height: 6px;
}

.nav-tabs::-webkit-scrollbar-track {
  background: #edf2f7;
  border-radius: 3px;
}

.nav-tabs::-webkit-scrollbar-thumb {
  background: #6cb2eb;
  border-radius: 3px;
}

.nav-tabs::-webkit-scrollbar-thumb:hover {
  background: #5a9fd4;
}

.nav-link {
  cursor: pointer;
  transition: background-color 0.3s ease;
  border-radius: 0.25rem;
  margin: 0 2px;
  white-space: nowrap;
}

.nav-item {
  flex: 0 0 auto;
  width: auto;
  min-width: 150px;
  text-align: center;
}

.nav-link:hover {
  background-color: #2d3748;
  color: white;
  border-bottom: 2px solid #6cb2eb;
  font-weight: bolder;
}

/* Responsive adjustments */
@media (max-width: 480px) {
  .nav-item {
    min-width: 120px;
  }
  
  .nav-link {
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
  }
}

.table-light {
  background-color: #edf2f7;
  text-align: left;
}

.price-div {
  font-weight: 1000;
  color: #2c3e50;
  float: right;
}

/* Stock Vietnam section */
.card {
  border: none;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Add some padding to the footer */
footer {
  padding: 20px 0;
}

.user-info {
  cursor: pointer;
}

.dropdown {
  position: relative;
  display: inline-block;
}
</style>