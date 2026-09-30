<template>
  <div class="tradingview-chart-wrapper" :style="wrapperStyle">
    <!-- Top Toolbar: Mode Engine + Interval Switcher -->
    <div v-if="showIntervals" class="tv-interval-toolbar" @click.stop>
      <!-- Engine Switcher (TradingView/Vietstock Native vs HaoNguyen V14.4 Indicator) -->
      <div class="tv-engine-group">
        <!-- If VN Stock: HaoNguyen V14.4 vs Vietstock Gốc -->
        <template v-if="isVnStock">
          <button
            type="button"
            class="tv-engine-btn"
            :class="{ 'is-active': currentEngine === 'vietstock' || currentEngine === 'tradingview' }"
            @click="setEngine('vietstock')"
            title="Biểu đồ Vietstock tiêu chuẩn"
          >
            <i class="fa-solid fa-chart-line text-cyan"></i>
            <span>Vietstock Gốc</span>
          </button>
          <button
            type="button"
            class="tv-engine-btn"
            :class="{ 'is-active': currentEngine === 'haonguyen' }"
            @click="setEngine('haonguyen')"
            title="Biểu đồ Interactive chạy chỉ báo HaoNguyen Boxes V14.4 (VCP Nén, FVG, Order Blocks, EMA 9/21, Fib)"
          >
            <i class="fa-solid fa-bolt text-warning"></i>
            <span>HaoNguyen V14.4</span>
          </button>
        </template>

        <!-- If Global/Crypto/Commodity: TradingView Gốc vs HaoNguyen V14.4 -->
        <template v-else>
          <button
            type="button"
            class="tv-engine-btn"
            :class="{ 'is-active': currentEngine === 'tradingview' }"
            @click="setEngine('tradingview')"
            title="Biểu đồ TradingView tiêu chuẩn"
          >
            <i class="fa-solid fa-chart-line text-cyan"></i>
            <span>TradingView Gốc</span>
          </button>
          <button
            type="button"
            class="tv-engine-btn"
            :class="{ 'is-active': currentEngine === 'haonguyen' }"
            @click="setEngine('haonguyen')"
            title="Biểu đồ Interactive chạy chỉ báo HaoNguyen Boxes V14.4 (VCP Nén, FVG, Order Blocks, EMA 9/21, Fib)"
          >
            <i class="fa-solid fa-bolt text-warning"></i>
            <span>HaoNguyen V14.4</span>
          </button>
        </template>
      </div>

      <!-- Intervals (only when in TradingView Native mode and not VN stock) -->
      <div v-if="!isVnStock && currentEngine === 'tradingview'" class="tv-interval-group ms-auto">
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

      <!-- External Link Button -->
      <a 
        :href="externalChartUrl" 
        target="_blank" 
        rel="noopener noreferrer" 
        class="tv-ext-link-btn"
        :class="{ 'ms-auto': isVnStock || currentEngine !== 'tradingview' }"
        :title="isVnStock ? 'Mở biểu đồ này trên Vietstock.vn' : 'Mở biểu đồ này trên TradingView.com'"
      >
        <i class="fa-solid fa-arrow-up-right-from-square"></i>
      </a>
    </div>

    <!-- Mode 1: HaoNguyen Lightweight Chart with Custom Pine Indicators (Gold, Crypto, Commodities, VN Stocks) -->
    <div v-if="currentEngine === 'haonguyen'" class="hn-engine-wrapper">
      <HaoNguyenLightweightChart 
        :coin="coin" 
        :height="height" 
        :theme="theme" 
        :default-interval="currentInterval"
        :entry-price="entryPrice"
        @update:interval="onHnIntervalChange"
      />
    </div>

    <!-- Mode 2: Vietstock Iframe Container (for VN Stock) -->
    <div 
      v-if="isVnStock && (currentEngine === 'vietstock' || currentEngine === 'tradingview')"
      class="vietstock-chart-container" 
      :style="chartContainerStyle"
    >
      <iframe
        :key="resolvedVietstockCode"
        :src="`https://stockchart.vietstock.vn/?stockcode=${resolvedVietstockCode}`"
        width="100%"
        height="100%"
        frameborder="0"
        allowfullscreen
        style="display: block; border: none; background: #ffffff; width: 100%; height: 100%; min-height: 500px;"
      ></iframe>
    </div>

    <!-- Mode 3: Standard TradingView Iframe Widget Container (for Non-VN Stock) -->
    <div 
      v-show="!isVnStock && currentEngine === 'tradingview'"
      :id="containerId" 
      ref="chartContainer" 
      class="tradingview-chart-container" 
      :style="chartContainerStyle"
    ></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import HaoNguyenLightweightChart from './HaoNguyenLightweightChart.vue'

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
  defaultEngine: {
    type: String,
    default: ''
  },
  entryPrice: {
    type: [Number, String],
    default: null
  },
  theme: {
    type: String,
    default: 'dark'
  },
  studies: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:interval', 'update:engine'])

