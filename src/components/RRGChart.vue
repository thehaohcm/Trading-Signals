<template>
  <div ref="tradingviewContainer" class="tradingview-widget-container"></div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const tradingviewContainer = ref(null)

onMounted(() => {
  if (!window.TradingView) {
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/tv.js'
    script.onload = initTradingView
    document.head.appendChild(script)
  } else {
    initTradingView()
  }
})

function initTradingView() {
  if (!tradingviewContainer.value) return

  /* eslint-disable no-undef */
  new TradingView.widget({
    container_id: tradingviewContainer.value,
    autosize: true,
    symbol: 'BINANCE:BTCUSDT',
    interval: '1D',
    timezone: 'Asia/Bangkok',
    theme: 'light',
    style: '1',
    locale: 'en',
    hide_top_toolbar: false,
    hide_legend: false,
    save_image: false,
  })
  /* eslint-enable no-undef */
}
</script>

<style scoped>
.tradingview-widget-container {
  width: 100%;
  height: 600px;
}
</style>
