<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark d-flex">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">
          <img src="../assets/logo.png" alt="Vue logo" style="width: 40px; margin-left: 25px;">
        </a>
        <button class="navbar-toggler" type="button" @click="toggleMenu" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav" :class="{ show: isMenuOpen }">
          <ul class="navbar-nav">
            <li class="nav-item">
              <a class="nav-link" :class="{ active: activeTab === 'Crypto' }" @click="activeTab = 'Crypto'">
                <img :src="require('../assets/btc.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
                Crypto
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link" :class="{ active: activeTab === 'Stock VN' }" @click="activeTab = 'Stock VN'">
                <img :src="require('../assets/stock.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
                Stock VN
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link" :class="{ active: activeTab === 'Gold' }" @click="activeTab = 'Gold'">
                <img :src="require('../assets/gold.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
                Gold
              </a>
            </li>
          </ul>
        </div>
          <!-- Login Button / User Greeting -->
          <div class="ms-auto">
              <template v-if="isLoggedIn && userInfo">
                  <span class="text-white">{{ userInfo.name }} ({{ userInfo.custodyCode }})</span>
              </template>
              <template v-else>
                  <router-link to="/login" class="btn btn-outline-light">Login</router-link>
              </template>
          </div>
      </div>
    </nav>
      <div class="text-center mt-3">
          <h2>Disclaimer</h2>
          <p>The information and indicators on this website reflect the owner's views and should not be taken as investment advice.</p>
      </div>

  <div class="container mt-4 flex-grow-1">
    <notifications />
    <div v-if="activeTab === 'Crypto'">
      <table class="table table-hover">
        <tbody>
          <template v-for="(signalData, symbol) in signals" :key="symbol">
            <tr>
              <td colspan="2" class="table-light">
                <strong>
                  <img :src="require(`../assets/${symbol.split('USDT')[0].toLowerCase()}.svg`)" style="width: 20px; height: 20px; margin-right: 5px;" />
                  <a :href="'https://www.binance.com/en/trade/' + symbol.split('USDT')[0] + '_USDT?type=spot'" target="_blank" class="text-decoration-none text-primary">{{ symbol }}</a>
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

      <p style="font-weight: bold;" :style="{ color: isConnected ? 'green' : 'red' }">WebSocket is {{ isConnected ? 'connected' : 'disconnected' }}</p>
    </div>

    <div v-if="activeTab === 'Gold'">
      <table class="table table-hover">
        <tbody>
          <template v-for="(signalData, symbol) in goldSignals" :key="symbol">
            <tr>
              <td colspan="2" class="table-light">
                <img :src="require(`../assets/gold.svg`)" style="width: 25px; height: 25px; margin-right: 5px;" />
                <strong>Gold</strong>
                <div class="price-div">{{ currentPrices[symbol]['5m'] }} USD</div>
              </td>
            </tr>
            <template v-for="(intervalData, interval) in signalData" :key="`${symbol}-${interval}`">
              <tr>
                <td><strong>{{ interval }}</strong></td>
                <td><span style="display: block; font-size: 15px;" class="badge" :class="{
                  'bg-secondary': goldSignals['PAXGUSDT'][interval].value === 'Waiting...',
                  'bg-warning': goldSignals['PAXGUSDT'][interval].value === 'HOLD',
                  'bg-danger': goldSignals['PAXGUSDT'][interval].value === 'SELL',
                  'bg-success': goldSignals['PAXGUSDT'][interval].value === 'BUY'
                }">{{ goldSignals['PAXGUSDT'][interval].value }}</span></td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>

      <p style="font-weight: bold;" :style="{ color: isConnected ? 'green' : 'red' }">WebSocket is {{ isConnected ? 'connected' : 'disconnected' }}</p>
    </div>

    <div v-if="activeTab === 'Stock VN'">
        <div class="row justify-content-center">
          <!-- <div class="col-md-8"> -->
            <div class="card">
              <div class="card-header bg-secondary text-white">
                <h5 class="mb-0">Vietnam Stock Evaluator</h5>
              </div>
              <div class="card-body">
                <p class="card-text" style="margin-top:0px; font-weight: bold;">Choose a stock symbol:</p>
                <v-select v-model="selectedStock" :options="stocks"  @input="onStockSelected" placeholder="Input (or choose) a stock symbol"></v-select>
                <StockVn style="width: 100%;" v-if="activeTab === 'Stock VN'" @update:selectedStock="updateSelectedStock" @update:stocks="updateStocks"/>
              </div>
            </div>
          <!-- </div> -->
        </div>
      </div>
  </div>
  <footer class="mt-5 text-center text-white bg-dark py-3">Copyright © by Nguyen The Hao 2025. All rights reserved.</footer>
</div>
</template>

<script>
import StockVn from './StockVn.vue';
import 'vue3-select/dist/vue3-select.css';
import { ref, onMounted, watch, computed } from 'vue'
import { useNotification } from "@kyvg/vue3-notification";
import 'vue3-select/dist/vue3-select.css';

const { notify } = useNotification();

export default {
  components: {
    StockVn,
  },
  setup() {
    const isMenuOpen = ref(false);
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };
    const isConnected = ref(false);
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

    // Initialize signals and currentPrices objects
    symbols.value.forEach(symbol => {
      signals[symbol] = {};
      currentPrices[symbol] = {};
      intervals.forEach(interval => {
        signals[symbol][interval] = ref('Waiting...');
        currentPrices[symbol][interval] = ref(null); // Initialize with null
      });
    });

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
      const response = await fetch('/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000');
      const data = await response.json();
      stocks.value = data.data;
    };

    const fetchUserInfo = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          console.log("token",token)
          const response = await fetch('/dnse-user-service/api/me', {
            headers: {
              'Content-Type': 'application/json',
              'authorization': `Bearer ${token}`
            }
          });
          const data = await response.json();
          if (response.ok) {
            userInfo.value = data;
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

    const isLoggedIn = computed(() => {
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
      userInfo
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
  margin-top: 0; /* Remove top margin */
}

/* Tab styling */
.nav-link {
  cursor: pointer;
  transition: background-color 0.3s ease;
  border-radius: 0.25rem;
  margin: 0 2px;
}

.nav-item {
  width: 150px; /* Adjust as needed */
  text-align: center;
}

.nav-link:hover {
  background-color: #2d3748; /* Dark background for active tab */
  color: white;
  border-bottom: 2px solid #6cb2eb; /* Highlight active tab */
  font-weight: bolder;
}

.table-light {
  background-color: #edf2f7;
  text-align: left;
}

.price-div{
  font-weight:1000;
  color:#2c3e50;
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
</style>