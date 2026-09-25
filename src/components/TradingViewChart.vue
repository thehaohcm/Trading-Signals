<template>
  <div class="tradingview-chart-wrapper" :style="wrapperStyle">
    <!-- Interval Toolbar: 1D (default), 4H, 1H, 5m, 1m -->
    <div v-if="showIntervals" class="tv-interval-toolbar" @click.stop>
      <div class="tv-interval-group">
        <button
          v-for="item in intervalOptions"
          :key="item.value"
          type="button"
          class="tv-interval-btn"
          :class="{ 'is-active': currentInterval === item.value }"
          @click="selectInterval(item.value)"
          :title="`Khung thời gian ${item.label}`"
        >
          {{ item.label }}
        </button>
      </div>
    </div>

    <!-- TradingView Chart Container -->
    <div 
      :id="containerId" 
      ref="chartContainer" 
      class="tradingview-chart-container" 
      :style="chartContainerStyle"
    ></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps({
  coin: String,
  height: {
    type: [Number, String],
    default: 520
  },
  showIntervals: {
    type: Boolean,
    default: true
  },
  defaultInterval: {
    type: String,
    default: 'D'
  },
  theme: {
    type: String,
    default: 'dark'
  }
})

const intervalOptions = [
  { label: '1D', value: 'D' },
  { label: '4H', value: '240' },
  { label: '1H', value: '60' },
  { label: '30m', value: '30' },
  { label: '15m', value: '15' },
  { label: '5m', value: '5' },
  { label: '1m', value: '1' }
]

const getInitialInterval = () => {
  try {
    const saved = localStorage.getItem('tv_preferred_interval')
    if (saved && intervalOptions.some(item => item.value === saved)) {
      return saved
    }
  } catch (e) {
    console.warn('Could not read preferred interval from localStorage:', e)
  }
  return props.defaultInterval || 'D'
}

const currentInterval = ref(getInitialInterval())

const selectInterval = (val) => {
  if (currentInterval.value === val) return
  currentInterval.value = val
  try {
    localStorage.setItem('tv_preferred_interval', val)
  } catch (e) {
    console.warn('Could not save preferred interval to localStorage:', e)
  }
  initChart(props.coin)
}

const chartContainer = ref(null)
const containerId = `tradingview_chart_${Math.random().toString(36).substr(2, 9)}`

const isPercentHeight = computed(() => {
  return typeof props.height === 'string' && props.height.includes('%')
})

const wrapperStyle = computed(() => {
  if (typeof props.height === 'number') {
    return {
      height: `${props.height}px`,
      minHeight: `${props.height}px`,
      width: '100%',
      display: 'flex',
      flexDirection: 'column'
    }
  }
  if (isPercentHeight.value || props.height === '100%' || props.height === 100 || props.height === '100') {
    return {
      height: '100%',
      minHeight: '0',
      width: '100%',
      flex: '1',
      display: 'flex',
      flexDirection: 'column'
    }
  }
  return {
    height: props.height || '100%',
    minHeight: props.height || '0',
    width: '100%',
    display: 'flex',
    flexDirection: 'column'
  }
})

const chartContainerStyle = computed(() => {
  return {
    flex: '1 1 0%',
    minHeight: '0',
    width: '100%',
    height: '100%'
  }
})

