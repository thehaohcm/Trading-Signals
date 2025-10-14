<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />
    <notifications />
    <div class="container mt-4 flex-grow-1">
      <div class="nav nav-tabs" id="homeTabs" role="tablist">
        <a class="nav-item nav-link" :class="{ 'active': activeTab === 'Signals' }" @click="activeTab = 'Signals'">Signals</a>
        <a class="nav-item nav-link" :class="{ 'active': activeTab === 'RRG chart' }" @click="activeTab = 'RRG chart'">RRG chart</a>
        <a class="nav-item nav-link" :class="{ 'active': activeTab === 'Potential coins' }" @click="activeTab = 'Potential coins'">Potential coins</a>
      </div>

      <div class="tab-content" id="homeTabContent">
        <div class="tab-pane fade show active" v-show="activeTab === 'Signals'">
        <table class="table table-hover">
          <tbody>
            <template v-for="(signalData, symbol) in signals" :key="symbol">
              <tr>
                <td colspan="2" class="table-light">
                  <strong>
                    <img :src="require(`../assets/${symbol.split('USDT')[0].toLowerCase()}.svg`)"
                      style="width: 20px; height: 20px; margin-right: 5px;" />
                    <a :href="'https://www.binance.com/en/trade/' + symbol.split('USDT')[0] + '_USDT?type=spot'"
                      target="_blank" class="text-decoration-none text-primary">{{ symbol }}</a>
                  </strong>
                  <div class="price-div">{{ currentPrices[symbol]['5m'] }} USD</div>
                </td>
              </tr>
              <template v-for="(intervalData, interval) in signalData" :key="`${symbol}-${interval}`">
                <tr>
                  <td><strong>{{ interval }}</strong></td>
                  <td><span style="display: block; font-size:15px" class="badge" :class="{
                    'bg-secondary': signals[symbol][interval].value === 'Waiting...',
                    'bg-warning': signals[symbol][interval].value === 'HOLD',
                    'bg-danger': signals[symbol][interval].value === 'SELL',
                    'bg-success': signals[symbol][interval].value === 'BUY'
                  }">{{ signals[symbol][interval].value }}</span></td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>

        <p style="font-weight: bold;" :style="{ color: isConnected ? 'green' : 'red' }">WebSocket is {{ isConnected ?
          'connected' : 'disconnected' }}</p>
        </div>

        <div class="tab-pane fade show active" v-show="activeTab === 'RRG chart'">
          <div class="d-flex flex-wrap mb-3">
            <button
              v-for="interval in rrgIntervals"
              :key="interval"
              class="btn btn-outline-primary m-1"
              :class="{ 'btn-primary': interval === activeRRGInterval }"
              @click="activeRRGInterval = interval">
              {{ interval }}
            </button>
          </div>
          <Suspense>
            <template #default>
              <RRGChart />
            </template>
            <template #fallback>
              <div>Loading chart...</div>
            </template>
          </Suspense>
        </div>
        <div class="tab-pane fade show active" v-show="activeTab === 'Potential coins'">
          <TradingViewChart :coin="selectedCoin" />
          <br />
          <h5 class="mb-0">Potential coins</h5>
            <div class="card-body">
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
import { ref, onMounted, watch, computed } from 'vue'
import { useNotification } from "@kyvg/vue3-notification";
import 'vue3-select/dist/vue3-select.css';
import TradingViewChart from './TradingViewChart.vue'

const { notify } = useNotification();

