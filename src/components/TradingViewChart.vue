<template>
    <div ref="chartContainer" id="tradingview_chart" class="w-full h-[600px]"></div>
  </template>
  
  <script setup>
  // eslint-disable-next-line no-undef
  const props = defineProps({
    coin: String,
  })

  import { ref, onMounted, watch } from 'vue'
  
  const chartContainer = ref(null)
  
  const initChart = (coin) => {
    if (!window.TradingView) {
      console.error('⚠️ TradingView script chưa sẵn sàng!')
      return
    }
  
    new window.TradingView.widget({
      container_id: `tradingview_chart`,
      autosize: true,
      symbol: coin.includes(':') ? coin : `BINANCE:${coin}`,
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
  #tradingview_chart {
    width: 100%;
    height: 600px;
  }
  </style>
  