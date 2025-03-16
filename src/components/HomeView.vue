<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />

    <div class="container mt-4 flex-grow-1">
      <notifications />
      <router-view v-slot="{ Component }">
        <component :is="Component" :goldSignals="goldSignals" :currentPrices="currentPrices"
          :isConnected="isConnected" />
      </router-view>

      <div v-if="activeTab === 'Crypto'">
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
    </div>
    <AppFood />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter  from './AppFooter.vue';
import StockVn from './StockVn.vue';
import 'vue3-select/dist/vue3-select.css';
import { ref, onMounted, watch, computed } from 'vue'
import { useNotification } from "@kyvg/vue3-notification";
import 'vue3-select/dist/vue3-select.css';
import { useRouter } from 'vue-router';

const { notify } = useNotification();

export default {
  components: {
    StockVn,
    NavBar,
    AppFooter
  },
  setup() {
    const isMenuOpen = ref(false);
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };
    var isConnected = ref(false);
    const selectedSymbol = ref('BTCUSDT');
    const selectedStock = ref(null);
    const stocks = ref([]);
    const symbols = ref(['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'LINKUSDT']); // Example symbols
    const intervals = ['5m', '15m', '1h', '4h', '1d'];
    // Use individual refs for each signal
    const signals = {};
    const goldSymbols = ref(['PAXGUSDT']);
    const goldSignals = {};
    const activeConnections = new Map(); // Keep track of active connections
    const currentPrices = {};
    const potentialStocks = ref([]);
    const loadingPotentialStocks = ref(false);
    const showChatbox = ref(false);
    const chatboxMessage = ref('');
    const userInfo = ref(null);
    const router = useRouter();
    const showDropdown = ref(false);

    // Initialize signals and currentPrices objects
    symbols.value.forEach(symbol => {
      signals[symbol] = {};
      currentPrices[symbol] = {};
      intervals.forEach(interval => {
        signals[symbol][interval] = ref('Waiting...');
        currentPrices[symbol][interval] = ref(null); // Initialize with null
      });
    });

    const logout = () => {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userInfo');
      userInfo.value = null;
      isLoggedIn = false;
      router.push('/');
    }

    goldSymbols.value.forEach(symbol => {
      goldSignals[symbol] = {};
      currentPrices[symbol] = {};
      intervals.forEach(interval => {
        goldSignals[symbol][interval] = ref('Waiting...');
        currentPrices[symbol][interval] = ref(null);
      });
    });

    const activeTab = ref('Crypto'); // Initialize activeTab

    const fetchStocks = async () => {
      const response = await fetch('https://api-finfo.vndirect.com.vn/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000');
      const data = await response.json();
      stocks.value = data.data;
    };

    const fetchUserInfo = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await fetch('https://services.entrade.com.vn/dnse-user-service/api/me', {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          });
          const data = await response.json();
          if (response.ok) {
            userInfo.value = data;
            localStorage.setItem('userInfo', JSON.stringify(data));
          } else {
            console.error('Failed to fetch user info:', data);
            // Optionally clear the token if it's invalid
            localStorage.removeItem('token');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('userInfo');
          }
        } catch (error) {
          console.error('Error fetching user info:', error);
        }
      }
    };

    onMounted(async () => {
      notify({
        type: "info",
        title: "Welcome!",
        text: "The application has loaded successfully.",
      });
      await fetchStocks();
      await fetchUserInfo(); // Fetch user info on mount
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
          if (goldSymbols.value.includes(symbol)) {
            currentPrices[symbol][interval].value = parseFloat(candle['c']);
          } else {
            currentPrices[symbol][interval].value = parseFloat(candle['c']);
          }


          if (isCandleClosed) {
            //console.log(`Candle closed for ${symbol} - ${interval}`);
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

            //console.log(`Updating signal for ${symbol} - ${interval}: ${combinedSignal}`);
            if (goldSymbols.value.includes(symbol)) {
              goldSignals[symbol][interval].value = combinedSignal;
            } else {
              signals[symbol][interval].value = combinedSignal; // Update signal using .value
            }
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


    onMounted(() => {
      // Use existing symbols for initialization
      symbols.value.forEach(symbol => {
        intervals.forEach(interval => {
          connectWebSocket(symbol, interval);
        })
      });

      goldSymbols.value.forEach(symbol => {
        intervals.forEach(interval => {
          connectWebSocket(symbol, interval);
        })
      });
    });

    watch(selectedSymbol, (newSymbol) => {
      // Close existing connections for the old symbol
      for (const [key, socket] of activeConnections) {
        if (key.startsWith(selectedSymbol.value)) {
          socket.close();
        }
      }
      // Connect for the new symbol
      intervals.forEach(interval => {
        connectWebSocket(newSymbol, interval);
      });

    });

    watch(signals, (newSignals) => {
      console.log('Signals changed:', JSON.parse(JSON.stringify(newSignals)));
    }, { deep: true });

    watch(goldSignals, (newSignals) => {
      console.log('Gold Signals changed:', JSON.parse(JSON.stringify(newSignals)));
    }, { deep: true });

    const updateSelectedStock = (newStock) => {
      selectedStock.value = newStock ? newStock : null;
    }

    const updateStocks = (newStocks) => {
      stocks.value = newStocks;
    }

    const tabs = ref(['Crypto', 'Stock VN', 'Gold']);

    var isLoggedIn = computed(() => {
      return !!localStorage.getItem('token');
    });
    return {
      isConnected,
      selectedSymbol,
      symbols,
      signals,
      goldSymbols,
      goldSignals,
      tabs,
      activeTab, // Return activeTab,
      selectedStock,
      updateSelectedStock,
      stocks,
      updateStocks,
      currentPrices,
      potentialStocks,
      loadingPotentialStocks,
      showChatbox,
      chatboxMessage,
      isMenuOpen,
      toggleMenu,
      isLoggedIn,
      userInfo,
      logout,
      showDropdown
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

.dropdown-content {
  display: none;
  position: absolute;
  background-color: #f9f9f9;
  min-width: 160px;
  box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.2);
  z-index: 1;
  right: 0;
  /* Align to the right */
}

.dropdown-content a {
  color: black;
  padding: 12px 16px;
  text-decoration: none;
  display: block;
  text-align: left;
}

.dropdown-content a:hover {
  background-color: #ddd;
}

.dropdown:hover .dropdown-content {
  display: block;
}
</style>