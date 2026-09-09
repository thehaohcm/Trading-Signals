<template>
    <div :id="containerId" ref="chartContainer" class="tradingview-chart-container" :style="{ minHeight: `${height}px`, height: `${height}px` }"></div>
  </template>
  
  <script setup>
  // eslint-disable-next-line no-undef
  const props = defineProps({
    coin: String,
    height: {
      type: [Number, String],
      default: 600
    }
  })

  import { ref, onMounted, watch } from 'vue'
  
  const chartContainer = ref(null)
  const containerId = `tradingview_chart_${Math.random().toString(36).substr(2, 9)}`
  
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

    // Government Bond Yields: TVC: prefix on yields (e.g. TVC:DE10Y, TVC:US10Y) triggers
    // "This symbol is only available on TradingView" popup on free widgets.
    // Strip TVC: to use the clean OTC Bond market symbol (e.g. DE10Y, US10Y, JP10Y).
    if (/^TVC:([A-Z]{2}[0-9]{2}Y)$/i.test(symbol)) {
      symbol = symbol.replace(/^TVC:/i, '')
    }

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
  
    new window.TradingView.widget({
      container_id: containerId,
      width: '100%',
      height: props.height,
      symbol: symbol,
      interval: '1D',
      timezone: 'Asia/BangKok', // UTC+7
      theme: 'light', 
      style: '1',
      locale: 'en',
      toolbar_bg: '#f1f3f6',
      enable_publishing: false,
    })
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
  }
  </style>
  