const initChart = (coin) => {
  if (!window.TradingView) {
    console.error('⚠️ TradingView script chưa sẵn sàng!')
    return
  }

  // Clear previous chart
  if (chartContainer.value) {
    chartContainer.value.innerHTML = ''
  }

  // Global indices & commodities alias mapping for TradingView
  const indexAliases = {
    'GC=F': 'OANDA:XAUUSD',
    'GC': 'OANDA:XAUUSD',
    'GOLD': 'OANDA:XAUUSD',
    'XAUUSD': 'OANDA:XAUUSD',
    'SI=F': 'OANDA:XAGUSD',
    'SI': 'OANDA:XAGUSD',
    'SILVER': 'OANDA:XAGUSD',
    'XAGUSD': 'OANDA:XAGUSD',
    'CL=F': 'TVC:USOIL',
    'CL': 'NYMEX:CL1!',
    'WTI': 'TVC:USOIL',
    'USOIL': 'TVC:USOIL',
    'BZ=F': 'TVC:UKOIL',
    'BRENT': 'TVC:UKOIL',
    'UKOIL': 'TVC:UKOIL',
    'HG=F': 'CAPITALCOM:COPPER',
    'COPPER': 'CAPITALCOM:COPPER',
    'NG=F': 'TVC:NATGAS',
    'NATGAS': 'TVC:NATGAS',
    'NIKKEI225': 'FOREXCOM:JP225',
    'NI225': 'FOREXCOM:JP225',
    'NIKKEI': 'FOREXCOM:JP225',
    'KOSPI': 'AMEX:EWY',
    'EWY': 'AMEX:EWY',
    'KRX:KOSPI': 'AMEX:EWY',
    'SHANGHAI': 'SSE:000001',
    'SHCOMP': 'SSE:000001',
    'VNINDEX': 'HOSE:VNINDEX',
    'VN30': 'HOSE:VN30',
    'FTSE': 'FOREXCOM:UK100',
    'FTSE100': 'FOREXCOM:UK100',
    'UK100': 'FOREXCOM:UK100',
    'DAX': 'FOREXCOM:GER40',
    'DAX40': 'FOREXCOM:GER40',
    'GER40': 'FOREXCOM:GER40',
    'DEU40': 'FOREXCOM:GER40',
    'SPX': 'FOREXCOM:SPXUSD',
    '^GSPC': 'FOREXCOM:SPXUSD',
    'US30': 'FOREXCOM:DJI',
    'DJI': 'FOREXCOM:DJI',
    '^DJI': 'FOREXCOM:DJI',
    'NDX': 'NASDAQ:NDX',
    'NASDAQ': 'NASDAQ:NDX',
    '^IXIC': 'NASDAQ:NDX',
    'DXY': 'CAPITALCOM:DXY',
    'USDVND': 'USDVND',
    // Government Bond Benchmark Futures (TVC: yields are blocked by TV widget data licensing)
    'US02Y': 'CBOT:ZT1!',
    'US05Y': 'CBOT:ZF1!',
    'US10Y': 'CBOT:ZN1!',
    'US30Y': 'CBOT:ZB1!',
    'GB02Y': 'ICEEUR:G1!',
    'GB10Y': 'ICEEUR:G1!',
    'GB30Y': 'ICEEUR:G1!',
    'UK10Y': 'ICEEUR:G1!',
    'UK02Y': 'ICEEUR:G1!',
    'UK30Y': 'ICEEUR:G1!',
    'JP02Y': 'OSE:2JGB1!',
    'JP10Y': 'OSE:2JGB1!',
    'JP30Y': 'OSE:2JGB1!',
    'DE02Y': 'EUREX:FGBS1!',
    'DE05Y': 'EUREX:FGBM1!',
    'DE10Y': 'EUREX:FGBL1!',
    'DE30Y': 'EUREX:FGBX1!'
  }

  // Coins not listed on Binance - use alternative exchanges
  const notOnBinance = {
    'XMRUSDT': 'KRAKEN:XMRUSD',
    'XMRBTC': 'KRAKEN:XMRBTC',
    'XMR': 'KRAKEN:XMRUSD',
    'ZCASHUSDT': 'KRAKEN:ZECUSD',
    'ZEC': 'KRAKEN:ZECUSD'
  }

  // Popular cryptos shorthand without USDT
  const cryptoShorthands = {
    'BTC': 'BINANCE:BTCUSDT',
    'ETH': 'BINANCE:ETHUSDT',
    'SOL': 'BINANCE:SOLUSDT',
    'BNB': 'BINANCE:BNBUSDT',
    'XRP': 'BINANCE:XRPUSDT',
    'DOGE': 'BINANCE:DOGEUSDT',
    'ADA': 'BINANCE:ADAUSDT',
    'AVAX': 'BINANCE:AVAXUSDT',
    'DOT': 'BINANCE:DOTUSDT',
    'LINK': 'BINANCE:LINKUSDT',
    'NEAR': 'BINANCE:NEARUSDT',
    'SUI': 'BINANCE:SUIUSDT',
    'APT': 'BINANCE:APTUSDT',
    'OP': 'BINANCE:OPUSDT',
    'ARB': 'BINANCE:ARBUSDT',
    'PEPE': 'BINANCE:PEPEUSDT',
    'SHIB': 'BINANCE:SHIBUSDT'
  }

  const forexPairs = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD',
    'EURJPY', 'GBPJPY', 'AUDJPY', 'EURGBP', 'EURAUD', 'EURCHF', 'GBPAUD'
  ]

  let rawSym = (coin || '').trim();
  let upper = rawSym.toUpperCase();

  // Extract core symbol (e.g. strip BINANCE:, TVC:, FX:, etc. to verify if it's actually a bond, index, or commodity)
  let core = upper;
  if (core.includes(':')) {
    core = core.split(':').pop().trim();
  }

  // Strip trailing USDT, USD, or .P if mistakenly attached to bond codes (e.g. JP30YUSDT -> JP30Y)
  const bondRegex = /^([A-Z]{2}\d{1,2}Y)(?:USDT|USD|\.P)?$/i;
  const bondMatch = core.match(bondRegex);
  if (bondMatch) {
    core = bondMatch[1].toUpperCase();
  }

  // Bond & Yield Benchmark Futures mapping for TradingView
  const bondFuturesMap = {
    // US Treasury Futures (CBOT)
    'US02Y': 'CBOT:ZT1!',
    'US2Y': 'CBOT:ZT1!',
    'US05Y': 'CBOT:ZF1!',
    'US5Y': 'CBOT:ZF1!',
    'US10Y': 'CBOT:ZN1!',
    'US30Y': 'CBOT:ZB1!',
    // German Bund/Bobl/Schatz/Buxl Futures (EUREX)
    'DE02Y': 'EUREX:FGBS1!',
    'DE2Y': 'EUREX:FGBS1!',
    'DE05Y': 'EUREX:FGBM1!',
    'DE5Y': 'EUREX:FGBM1!',
    'DE10Y': 'EUREX:FGBL1!',
    'DE30Y': 'EUREX:FGBX1!',
    'BUND': 'EUREX:FGBL1!',
    // UK Gilt Futures (ICE)
    'GB02Y': 'ICEEUR:G1!',
    'GB05Y': 'ICEEUR:G1!',
    'GB10Y': 'ICEEUR:G1!',
    'GB30Y': 'ICEEUR:G1!',
    'UK02Y': 'ICEEUR:G1!',
    'UK05Y': 'ICEEUR:G1!',
    'UK10Y': 'ICEEUR:G1!',
    'UK30Y': 'ICEEUR:G1!',
    'UK10': 'ICEEUR:G1!',
    'GILT': 'ICEEUR:G1!',
    // Japan Government Bond Futures (OSE)
    'JP02Y': 'OSE:2JGB1!',
    'JP05Y': 'OSE:2JGB1!',
    'JP10Y': 'OSE:2JGB1!',
    'JP30Y': 'OSE:2JGB1!',
    'JGB': 'OSE:2JGB1!'
  };

  let symbol = upper;

  // 1. Check Bond / Yield futures mappings first (even if symbol was passed with BINANCE: or TVC:)
  if (bondFuturesMap[core]) {
    symbol = bondFuturesMap[core];
  }
  // 2. Other generic country bonds (e.g. IT10Y, FR10Y, CN10Y, VN10Y, ES10Y, AU10Y) -> Use raw symbol directly without BINANCE:
  else if (/^[A-Z]{2}\d{1,2}Y$/i.test(core)) {
    symbol = core;
  }
  // 3. USDVND mapping
  else if (/^(FX|FX_IDC|ICE|BINANCE):USDVND$/i.test(upper) || core === 'USDVND') {
    symbol = 'USDVND';
  }
  // 4. Global indices & commodities alias mapping
  else if (indexAliases[core]) {
    symbol = indexAliases[core];
  }
  // 5. Crypto not on Binance
  else if (notOnBinance[core]) {
    symbol = notOnBinance[core];
  }
  // 6. Crypto shorthand without USDT (e.g. BTC, ETH)
  else if (cryptoShorthands[core]) {
    symbol = cryptoShorthands[core];
  }
  // 7. Forex pairs
  else if (forexPairs.includes(core)) {
    symbol = `FX:${core}`;
  }
  // 8. If already has legitimate exchange prefix (e.g. NASDAQ:AAPL, HOSE:VNINDEX), keep as-is
  else if (upper.includes(':') && !upper.startsWith('BINANCE:')) {
    symbol = upper;
  }
  // 9. Crypto pair ending with USDT
  else if (core.endsWith('USDT')) {
    symbol = `BINANCE:${core}`;
  }
  // 10. Default fallback
  else {
    symbol = core;
  }

  const isDark = props.theme !== 'light'

  const widgetConfig = {
    container_id: containerId,
    autosize: true,
    symbol: symbol,
    interval: currentInterval.value,
    timezone: 'Asia/BangKok', // UTC+7
    theme: isDark ? 'dark' : 'light', 
    style: '1',
    locale: 'en',
    toolbar_bg: isDark ? '#131722' : '#f1f3f6',
    enable_publishing: false,
    allow_symbol_change: true,
    hide_side_toolbar: false,
    save_image: true,
  }

  new window.TradingView.widget(widgetConfig)
}

