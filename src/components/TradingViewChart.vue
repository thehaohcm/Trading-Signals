<template>
  <div 
    :id="containerId" 
    ref="chartContainer" 
    class="tradingview-chart-container" 
    :style="chartContainerStyle"
  ></div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps({
  coin: String,
  height: {
    type: [Number, String],
    default: 600
  }
})

const chartContainer = ref(null)
const containerId = `tradingview_chart_${Math.random().toString(36).substr(2, 9)}`

const isPercentHeight = computed(() => {
  return typeof props.height === 'string' && props.height.includes('%')
})

const chartContainerStyle = computed(() => {
  if (typeof props.height === 'number') {
    return {
      height: `${props.height}px`,
      minHeight: `${props.height}px`,
      width: '100%'
    }
  }
  if (isPercentHeight.value || props.height === '100%') {
    return {
      height: '100%',
      minHeight: '0',
      width: '100%',
      flex: '1'
    }
  }
  return {
    height: props.height || '100%',
    minHeight: props.height || '0',
    width: '100%'
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

  let symbol = coin || ''

  // Government Bond Yields: TVC: prefix on yields (e.g. TVC:US10Y) triggers
  // "This symbol is only available on TradingView" popup on free widgets.
  // Map them to benchmark CBOT/EUREX/ICE futures.
  if (/^TVC:(US02Y|US2Y|ZT)$/i.test(symbol)) symbol = 'CBOT:ZT1!'
  else if (/^TVC:(US05Y|US5Y|ZF)$/i.test(symbol)) symbol = 'CBOT:ZF1!'
  else if (/^TVC:(US10Y|TNX|ZN)$/i.test(symbol)) symbol = 'CBOT:ZN1!'
  else if (/^TVC:(US30Y|TYX|ZB)$/i.test(symbol)) symbol = 'CBOT:ZB1!'
  else if (/^TVC:(DE02Y|DE2Y|FGBS)$/i.test(symbol)) symbol = 'EUREX:FGBS1!'
  else if (/^TVC:(DE05Y|DE5Y|FGBM)$/i.test(symbol)) symbol = 'EUREX:FGBM1!'
  else if (/^TVC:(DE10Y|BUND|FGBL)$/i.test(symbol)) symbol = 'EUREX:FGBL1!'
  else if (/^TVC:(DE30Y|FGBX)$/i.test(symbol)) symbol = 'EUREX:FGBX1!'
  else if (/^TVC:(GB02Y|GB10Y|GB30Y|UK02Y|UK10Y|UK30Y|GILT)$/i.test(symbol)) symbol = 'ICEEUR:G1!'
  else if (/^TVC:(JP02Y|JP10Y|JP30Y|JGB)$/i.test(symbol)) symbol = 'OSE:2JGB1!'

  // USDVND: TradingView does not support FX:USDVND or FX_IDC:USDVND on free widget;
  // use raw 'USDVND' (ICE:USDVND).
  if (/^(FX|FX_IDC|ICE):USDVND$/i.test(symbol) || symbol.toUpperCase() === 'USDVND') {
    symbol = 'USDVND'
  }
  
  // If coin has exchange prefix already, use as-is
  if (symbol.includes(':')) {
    // Keep as-is
  } 
  // Check if it's a global index or alias
  else if (indexAliases[symbol.toUpperCase()]) {
    symbol = indexAliases[symbol.toUpperCase()]
  }
  // Check if it's a crypto not on Binance
  else if (notOnBinance[symbol.toUpperCase()]) {
    symbol = notOnBinance[symbol.toUpperCase()]
  }
  // Check if it's a crypto shorthand (e.g. BTC, ETH)
  else if (cryptoShorthands[symbol.toUpperCase()]) {
    symbol = cryptoShorthands[symbol.toUpperCase()]
  }
  // Check if it's a common 6-letter forex pair
  else if (forexPairs.includes(symbol.toUpperCase())) {
    symbol = `FX:${symbol.toUpperCase()}`
  }
  // If it's a crypto pair ending with USDT, use Binance
  else if (symbol && symbol.toUpperCase().endsWith('USDT')) {
    symbol = `BINANCE:${symbol.toUpperCase()}`
  }
  // Otherwise use raw symbol (stocks, government bonds DE10Y, US10Y, etc.)
  else {
    // Use raw symbol
  }

  const isFullHeight = isPercentHeight.value || props.height === '100%' || props.height === 100 || props.height === '100'

  const widgetConfig = {
    container_id: containerId,
    width: '100%',
    height: isFullHeight ? '100%' : props.height,
    symbol: symbol,
    interval: '1D',
    timezone: 'Asia/BangKok', // UTC+7
    theme: 'light', 
    style: '1',
    locale: 'en',
    toolbar_bg: '#f1f3f6',
    enable_publishing: false,
    autosize: isFullHeight ? true : false,
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

// Khi prop coin thay đổi thì tự load lại chart
watch(() => props.coin, (newCoin) => {
  initChart(newCoin)
})
</script>

<style scoped>
.tradingview-chart-container {
  width: 100%;
  height: 100%;
  min-height: 0;
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
  