const knownCryptoList = [
  'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'DOT', 'LINK',
  'NEAR', 'SUI', 'APT', 'OP', 'ARB', 'PEPE', 'SHIB', 'UNI', 'LTC', 'BCH',
  'FET', 'RENDER', 'INJ', 'TIA', 'SEI', 'ATOM', 'FIL', 'ICP', 'TRX', 'MATIC',
  'POL', 'FTM', 'SAND', 'MANA', 'AXS', 'GALA', 'CHZ', 'CRV', 'AAVE', 'MKR',
  'SNX', 'DYDX', 'RUNE', 'KAS', 'ALGO', 'VET', 'ETC', 'XLM', 'HBAR',
  'FLOW', 'NEO', 'QNT', 'EGLD', 'RNDR', 'STX', 'ORDI', 'SATS', 'TAO', 'WLD', 'BLUR', 'MEME',
  'STRK', 'JTO', 'BEAM', 'RON', 'PORTAL', 'PIXEL', 'AEVO', 'TNSR', 'IO', 'ZK', 'LISTA',
  'ZRO', 'NOT', 'DOGS', 'CATI', 'HMSTR', 'EIGEN', 'NEIRO', 'TURBO', 'BABY'
]

const isVnStock = computed(() => {
  const raw = String(props.coin || '').trim().toUpperCase()
  if (raw.startsWith('HOSE:') || raw.startsWith('HNX:') || raw.startsWith('UPCOM:')) return true
  const clean = raw.includes(':') ? raw.split(':').pop().trim() : raw
  const isVnIndex = ['VNINDEX', 'VN30', 'VN30F1M', 'VN30FM1', 'HNXINDEX', 'UPCOMINDEX'].includes(clean)
  if (isVnIndex) return true
  const isLikelyVnTicker = /^[A-Z0-9]{3}$/.test(clean) && !knownCryptoList.includes(clean) && !['USD', 'EUR', 'JPY', 'GBP', 'AUD', 'CAD', 'CHF', 'NZD', 'SGD', 'HKD', 'WTI', 'OIL', 'SPX', 'DJI', 'NDX', 'DAX', 'DXY', 'EWY', 'NI225'].includes(clean)
  return isLikelyVnTicker
})

const resolvedVietstockCode = computed(() => {
  const upper = String(props.coin || '').trim().toUpperCase()
  const clean = upper.includes(':') ? upper.split(':').pop().trim() : upper
  if (clean === 'VN30FM1') return 'VN30F1M'
  if (clean === 'UPCOMINDEX') return 'UPCOMINDEX'
  return clean
})

const getInitialEngine = () => {
  if (props.defaultEngine) return props.defaultEngine
  if (isVnStock.value) return 'vietstock'
  return localStorage.getItem('tv_preferred_engine') || 'tradingview'
}

// Engine Selection: prioritize props.defaultEngine if passed, otherwise localStorage, then 'tradingview'
const currentEngine = ref(getInitialEngine())