export default {
  components: {
    NavBar,
    AppFooter,
    TradingViewChart,
    RRGChart: () => import('./RRGChart.vue')
  },
  setup() {
    const activeTab = ref('Signals'); // Add reactive activeTab variable
    const isMenuOpen = ref(false);
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };
    var isConnected = ref(false);
    const selectedCoin = ref('BTCUSDT');
    const activeRRGInterval = ref('5m');
    const selectedStock = ref(null);
    const stocks = ref([]);
    const symbols = ref(['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'LINKUSDT']); // Example symbols
    const intervals = ['5m', '15m', '1h', '4h', '1d'];
    const rrgIntervals = ['5m', '30m', '1h', '4h', '1d', '1w'];
    // Use individual refs for each signal
    const signals = {};
    const activeConnections = new Map(); // Keep track of active connections
    const currentPrices = {};
    const potentialCoins = ref([]);
    const loadingPotentialCoins = ref(false);
    const startScanning = ref(false);
    const filterText = ref(''); // Add filterText
    const isLoading = ref(false);

    // Initialize signals and currentPrices objects
    symbols.value.forEach(symbol => {
      signals[symbol] = {};
      currentPrices[symbol] = {};
      intervals.forEach(interval => {
        signals[symbol][interval] = ref('Waiting...');
        currentPrices[symbol][interval] = ref(null); // Initialize with null
      });
    });

    onMounted(async () => {
      notify({
        type: "info",
        title: "Welcome!",
        text: "The application has loaded successfully.",
      });
    });

    const connectWebSocket = (symbol, interval) => {
      const connectionKey = `${symbol}-${interval}`;
      if (activeConnections.has(connectionKey)) {
        console.log(`WebSocket connection already exists for ${symbol} - ${interval}`);
        return; // Prevent duplicate connections
      }

      const url = `wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}@kline_${interval}`;
      console.log(`Connecting to: ${url}`);
      const socket = new WebSocket(url);
      activeConnections.set(connectionKey, socket);

      socket.onopen = () => {
        console.log(`WebSocket connected for ${symbol} - ${interval}`);
        isConnected.value = true;
      };

      // Use a closure to capture the 'interval' for the onmessage handler
      socket.onmessage = (event) => {
        try {
          const jsonMessage = JSON.parse(event.data);
          const candle = jsonMessage['k'];
          const isCandleClosed = candle['x'];

          // Update current price
          currentPrices[symbol][interval].value = parseFloat(candle['c']);


          if (isCandleClosed) {
            const klineData = {
              open: parseFloat(candle['o']),
              high: parseFloat(candle['h']),
              low: parseFloat(candle['l']),
              close: parseFloat(candle['c']),
              volume: parseFloat(candle['v'])
            };

            // Implement Wyckoff, SMC, VSA strategies here
            const wyckoffSignal = analyzeWyckoff(klineData);
            const smcSignal = analyzeSMC(klineData);
            const vsaSignal = analyzeVSA(klineData);

            // Combine signals (example: simple average)
            let combinedSignal = 'HOLD';
            const signalValues = { 'BUY': 1, 'HOLD': 0, 'SELL': -1 };
            const combinedValue = (signalValues[wyckoffSignal] + signalValues[smcSignal] + signalValues[vsaSignal]) / 3;

            if (combinedValue > 0.3) {
              combinedSignal = 'BUY';
            } else if (combinedValue < -0.3) {
              combinedSignal = 'SELL';
            }

            signals[symbol][interval].value = combinedSignal; 
          }
        } catch (error) {
          notify({
            type: "error",
            title: "Error",
            text: `Error fetching ${symbol} in the interval ${interval}: ${error.message}`
          });
          console.error(error);
        }
      };

      socket.onclose = () => {
        console.log(`WebSocket disconnected for ${symbol} - ${interval}`);
        isConnected.value = false;
        activeConnections.delete(connectionKey); // Remove from active connections
        // Optionally handle reconnection logic here
      };
    };

    const analyzeWyckoff = (klineData) => {
      // Simplified Wyckoff Analysis - Placeholder
      // Basic Phase Identification (very simplified)
      let phase = 'Unknown';
      if (klineData.close > klineData.open && klineData.volume > 1000) { // Example condition
        phase = 'Markup';
      } else if (klineData.close < klineData.open && klineData.volume > 1000) {
        phase = 'Markdown';
      }

      // Basic Spring/Upthrust detection (very simplified)
      let event = 'None';
      if (klineData.low < klineData.open * 0.95) { // Example: 5% drop below open
        event = 'Potential Spring';
      }

      let signal = 'HOLD';
      if (phase === 'Markup' && event === 'None') {
        signal = 'BUY';
      } else if (phase === 'Markdown') {
        signal = 'SELL';
      }
      return signal;
    };

    const analyzeSMC = (klineData) => {
      // Simplified SMC Analysis - Placeholder
      // Basic Order Block Detection (very simplified)
      let orderBlock = false;
      if (Math.abs(klineData.close - klineData.open) < 0.01 * klineData.open) { // Example: small candle body
        orderBlock = true;
      }

      let signal = 'HOLD';
      if (orderBlock && klineData.close > klineData.open) {
        signal = 'BUY'; // Simplified
      }
      return signal;
    };

    const analyzeVSA = (klineData) => {
      // Simplified VSA - Placeholder
      // Basic Volume/Spread Analysis
      let highVolumeHighSpread = klineData.volume > 2000 && (klineData.high - klineData.low) > 0.02 * klineData.open;
      let lowVolumeNarrowSpread = klineData.volume < 500 && (klineData.high - klineData.low) < 0.005 * klineData.open;

      let signal = 'HOLD';
      if (highVolumeHighSpread && klineData.close > klineData.open) {
        signal = 'BUY'; // Simplified
      } else if (lowVolumeNarrowSpread) {
        signal = 'HOLD';
      }
      return signal;
    };

    const fetchPotentialCoins = async () => {
      loadingPotentialCoins.value = true;
      isLoading.value = true;
      try {
        const response = await fetch('/getPotentialCoins');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        potentialCoins.value = data; // Assign directly
      } catch (error) {
        console.error('Error fetching potential coins:', error);
        potentialCoins.value = {}; // Clear the list on error
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

    onMounted(() => {
      // Use existing symbols for initialization
      symbols.value.forEach(symbol => {
        intervals.forEach(interval => {
          connectWebSocket(symbol, interval);
        })
      });
    });

    watch(selectedCoin, (newCoin) => {
      console.log('📊 Coin changed to:', newCoin)
      // Close existing connections for the old coin
      for (const [key, socket] of activeConnections) {
        if (key.startsWith(selectedCoin.value)) {
          socket.close();
        }
      }
      // Connect for the new coin
      intervals.forEach(interval => {
        connectWebSocket(newCoin, interval);
      });

    });

    watch(signals, (newSignals) => {
      console.log('Signals changed:', JSON.parse(JSON.stringify(newSignals)));
    }, { deep: true });

    const updateSelectedStock = (newStock) => {
      selectedStock.value = newStock ? newStock : null;
    }

    const updateStocks = (newStocks) => {
      stocks.value = newStocks;
    }

    return {
      isConnected,
      selectedCoin,
      symbols,
      signals,
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
      isMenuOpen,
      toggleMenu,
      activeTab,
      rrgIntervals,
      activeRRGInterval
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
.nav-link {
  cursor: pointer;
  transition: background-color 0.3s ease;
  border-radius: 0.25rem;
  margin: 0 2px;
}

.nav-item {
  width: 150px;
  /* Adjust as needed */
  text-align: center;
}

.nav-link:hover {
  background-color: #2d3748;
  /* Dark background for active tab */
  color: white;
  border-bottom: 2px solid #6cb2eb;
  /* Highlight active tab */
  font-weight: bolder;
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

/* Stock VN section */
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