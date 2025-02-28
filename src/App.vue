<template>
  <img alt="Vue logo" src="./assets/logo.png">
  <h1>Trading Signals</h1>

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
          <td colspan="3"><strong>{{ symbol }}</strong></td>
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

  <footer>Copyright &copy; by Nguyen The Hao 2025. All rights reserved.</footer>
</template>

<script>
import 'vue3-select/dist/vue3-select.css';
import { ref, onMounted, watch } from 'vue';

export default {
  components: {
  },
  setup() {
    const isConnected = ref(false);
    const selectedSymbol = ref('BTCUSDT');
    const symbols = ref(['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'LINKUSDT']); // Example symbols
    const intervals = ['5m','15m', '30m', '1h', '4h', '1d'];
    // Use individual refs for each signal
    const signals = {};
    const activeConnections = new Map(); // Keep track of active connections

    // Initialize signals object
    symbols.value.forEach(symbol => {
      signals[symbol] = {};
      intervals.forEach(interval => {
        signals[symbol][interval] = ref('Waiting...');
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
          signals[symbol][interval].value = combinedSignal; // Update signal using .value
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

    return {
      isConnected,
      selectedSymbol,
      symbols,
      signals,
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
</style>