onMounted(() => {
  // Nạp script TradingView nếu chưa có
  if (!window.TradingView) {
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/tv.js'
    script.onload = () => initChart(props.coin)
    document.body.appendChild(script)
  } else {
    initChart(props.coin)
  }
})

// Khi prop coin thay đổi thì tự load lại chart với interval đã chọn
watch(() => props.coin, (newCoin) => {
  initChart(newCoin)
})
</script>

<style scoped>
.tradingview-chart-wrapper {
  width: 100%;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  position: relative;
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
}

.tv-interval-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 4px 8px;
  background: rgba(13, 17, 28, 0.95);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  gap: 6px;
  user-select: none;
  z-index: 10;
}

.tv-interval-group {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: rgba(255, 255, 255, 0.04);
  padding: 2px 4px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.tv-interval-btn {
  padding: 3px 10px;
  font-size: 0.74rem;
  font-weight: 600;
  color: #94a3b8;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.18s ease;
  line-height: 1.2;
}

.tv-interval-btn:hover {
  color: #00f2fe;
  background: rgba(0, 242, 254, 0.08);
}

.tv-interval-btn.is-active {
  color: #0a0d14 !important;
  font-weight: 700;
  background: linear-gradient(135deg, #00f2fe 0%, #38bdf8 100%) !important;
  box-shadow: 0 2px 8px rgba(0, 242, 254, 0.35);
}

.tradingview-chart-container {
  width: 100%;
  height: 100%;
  min-height: 0;
  flex: 1 1 0%;
  display: flex;
  flex-direction: column;
}

.tradingview-chart-container :deep(iframe) {
  width: 100% !important;
  height: 100% !important;
  border: none !important;
  display: block;
}
</style>