const setEngine = (eng) => {
  currentEngine.value = eng
  try {
    if (!isVnStock.value) {
      localStorage.setItem('tv_preferred_engine', eng)
    }
  } catch (e) {
    console.warn(e)
  }
  emit('update:engine', eng)
  if (eng === 'tradingview' && !isVnStock.value) {
    if (!window.TradingView) {
      const script = document.createElement('script')
      script.src = 'https://s3.tradingview.com/tv.js'
      script.onload = () => initChart(props.coin)
      document.body.appendChild(script)
    } else {
      initChart(props.coin)
    }
  }
}

watch(() => props.defaultEngine, (newEngine) => {
  if (newEngine && newEngine !== currentEngine.value) {
    setEngine(newEngine)
  }
})

watch(() => isVnStock.value, (isVn) => {
  if (isVn && (currentEngine.value !== 'haonguyen' && currentEngine.value !== 'vietstock')) {
    setEngine(props.defaultEngine || 'haonguyen')
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

const normalizeTvInterval = (val) => {
  if (!val) return 'D'
  const v = String(val).toUpperCase().trim()
  if (v === '5M' || v === '5') return '5'
  if (v === '1M' || v === '1') return '1'
  if (v === '15M' || v === '15') return '15'
  if (v === '1H' || v === '60') return '60'
  if (v === '4H' || v === '240') return '240'
  if (v === '1D' || v === 'D') return 'D'
  return 'D'
}

const getInitialInterval = () => {
  if (props.defaultInterval && props.defaultInterval !== 'D') {
    return normalizeTvInterval(props.defaultInterval)
  }
  try {
    const saved = localStorage.getItem('tv_preferred_interval')
    if (saved && intervalOptions.some(item => item.value === saved)) {
      return saved
    }
  } catch (e) {
    console.warn('Could not read preferred interval from localStorage:', e)
  }
  return normalizeTvInterval(props.defaultInterval) || 'D'
}

const currentInterval = ref(getInitialInterval())

watch(() => props.defaultInterval, (newVal) => {
  if (newVal) {
    const mapped = normalizeTvInterval(newVal)
    if (currentInterval.value !== mapped) {
      selectInterval(mapped)
    }
  }
})

const onHnIntervalChange = (val) => {
  const tvVal = val === '1d' ? 'D' : (val === '4h' ? '240' : (val === '1h' ? '60' : (val === '15m' ? '15' : (val === '5m' ? '5' : '1'))))
  currentInterval.value = tvVal
  try {
    localStorage.setItem('tv_preferred_interval', tvVal)
  } catch (e) {
    console.warn(e)
  }
  emit('update:interval', tvVal)
}

const selectInterval = (val) => {
  if (currentInterval.value === val) return
  currentInterval.value = val
  try {
    localStorage.setItem('tv_preferred_interval', val)
  } catch (e) {
    console.warn('Could not save preferred interval to localStorage:', e)
  }
  emit('update:interval', val)
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

const externalChartUrl = computed(() => {
  if (isVnStock.value) {
    return `https://stockchart.vietstock.vn/?stockcode=${resolvedVietstockCode.value}`
  }
  let sym = (props.coin || 'BTCUSDT').trim().toUpperCase()
  if (['XAUUSD', 'GOLD', 'GC'].includes(sym)) sym = 'OANDA:XAUUSD'
  return `https://www.tradingview.com/chart/?symbol=${sym}`
})

const initChart = (coin) => {
  if (currentEngine.value !== 'tradingview') return
  if (!window.TradingView) {
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

  const notOnBinance = {
    'XMRUSDT': 'KRAKEN:XMRUSD',
    'XMRBTC': 'KRAKEN:XMRBTC',
    'XMR': 'KRAKEN:XMRUSD',
    'ZCASHUSDT': 'KRAKEN:ZECUSD',
    'ZEC': 'KRAKEN:ZECUSD'
  }

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

  let rawSym = (coin || '').trim()
  let upper = rawSym.toUpperCase()
  let core = upper
  if (core.includes(':')) {
    core = core.split(':').pop().trim()
  }

  const bondRegex = /^([A-Z]{2}\d{1,2}Y)(?:USDT|USD|\.P)?$/i
  const bondMatch = core.match(bondRegex)
  if (bondMatch) {
    core = bondMatch[1].toUpperCase()
  }

  const bondYieldMap = {
    'US02Y': 'OTCB:US02Y',
    'US2Y': 'OTCB:US02Y',
    'US05Y': 'OTCB:US05Y',
    'US5Y': 'OTCB:US05Y',
    'US10Y': 'OTCB:US10Y',
    'US30Y': 'OTCB:US30Y',
    'DE02Y': 'OTCB:DE02Y',
    'DE2Y': 'OTCB:DE02Y',
    'DE05Y': 'OTCB:DE05Y',
    'DE5Y': 'OTCB:DE05Y',
    'DE10Y': 'OTCB:DE10Y',
    'DE30Y': 'OTCB:DE30Y',
    'BUND': 'OTCB:DE10Y',
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
    'JP02Y': 'OTCB:JP02Y',
    'JP2Y': 'OTCB:JP02Y',
    'JP05Y': 'OTCB:JP05Y',
    'JP5Y': 'OTCB:JP05Y',
    'JP10Y': 'OTCB:JP10Y',
    'JP30Y': 'OTCB:JP30Y',
    'JGB': 'OTCB:JP10Y',
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
  }

  let symbol = upper

  if (bondYieldMap[core]) {
    symbol = bondYieldMap[core]
  } else if (/^[A-Z]{2}\d{1,2}Y$/i.test(core)) {
    symbol = `OTCB:${core}`
  } else if (/^(FX|FX_IDC|ICE|BINANCE):USDVND$/i.test(upper) || core === 'USDVND') {
    symbol = 'USDVND'
  } else if (indexAliases[core]) {
    symbol = indexAliases[core]
  } else if (notOnBinance[core]) {
    symbol = notOnBinance[core]
  } else if (cryptoShorthands[core]) {
    symbol = cryptoShorthands[core]
  } else if (forexPairs.includes(core)) {
    symbol = `FX:${core}`
  } else if (upper.includes(':') && !upper.startsWith('BINANCE:')) {
    symbol = upper
  } else if (core.endsWith('USDT')) {
    symbol = `BINANCE:${core}`
  } else {
    symbol = core
  }

  const isDark = props.theme !== 'light'

  const widgetConfig = {
    container_id: containerId,
    autosize: true,
    symbol: symbol,
    interval: currentInterval.value,
    timezone: 'Asia/BangKok',
    theme: isDark ? 'dark' : 'light', 
    style: '1',
    locale: 'en',
    toolbar_bg: isDark ? '#131722' : '#f1f3f6',
    enable_publishing: false,
    allow_symbol_change: true,
    hide_side_toolbar: false,
    save_image: true,
    studies: props.studies
  }

  new window.TradingView.widget(widgetConfig)
}

onMounted(() => {
  if (!isVnStock.value && currentEngine.value === 'tradingview') {
    if (!window.TradingView) {
      const script = document.createElement('script')
      script.src = 'https://s3.tradingview.com/tv.js'
      script.onload = () => initChart(props.coin)
      document.body.appendChild(script)
    } else {
      initChart(props.coin)
    }
  }
})

watch(() => props.coin, (newCoin) => {
  if (!isVnStock.value && currentEngine.value === 'tradingview') {
    initChart(newCoin)
  }
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
  padding: 5px 8px;
  background: rgba(13, 17, 28, 0.95);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  gap: 8px;
  user-select: none;
  z-index: 10;
}

/* Engine Switcher Group */
.tv-engine-group {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: rgba(255, 255, 255, 0.04);
  padding: 2px 4px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.tv-engine-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
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

.tv-engine-btn:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

.tv-engine-btn.is-active {
  color: #0f172a !important;
  font-weight: 700;
  background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%) !important;
  box-shadow: 0 2px 8px rgba(56, 189, 248, 0.35);
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

.tv-ext-link-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-decoration: none;
  font-size: 11px;
  transition: all 0.2s;
}

.tv-ext-link-btn:hover {
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
  border-color: #38bdf8;
}

.hn-engine-wrapper {
  flex: 1 1 0%;
  width: 100%;
  height: 100%;
  min-height: 0;
  display: flex;
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