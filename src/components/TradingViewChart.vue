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
      'WTI': 'TVC:USOIL',
      'USOIL': 'TVC:USOIL',
      'CL': 'NYMEX:CL1!',
      'BRENT': 'TVC:UKOIL',
      'UKOIL': 'TVC:UKOIL',
      'NIKKEI225': 'TVC:NI225',
      'NI225': 'TVC:NI225',
      'NIKKEI': 'TVC:NI225',
      'KOSPI': 'KRX:KOSPI',
      'SHANGHAI': 'SSE:000001',
      'SHCOMP': 'SSE:000001',
      'VNINDEX': 'HOSE:VNINDEX',
      'FTSE': 'TVC:UKX',
      'FTSE100': 'TVC:UKX',
      'DAX': 'TVC:DEU40',
      'DAX40': 'TVC:DEU40',
      'SPX': 'FOREXCOM:SPXUSD',
      'DXY': 'CAPITALCOM:DXY',
    }

    // Coins not listed on Binance - use alternative exchanges
    const notOnBinance = {
      'XMRUSDT': 'KRAKEN:XMRUSD',
      'XMRBTC': 'KRAKEN:XMRBTC',
      'XMR': 'KRAKEN:XMRUSD',
      'ZCASHUSDT': 'KRAKEN:ZECUSD',
      'ZEC': 'KRAKEN:ZECUSD'
    }

    let symbol = coin || ''

    // Government Bond Yields: TVC: prefix on yields (e.g. TVC:DE10Y, TVC:US10Y) triggers
    // "This symbol is only available on TradingView" popup on free widgets.
    // Strip TVC: to use the clean OTC Bond market symbol (e.g. DE10Y, US10Y, JP10Y).
    if (/^TVC:([A-Z]{2}[0-9]{2}Y)$/i.test(symbol)) {
      symbol = symbol.replace(/^TVC:/i, '')
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
    // If it's a crypto pair ending with USDT, use Binance
    else if (symbol && symbol.toUpperCase().endsWith('USDT')) {
      symbol = `BINANCE:${symbol}`
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
  