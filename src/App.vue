<template>
  <div id="app">
    <notifications />
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">
          <img src="./assets/logo.png" alt="Vue logo" style="width: 50px;">
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav">
            <li class="nav-item">
              <a class="nav-link" :class="{ active: activeTab === 'Crypto' }" @click="activeTab = 'Crypto'">Crypto</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" :class="{ active: activeTab === 'Stock VN' }" @click="activeTab = 'Stock VN'">Stock VN</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" :class="{ active: activeTab === 'Gold' }" @click="activeTab = 'Gold'">Gold</a>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <div class="container mt-4">
  <div v-if="activeTab === 'Crypto'">
    <table class="table table-hover">
      <tbody>
        <template v-for="(signalData, symbol) in signals" :key="symbol">
          <tr>
            <td colspan="2" class="table-light">
              <strong>
                <img :src="require(`./assets/${symbol.split('USDT')[0].toLowerCase()}.svg`)" style="width: 20px; height: 20px; margin-right: 5px;" />
                <a :href="'https://www.binance.com/en/trade/' + symbol.split('USDT')[0] + '_USDT?type=spot'" target="_blank" class="text-decoration-none text-primary">{{ symbol }}</a>
              </strong>
            </td>
          </tr>
          <template v-for="(intervalData, interval) in signalData" :key="`${symbol}-${interval}`">
            <tr>
              <td>{{ interval }}</td>
              <td><span class="badge bg-secondary">{{ signals[symbol][interval].value }}</span></td>
            </tr>
          </template>
        </template>
      </tbody>
    </table>

    <p :style="{ color: isConnected ? 'green' : 'red' }">WebSocket is {{ isConnected ? 'connected' : 'disconnected' }}</p>
  </div>

  <div v-if="activeTab === 'Gold'">
    <table class="table table-hover">
      <tbody>
        <template v-for="(signalData, symbol) in goldSignals" :key="symbol">
          <tr>
            <td colspan="2" class="table-light">
              <img :src="require(`./assets/gold.svg`)" style="width: 25px; height: 25px; margin-right: 5px;" />
              <strong>Gold</strong>
            </td>
          </tr>
          <template v-for="(intervalData, interval) in signalData" :key="`${symbol}-${interval}`">
            <tr>
              <td>{{ interval }}</td>
              <td><span class="badge bg-secondary">{{ goldSignals['PAXGUSDT'][interval].value }}</span></td>
            </tr>
          </template>
        </template>
      </tbody>
    </table>

    <p :style="{ color: isConnected ? 'green' : 'red' }">WebSocket is {{ isConnected ? 'connected' : 'disconnected' }}</p>
  </div>

      <div v-if="activeTab === 'Stock VN'">
          <div class="row justify-content-center">
            <div class="col-md-8">
              <div class="card">
                <div class="card-header bg-secondary text-white">
                  <h5 class="mb-0">Vietnam Stock Evaluator</h5>
                </div>
                <div class="card-body">
                  <p class="card-text" style="margin-top:0px;">Choose a stock symbol:</p>
                  <v-select v-model="selectedStock" :options="stocks" label="code" @input="onStockSelected" placeholder="Search stock code..."></v-select>
                    <StockVn style="width: 100%; margin-top: 10px;" v-if="activeTab === 'Stock VN'" @update:selectedStock="updateSelectedStock"  @update:stocks="updateStocks"/>
                </div>
              </div>
            </div>
          </div>
        </div>
    </div>

    <footer class="mt-5 text-center text-muted">Copyright &amp;copy; by Nguyen The Hao 2025. All rights reserved.</footer>
  </div>
</template>

<script>
import StockVn from './components/StockVn.vue';
import 'vue3-select/dist/vue3-select.css';
import { ref, onMounted, watch } from 'vue'
import { useNotification } from "@kyvg/vue3-notification";

const { notify }  = useNotification()

export default {
  components: {
    StockVn,
  },
  setup() {
    const isConnected = ref(false);
    const selectedSymbol = ref('BTCUSDT');
    const selectedStock = ref(null);
    const stocks = ref([]);
    const symbols = ref(['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'LINKUSDT']); // Example symbols
    const intervals = ['5m','15m', '1h', '4h', '1d'];
    // Use individual refs for each signal
    const signals = {};
    const goldSymbols = ref(['PAXGUSDT']);
    const goldSignals = {};
    const activeConnections = new Map(); // Keep track of active connections

    // Initialize signals object
    symbols.value.forEach(symbol => {
      signals[symbol] = {};
      intervals.forEach(interval => {
        signals[symbol][interval] = ref('Waiting...');
      });
    });

    goldSymbols.value.forEach(symbol=>{
      goldSignals[symbol]={};
      intervals.forEach(interval => {
        goldSignals[symbol][interval]=ref('Waiting...');
      });
    });

   const activeTab = ref('Crypto'); // Initialize activeTab

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

          if (isCandleClosed) {
            console.log(`Candle closed for ${symbol} - ${interval}`);
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

            console.log(`Updating signal for ${symbol} - ${interval}: ${combinedSignal}`);
            if (goldSymbols.value.includes(symbol)) {
              goldSignals[symbol][interval].value = combinedSignal;
            } else {
              signals[symbol][interval].value = combinedSignal; // Update signal using .value
            }
          }
        } catch (error) {
          notify({
            title: "Error",
            text:  `Error fetching ${symbol} in the interval ${interval}.`
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

       goldSymbols.value.forEach(symbol=>{
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
        selectedStock.value = newStock;
    }

     const updateStocks = (newStocks) => {
        stocks.value = newStocks;
    }

    const tabs = ref(['Crypto', 'Stock VN', 'Gold']);
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
      updateStocks
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

.nav-link:hover {
  background-color: #4a5568; /* Darker shade on hover */
}

.nav-link.active {
  background-color: #2d3748; /* Dark background for active tab */
  color: white;
  border-bottom: 2px solid #6cb2eb; /* Highlight active tab */
}

.table-light {
  background-color: #edf2f7;
  text-align: left;
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
