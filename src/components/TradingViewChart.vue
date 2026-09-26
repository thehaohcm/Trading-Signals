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
    // Government Bond Benchmark Yields (OTCB: OTC Bonds)
    'US02Y': 'OTCB:US02Y',
    'US05Y': 'OTCB:US05Y',
    'US10Y': 'OTCB:US10Y',
    'US30Y': 'OTCB:US30Y',
    'GB02Y': 'OTCB:GB02Y',
    'GB10Y': 'OTCB:GB10Y',
    'GB30Y': 'OTCB:GB30Y',
    'UK10Y': 'OTCB:GB10Y',
    'UK02Y': 'OTCB:GB02Y',
    'UK30Y': 'OTCB:GB30Y',
    'JP02Y': 'OTCB:JP02Y',
    'JP10Y': 'OTCB:JP10Y',
    'JP30Y': 'OTCB:JP30Y',
    'DE02Y': 'OTCB:DE02Y',
    'DE05Y': 'OTCB:DE05Y',
    'DE10Y': 'OTCB:DE10Y',
    'DE30Y': 'OTCB:DE30Y'
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

  // Bond & Yield Benchmark mapping for TradingView (OTCB)
  const bondYieldMap = {
    // US Treasury Yields (OTCB)
    'US02Y': 'OTCB:US02Y',
    'US2Y': 'OTCB:US02Y',
    'US05Y': 'OTCB:US05Y',
    'US5Y': 'OTCB:US05Y',
    'US10Y': 'OTCB:US10Y',
    'US30Y': 'OTCB:US30Y',
    // German Bund Yields (OTCB)
    'DE02Y': 'OTCB:DE02Y',
    'DE2Y': 'OTCB:DE02Y',
    'DE05Y': 'OTCB:DE05Y',
    'DE5Y': 'OTCB:DE05Y',
    'DE10Y': 'OTCB:DE10Y',
    'DE30Y': 'OTCB:DE30Y',
    'BUND': 'OTCB:DE10Y',
    // UK Gilt Yields (OTCB)
    'GB02Y': 'OTCB:GB02Y',
    'GB05Y': 'OTCB:GB05Y',
    'GB10Y': 'OTCB:GB10Y',
    'GB30Y': 'OTCB:GB30Y',
    'UK02Y': 'OTCB:GB02Y',
    'UK05Y': 'OTCB:GB05Y',
    'UK10Y': 'OTCB:GB10Y',
    'UK30Y': 'OTCB:GB30Y',
    'UK10': 'OTCB:GB10Y',
    'GILT': 'OTCB:GB10Y',
    // Japan Government Bond Yields (OTCB)
    'JP02Y': 'OTCB:JP02Y',
    'JP2Y': 'OTCB:JP02Y',
    'JP05Y': 'OTCB:JP05Y',
    'JP5Y': 'OTCB:JP05Y',
    'JP10Y': 'OTCB:JP10Y',
    'JP30Y': 'OTCB:JP30Y',
    'JGB': 'OTCB:JP10Y',
    // Australia & Canada & other countries
    'AU02Y': 'OTCB:AU02Y',
    'AU05Y': 'OTCB:AU05Y',
    'AU10Y': 'OTCB:AU10Y',
    'AU30Y': 'OTCB:AU30Y',
    'CA02Y': 'OTCB:CA02Y',
    'CA05Y': 'OTCB:CA05Y',
    'CA10Y': 'OTCB:CA10Y',
    'CA30Y': 'OTCB:CA30Y',
    'KR02Y': 'OTCB:KR02Y',
    'KR05Y': 'OTCB:KR05Y',
    'KR10Y': 'OTCB:KR10Y',
    'KR30Y': 'OTCB:KR30Y',
    'CN02Y': 'OTCB:CN02Y',
    'CN05Y': 'OTCB:CN05Y',
    'CN10Y': 'OTCB:CN10Y',
    'CN30Y': 'OTCB:CN30Y',
    'VN02Y': 'OTCB:VN02Y',
    'VN05Y': 'OTCB:VN05Y',
    'VN10Y': 'OTCB:VN10Y',
    'VN30Y': 'OTCB:VN30Y'
  };

  let symbol = upper;

  // 1. Check Bond / Yield mappings first (even if symbol was passed with BINANCE: or TVC:)
  if (bondYieldMap[core]) {
    symbol = bondYieldMap[core];
  }
  // 2. Other generic country bonds (e.g. IT10Y, FR10Y, CN10Y, VN10Y, ES10Y, AU10Y) -> Use OTCB: prefix
  else if (/^[A-Z]{2}\d{1,2}Y$/i.test(core)) {
    symbol = `OTCB:${core}`;
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