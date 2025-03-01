<template>
  <notifications />
  <img alt="Vue logo" src="./assets/logo.png" style="width: 150px;">
  <h1>Trading Signals</h1>

  <!-- Tabs -->
  <div class="tabs">
    <div
      v-for="(tab, index) in tabs"
      :key="index"
      :class="{ active: activeTab === tab }"
      @click="activeTab = tab"
    >
      {{ tab }}
    </div>
  </div>

  <!-- Tab Content -->
  <div v-if="activeTab === 'Crypto'">
    <table v-if="Object.keys(signals).length > 0">
      <thead>
        <tr style="text-align: center;">
          <th>Symbol</th>
          <th>Interval</th>
          <th>Signal</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(signalData, symbol) in signals" :key="symbol">
          <tr>
            <td colspan="3"><strong><a :href="'https://www.binance.com/en/trade/' + symbol.split('USDT')[0] + '_USDT?type=spot'" target="_blank">{{ symbol }}</a></strong></td>
          </tr>
          <template v-for="(intervalData, interval) in signalData" :key="`${symbol}-${interval}`">
            <tr>
              <td></td>
              <td>{{ interval }}</td>
              <td>{{ signals[symbol][interval].value }}</td>
            </tr>
          </template>
        </template>
      </tbody>
    </table>

    <p v-if="isConnected" style="color: green;">WebSocket is connected</p>
    <p v-else style="color:red">WebSocket is disconnected</p>
  </div>

  <div v-if="activeTab === 'Gold'">
    <table v-if="Object.keys(goldSignals).length > 0">
      <thead>
        <tr style="text-align: center;">
          <th>Symbol</th>
          <th>Interval</th>
          <th>Signal</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(signalData, symbol) in goldSignals" :key="symbol">
          <tr>
            <td colspan="3"><strong>Gold</strong></td>
          </tr>
          <template v-for="(intervalData, interval) in signalData" :key="`${symbol}-${interval}`">
            <tr>
              <td></td>
              <td>{{ interval }}</td>
              <td>{{ goldSignals['PAXGUSDT'][interval].value }}</td>
            </tr>
          </template>
        </template>
      </tbody>
    </table>

    <p v-if="isConnected" style="color: green;">WebSocket is connected</p>
    <p v-else style="color:red">WebSocket is disconnected</p>
  </div>
  <div v-if="activeTab === 'Stock VN'" class="stock-vn-container">
    <p>Input a VN stock symbol (3 capital letters):</p>
    <div>
      <v-select v-model="selectedStock" :options="stocks" label="code" @input="onStockSelected" placeholder="Search stock code..."></v-select>
    </div>
    <div>
      <StockVn style="width: 500px;" v-if="activeTab === 'Stock VN'" @update:selectedStock="updateSelectedStock"  @update:stocks="updateStocks"/>
    </div>
  </div>

  <footer>Copyright &copy; by Nguyen The Hao 2025. All rights reserved.</footer>
</template>

<style scoped>
.stock-vn-container {
  display: flex;
  justify-content: center;
  flex-direction: column; /* Stack items vertically */
  align-items: center; /* Center items horizontally */
}
</style>

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
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

table {
  margin: 20px auto;
  border-collapse: collapse;
  width: 80%;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}

.tabs {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.tabs div {
  padding: 10px 20px;
  cursor: pointer;
  border: 1px solid #ddd;
  margin: 0 5px;
  border-radius: 5px 5px 0 0;
}

.tabs div.active {
  background-color: #f2f2f2;
  border-bottom: none;
}

.tab-content {
    border: 1px solid #ddd;
    padding: 20px;
    text-align: center;
    margin: 0 5px;
}
</style>
