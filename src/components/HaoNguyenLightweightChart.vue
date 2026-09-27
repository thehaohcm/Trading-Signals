<template>
  <div class="haonguyen-chart-container" ref="containerRef">
    <!-- Top Toolbar -->
    <div class="hn-toolbar">
      <div class="hn-left-controls">
        <!-- Interval Selector -->
        <div class="hn-btn-group">
          <button
            v-for="tf in intervals"
            :key="tf.value"
            class="hn-btn"
            :class="{ 'is-active': activeInterval === tf.value }"
            @click="changeInterval(tf.value)"
          >
            {{ tf.label }}
          </button>
        </div>

        <!-- Indicator Toggles Dropdown / Buttons -->
        <div class="hn-indicator-toggles">
          <button 
            class="hn-toggle-btn" 
            :class="{ 'is-on': showEMA }" 
            @click="toggleEMA"
            title="Bật/Tắt EMA 9 & EMA 21"
          >
            <span class="hn-dot hn-dot--ema"></span> EMA 9/21
          </button>
          <button 
            class="hn-toggle-btn" 
            :class="{ 'is-on': showFVG }" 
            @click="toggleFVG"
            title="Bật/Tắt Fair Value Gap (FVG - SMC)"
          >
            <span class="hn-dot hn-dot--fvg"></span> FVG
          </button>
          <button 
            class="hn-toggle-btn" 
            :class="{ 'is-on': showOB }" 
            @click="toggleOB"
            title="Bật/Tắt Order Blocks (OB - SMC)"
          >
            <span class="hn-dot hn-dot--ob"></span> Order Blocks
          </button>
          <button 
            class="hn-toggle-btn" 
            :class="{ 'is-on': showFib }" 
            @click="toggleFib"
            title="Bật/Tắt Hộp Sideway & Fib Target (TP1/TP2/SL)"
          >
            <span class="hn-dot hn-dot--fib"></span> Fib TP/SL
          </button>
        </div>
      </div>

      <!-- Right Stats Badge -->
      <div class="hn-stats" v-if="latestBar">
        <div class="hn-stat-item">
          <span class="hn-stat-label">Price:</span>
          <span class="hn-stat-val" :class="priceChange >= 0 ? 'text-green' : 'text-red'">
            ${{ formatPrice(latestBar.close) }}
          </span>
        </div>
        <div class="hn-stat-item" v-if="currentRSI">
          <span class="hn-stat-label">RSI(14):</span>
          <span class="hn-stat-val" :class="currentRSI > 70 ? 'text-red' : (currentRSI < 30 ? 'text-green' : 'text-cyan')">
            {{ currentRSI.toFixed(1) }}
          </span>
        </div>
        <div class="hn-stat-item" v-if="trendStatus">
          <span class="hn-badge" :class="trendClass">{{ trendStatus }}</span>
        </div>
        <div class="hn-badge hn-badge--ver">V14.4 SMC</div>
      </div>
    </div>

    <!-- Chart Canvas Element -->
    <div class="hn-chart-canvas" ref="chartDivRef">
      <!-- Loading Overlay -->
      <div v-if="isLoading" class="hn-loading-overlay">
        <div class="hn-spinner"></div>
        <span>Đang nạp dữ liệu nến & tính toán chỉ báo V14.4...</span>
      </div>

      <!-- Error State -->
      <div v-if="loadError" class="hn-error-overlay">
        <i class="fa-solid fa-triangle-exclamation text-amber"></i>
        <span>{{ loadError }}</span>
        <button class="hn-retry-btn" @click="fetchData">Thử lại</button>
      </div>

      <!-- Legend Overlay (Values on hover) -->
      <div class="hn-legend-overlay" v-if="legendData && !isLoading">
        <span class="legend-symbol">{{ displaySymbol }}</span>
        <span>O: <b>{{ formatPrice(legendData.open) }}</b></span>
        <span>H: <b>{{ formatPrice(legendData.high) }}</b></span>
        <span>L: <b>{{ formatPrice(legendData.low) }}</b></span>
        <span>C: <b>{{ formatPrice(legendData.close) }}</b></span>
        <span v-if="legendData.ema9" class="legend-ema9">EMA9: <b>{{ formatPrice(legendData.ema9) }}</b></span>
        <span v-if="legendData.ema21" class="legend-ema21">EMA21: <b>{{ formatPrice(legendData.ema21) }}</b></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  ColorType,
  CrosshairMode,
  createSeriesMarkers
} from 'lightweight-charts'
import axios from 'axios'

const props = defineProps({
  coin: {
    type: String,
    default: 'BTCUSDT'
  },
  height: {
    type: [Number, String],
    default: 520
  },
  theme: {
    type: String,
    default: 'dark'
  }
})

const containerRef = ref(null)
const chartDivRef = ref(null)
const isLoading = ref(false)
const loadError = ref(null)

const intervals = [
  { label: '1m', value: '1m', binance: '1m', yahoo: '1m' },
  { label: '5m', value: '5m', binance: '5m', yahoo: '5m' },
  { label: '15m', value: '15m', binance: '15m', yahoo: '15m' },
  { label: '1H', value: '1h', binance: '1h', yahoo: '60m' },
  { label: '4H', value: '4h', binance: '4h', yahoo: '1d' },
  { label: '1D', value: '1d', binance: '1d', yahoo: '1d' }
]
const activeInterval = ref('1d')

// Indicators Toggles
const showEMA = ref(true)
const showFVG = ref(true)
const showOB = ref(true)
const showFib = ref(true)

const latestBar = ref(null)
const priceChange = ref(0)
const currentRSI = ref(null)
const trendStatus = ref('')
const trendClass = ref('text-cyan')
const legendData = ref(null)

let chart = null
let candleSeries = null
let volumeSeries = null
let ema9Series = null
let ema21Series = null
let fibTP1Series = null
let fibTP2Series = null
let fibSLSeries = null
let boxTopSeries = null
let boxBotSeries = null
let markersPrimitive = null

let ws = null

// -------------------------------------------------------------
// SYMBOL RESOLVER
// -------------------------------------------------------------
const resolveSymbolInfo = (raw) => {
  let sym = (raw || 'BTCUSDT').trim().toUpperCase()
  if (sym.includes(':')) {
    sym = sym.split(':').pop().trim()
  }
  sym = sym.replace(/\.P$/i, '').replace(/=F$/i, '')

  // 1. Gold / Vàng
  if (['XAUUSD', 'GOLD', 'GC', 'XAU', 'PAXG', 'PAXGUSDT'].includes(sym)) {
    return {
      spotSymbol: 'PAXGUSDT',
      futuresSymbol: 'PAXGUSDT',
      yahooSymbol: 'GC=F',
      displayName: 'Gold / USD (PAXG)'
    }
  }

  // 2. Silver / Bạc
  if (['XAGUSD', 'SILVER', 'SI', 'XAG'].includes(sym)) {
    return {
      spotSymbol: null,
      futuresSymbol: 'XAGUSDT',
      yahooSymbol: 'SI=F',
      displayName: 'Silver / USD'
    }
  }

  // 3. Oil / Dầu
  if (['USOIL', 'WTI', 'CL', 'OIL'].includes(sym)) {
    return {
      spotSymbol: null,
      futuresSymbol: null,
      yahooSymbol: 'CL=F',
      displayName: 'WTI Crude Oil'
    }
  }
  if (['UKOIL', 'BRENT', 'BZ'].includes(sym)) {
    return {
      spotSymbol: null,
      futuresSymbol: null,
      yahooSymbol: 'BZ=F',
      displayName: 'Brent Oil'
    }
  }

  // 4. Forex
  const forexPairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD']
  if (forexPairs.includes(sym)) {
    return {
      spotSymbol: null,
      futuresSymbol: null,
      yahooSymbol: `${sym}=X`,
      displayName: sym
    }
  }
  if (sym === 'USDVND') {
    return {
      spotSymbol: null,
      futuresSymbol: null,
      yahooSymbol: 'USDVND=X',
      displayName: 'USD/VND'
    }
  }

  // 5. Crypto
  let cryptoPair = sym
  if (!cryptoPair.endsWith('USDT') && !cryptoPair.includes('USD') && !cryptoPair.includes('BTC') && !cryptoPair.includes('ETH')) {
    cryptoPair += 'USDT'
  }
  return {
    spotSymbol: cryptoPair,
    futuresSymbol: cryptoPair,
    yahooSymbol: null,
    displayName: cryptoPair
  }
}

const resolvedInfo = computed(() => resolveSymbolInfo(props.coin))
const displaySymbol = computed(() => resolvedInfo.value.displayName)

const formatPrice = (val) => {
  if (val === undefined || val === null || isNaN(val)) return '--'
  if (val >= 1000) return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (val >= 1) return val.toFixed(4)
  return val.toFixed(6)
}

// -------------------------------------------------------------
// TECHNICAL INDICATOR CALCULATIONS (Pine Script V14.4 in JS)
// -------------------------------------------------------------
function calculateEMA(data, period) {
  const k = 2 / (period + 1)
  const result = []
  let ema = null
  for (let i = 0; i < data.length; i++) {
    const val = data[i].close
    if (i < period - 1) {
      continue
    }
    if (ema === null) {
      let sum = 0
      for (let j = i - period + 1; j <= i; j++) sum += data[j].close
      ema = sum / period
    } else {
      ema = val * k + ema * (1 - k)
    }
    result.push({ time: data[i].time, value: ema })
  }
  return result
}

function calculateRSI(data, period = 14) {
  if (data.length < period + 1) return null
  let gains = 0
  let losses = 0
  for (let i = 1; i <= period; i++) {
    const diff = data[i].close - data[i - 1].close
    if (diff >= 0) gains += diff
    else losses -= diff
  }
  let avgGain = gains / period
  let avgLoss = losses / period

  for (let i = period + 1; i < data.length; i++) {
    const diff = data[i].close - data[i - 1].close
    const gain = diff >= 0 ? diff : 0
    const loss = diff < 0 ? -diff : 0
    avgGain = (avgGain * (period - 1) + gain) / period
    avgLoss = (avgLoss * (period - 1) + loss) / period
  }
  if (avgLoss === 0) return 100
  const rs = avgGain / avgLoss
  return 100 - (100 / (1 + rs))
}

function computeHaoNguyenV14(bars) {
  // 1. Calculate EMAs
  const ema9Data = calculateEMA(bars, 9)
  const ema21Data = calculateEMA(bars, 21)

  const markers = []

  // 2. Scan FVG (Fair Value Gaps) - 3 candle imbalance
  for (let i = 2; i < bars.length; i++) {
    const c0 = bars[i - 2]
    const c1 = bars[i - 1]
    const c2 = bars[i]

    // Bullish FVG: Low of candle 2 > High of candle 0
    if (c2.low > c0.high) {
      if (i >= bars.length - 25) {
        markers.push({
          time: c1.time,
          position: 'belowBar',
          color: '#10b981',
          shape: 'arrowUp',
          text: 'Bull FVG'
        })
      }
    }
    // Bearish FVG: High of candle 2 < Low of candle 0
    else if (c2.high < c0.low) {
      if (i >= bars.length - 25) {
        markers.push({
          time: c1.time,
          position: 'aboveBar',
          color: '#ef4444',
          shape: 'arrowDown',
          text: 'Bear FVG'
        })
      }
    }
  }

  // 3. Scan Order Blocks (OB)
  for (let i = 2; i < bars.length; i++) {
    const prev = bars[i - 1]
    const curr = bars[i]
    // Bullish displacement: curr is strong green breaking prev high
    if (curr.close > curr.open && (curr.close - curr.open) > (curr.high - curr.low) * 0.6 && prev.close < prev.open) {
      if (i >= bars.length - 20) {
        markers.push({
          time: prev.time,
          position: 'belowBar',
          color: '#38bdf8',
          shape: 'circle',
          text: 'OB Bull'
        })
      }
    }
    // Bearish displacement: curr is strong red breaking prev low
    if (curr.close < curr.open && (curr.open - curr.close) > (curr.high - curr.low) * 0.6 && prev.close > prev.open) {
      if (i >= bars.length - 20) {
        markers.push({
          time: prev.time,
          position: 'aboveBar',
          color: '#f59e0b',
          shape: 'circle',
          text: 'OB Bear'
        })
      }
    }
  }

  // 4. Wyckoff Sideway Box & Fib Targets on recent 30 bars
  const lookback = Math.min(30, bars.length)
  const recentSlice = bars.slice(bars.length - lookback)
  let boxHigh = -Infinity
  let boxLow = Infinity
  recentSlice.forEach(b => {
    if (b.high > boxHigh) boxHigh = b.high
    if (b.low < boxLow) boxLow = b.low
  })

  const boxRange = boxHigh - boxLow
  const fibTP1 = boxHigh + boxRange * 0.272
  const fibTP2 = boxHigh + boxRange * 0.618
  const fibSL = boxHigh - boxRange * 0.5

  const boxTopData = []
  const boxBotData = []
  const tp1Data = []
  const tp2Data = []
  const slData = []

  bars.forEach((b, idx) => {
    if (idx >= bars.length - lookback) {
      boxTopData.push({ time: b.time, value: boxHigh })
      boxBotData.push({ time: b.time, value: boxLow })
      tp1Data.push({ time: b.time, value: fibTP1 })
      tp2Data.push({ time: b.time, value: fibTP2 })
      slData.push({ time: b.time, value: fibSL })
    }
  })

  return {
    ema9Data,
    ema21Data,
    markers,
    boxTopData,
    boxBotData,
    tp1Data,
    tp2Data,
    slData
  }
}

// -------------------------------------------------------------
// INIT & RENDER CHART
// -------------------------------------------------------------
const initChart = () => {
  if (!chartDivRef.value) return

  // Dispose previous
  if (chart) {
    chart.remove()
    chart = null
    markersPrimitive = null
  }

  const isDark = props.theme !== 'light'

  chart = createChart(chartDivRef.value, {
    autoSize: true,
    layout: {
      background: { type: ColorType.Solid, color: isDark ? '#131722' : '#ffffff' },
      textColor: isDark ? '#94a3b8' : '#334155'
    },
    grid: {
      vertLines: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' },
      horzLines: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' }
    },
    crosshair: {
      mode: CrosshairMode.Normal
    },
    rightPriceScale: {
      borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
    },
    timeScale: {
      borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
      timeVisible: true,
      secondsVisible: false,
      rightOffset: 30,
      barSpacing: 9,
      fixLeftEdge: false,
      fixRightEdge: false
    }
  })

  // Candlestick series (v5 syntax: addSeries)
  candleSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#10b981',
    downColor: '#ef4444',
    borderVisible: false,
    wickUpColor: '#10b981',
    wickDownColor: '#ef4444'
  })

  // Volume series
  volumeSeries = chart.addSeries(HistogramSeries, {
    color: '#26a69a',
    priceFormat: { type: 'volume' },
    priceScaleId: ''
  })
  volumeSeries.priceScale().applyOptions({
    scaleMargins: {
      top: 0.8,
      bottom: 0
    }
  })

  // EMA 9 Series
  ema9Series = chart.addSeries(LineSeries, {
    color: '#38bdf8',
    lineWidth: 1.5,
    title: 'EMA 9',
    visible: showEMA.value
  })

  // EMA 21 Series
  ema21Series = chart.addSeries(LineSeries, {
    color: '#f59e0b',
    lineWidth: 2,
    title: 'EMA 21',
    visible: showEMA.value
  })

  // Fib Targets & Sideway Box Series
  boxTopSeries = chart.addSeries(LineSeries, {
    color: '#00bcd4',
    lineWidth: 1,
    lineStyle: 2,
    title: 'Box High',
    visible: showFib.value
  })
  boxBotSeries = chart.addSeries(LineSeries, {
    color: '#00bcd4',
    lineWidth: 1,
    lineStyle: 2,
    title: 'Box Low',
    visible: showFib.value
  })
  fibTP1Series = chart.addSeries(LineSeries, {
    color: '#10b981',
    lineWidth: 1.5,
    lineStyle: 1,
    title: 'Fib TP1 (1.272)',
    visible: showFib.value
  })
  fibTP2Series = chart.addSeries(LineSeries, {
    color: '#06b6d4',
    lineWidth: 1.5,
    lineStyle: 1,
    title: 'Fib TP2 (1.618)',
    visible: showFib.value
  })
  fibSLSeries = chart.addSeries(LineSeries, {
    color: '#ef4444',
    lineWidth: 1.5,
    lineStyle: 1,
    title: 'Fib SL (0.5)',
    visible: showFib.value
  })

  // Crosshair move handler for legend
  chart.subscribeCrosshairMove(param => {
    if (!param.time || !param.seriesData || !param.seriesData.get(candleSeries)) {
      if (latestBar.value) {
        legendData.value = latestBar.value
      }
      return
    }
    const bar = param.seriesData.get(candleSeries)
    const ema9Val = param.seriesData.get(ema9Series)
    const ema21Val = param.seriesData.get(ema21Series)
    legendData.value = {
      ...bar,
      ema9: ema9Val?.value,
      ema21: ema21Val?.value
    }
  })
}

// -------------------------------------------------------------
// MULTI-SOURCE RESILIENT DATA FETCHER
// -------------------------------------------------------------
const fetchData = async () => {
  isLoading.value = true
  loadError.value = null
  try {
    await nextTick()
    if (!chart) initChart()

    const info = resolvedInfo.value
    const binanceInterval = intervals.find(i => i.value === activeInterval.value)?.binance || '1d'
    const yahooInterval = intervals.find(i => i.value === activeInterval.value)?.yahoo || '1d'

    let candleData = []
    let volData = []
    let fetchedFrom = null

    // 1. Try Binance Spot
    if (info.spotSymbol) {
      try {
        const spotUrl = `https://api.binance.com/api/v3/klines?symbol=${info.spotSymbol}&interval=${binanceInterval}&limit=350`
        const res = await axios.get(spotUrl, { timeout: 8000 })
        if (Array.isArray(res.data) && res.data.length > 0) {
          res.data.forEach(item => {
            const time = Math.floor(item[0] / 1000)
            const open = parseFloat(item[1])
            const high = parseFloat(item[2])
            const low = parseFloat(item[3])
            const close = parseFloat(item[4])
            const vol = parseFloat(item[5])
            candleData.push({ time, open, high, low, close })
            volData.push({
              time,
              value: vol,
              color: close >= open ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'
            })
          })
          fetchedFrom = 'binance_spot'
        }
      } catch (e) {
        console.warn('Binance spot failed, fallback to next source:', e.message)
      }
    }

    // 2. Try Binance USD-M Futures (if spot failed or not available)
    if (candleData.length === 0 && info.futuresSymbol) {
      try {
        const futUrl = `https://fapi.binance.com/fapi/v1/klines?symbol=${info.futuresSymbol}&interval=${binanceInterval}&limit=350`
        const res = await axios.get(futUrl, { timeout: 8000 })
        if (Array.isArray(res.data) && res.data.length > 0) {
          res.data.forEach(item => {
            const time = Math.floor(item[0] / 1000)
            const open = parseFloat(item[1])
            const high = parseFloat(item[2])
            const low = parseFloat(item[3])
            const close = parseFloat(item[4])
            const vol = parseFloat(item[5])
            candleData.push({ time, open, high, low, close })
            volData.push({
              time,
              value: vol,
              color: close >= open ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'
            })
          })
          fetchedFrom = 'binance_futures'
        }
      } catch (e) {
        console.warn('Binance futures failed, fallback to next source:', e.message)
      }
    }

    // 3. Try Yahoo Finance (Forex, Commodities, Indices)
    if (candleData.length === 0 && info.yahooSymbol) {
      try {
        const yahooUrl = `https://query1.finance.yahoo.com/v8/finance/chart/${info.yahooSymbol}?interval=${yahooInterval}&range=1y`
        const res = await axios.get(yahooUrl, { timeout: 8000 })
        const result = res.data?.chart?.result?.[0]
        if (result && result.timestamp && result.indicators?.quote?.[0]) {
          const timestamps = result.timestamp
          const quotes = result.indicators.quote[0]
          timestamps.forEach((ts, idx) => {
            const open = quotes.open[idx]
            const high = quotes.high[idx]
            const low = quotes.low[idx]
            const close = quotes.close[idx]
            const vol = quotes.volume ? quotes.volume[idx] || 0 : 0
            if (open !== null && close !== null && !isNaN(open) && !isNaN(close)) {
              candleData.push({ time: ts, open, high, low, close })
              volData.push({
                time: ts,
                value: vol,
                color: close >= open ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'
              })
            }
          })
          fetchedFrom = 'yahoo'
        }
      } catch (e) {
        console.warn('Yahoo finance chart failed:', e.message)
      }
    }

    if (candleData.length === 0) {
      throw new Error(`Chưa tìm thấy dữ liệu nến cho ${props.coin}. Bạn có thể bấm nút "TradingView Gốc" ở trên để xem đầy đủ.`)
    }

    // Populate data to chart series
    candleSeries.setData(candleData)
    volumeSeries.setData(volData)

    // Compute indicator features
    const calc = computeHaoNguyenV14(candleData)

    ema9Series.setData(calc.ema9Data)
    ema21Series.setData(calc.ema21Data)

    boxTopSeries.setData(calc.boxTopData)
    boxBotSeries.setData(calc.boxBotData)
    fibTP1Series.setData(calc.tp1Data)
    fibTP2Series.setData(calc.tp2Data)
    fibSLSeries.setData(calc.slData)

    // Set markers on candles (v5 syntax: createSeriesMarkers)
    const validMarkers = (showFVG.value || showOB.value) ? calc.markers.sort((a, b) => a.time - b.time) : []
    if (!markersPrimitive) {
      markersPrimitive = createSeriesMarkers(candleSeries, validMarkers)
    } else {
      markersPrimitive.setMarkers(validMarkers)
    }

    // Update Stats
    const last = candleData[candleData.length - 1]
    const prev = candleData[candleData.length - 2]
    latestBar.value = last
    legendData.value = last
    priceChange.value = prev ? ((last.close - prev.close) / prev.close) * 100 : 0
    currentRSI.value = calculateRSI(candleData, 14)

    // Trend assessment
    const lastEMA9 = calc.ema9Data[calc.ema9Data.length - 1]?.value
    const lastEMA21 = calc.ema21Data[calc.ema21Data.length - 1]?.value
    if (last && lastEMA9 && lastEMA21) {
      if (last.close > lastEMA9 && lastEMA9 > lastEMA21) {
        trendStatus.value = 'TĂNG MẠNH (Bullish)'
        trendClass.value = 'badge--bull'
      } else if (last.close < lastEMA9 && lastEMA9 < lastEMA21) {
        trendStatus.value = 'GIẢM (Bearish)'
        trendClass.value = 'badge--bear'
      } else {
        trendStatus.value = 'SIDEWAY / TÍCH LŨY'
        trendClass.value = 'badge--sideway'
      }
    }

    // Hiển thị nến ở khoảng 2/3 khung hình, để trống 1/3 bên phải để không bị các nhãn Fib TP1/TP2/SL che
    const totalBars = candleData.length
    const visibleCount = Math.min(100, totalBars)
    chart.timeScale().setVisibleLogicalRange({
      from: totalBars - visibleCount,
      to: totalBars + 35 // Chừa khoảng trống 35 bars (~1/3 bên phải)
    })

    // Connect WebSocket if binance source
    if (fetchedFrom === 'binance_spot' && info.spotSymbol) {
      connectWebSocket(info.spotSymbol, binanceInterval)
    }

  } catch (err) {
    console.error('Lỗi nạp chart lightweight:', err)
    loadError.value = `${err.message}`
  } finally {
    isLoading.value = false
  }
}

// -------------------------------------------------------------
// WEBSOCKET REAL-TIME LIVE TICKS
// -------------------------------------------------------------
const connectWebSocket = (symbol, interval) => {
  if (ws) {
    ws.close()
    ws = null
  }
  try {
    const wsUrl = `wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}@kline_${interval}`
    ws = new WebSocket(wsUrl)
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg && msg.k) {
        const k = msg.k
        const time = Math.floor(k.t / 1000)
        const updatedBar = {
          time,
          open: parseFloat(k.o),
          high: parseFloat(k.h),
          low: parseFloat(k.l),
          close: parseFloat(k.c)
        }
        if (candleSeries) {
          candleSeries.update(updatedBar)
          latestBar.value = updatedBar
          legendData.value = updatedBar
        }
      }
    }
  } catch (e) {
    console.warn('WS error:', e)
  }
}

// -------------------------------------------------------------
// CONTROLS & TOGGLES
// -------------------------------------------------------------
const changeInterval = (val) => {
  activeInterval.value = val
  fetchData()
}

const toggleEMA = () => {
  showEMA.value = !showEMA.value
  if (ema9Series) ema9Series.applyOptions({ visible: showEMA.value })
  if (ema21Series) ema21Series.applyOptions({ visible: showEMA.value })
}

const toggleFVG = () => {
  showFVG.value = !showFVG.value
  fetchData()
}

const toggleOB = () => {
  showOB.value = !showOB.value
  fetchData()
}

const toggleFib = () => {
  showFib.value = !showFib.value
  if (boxTopSeries) boxTopSeries.applyOptions({ visible: showFib.value })
  if (boxBotSeries) boxBotSeries.applyOptions({ visible: showFib.value })
  if (fibTP1Series) fibTP1Series.applyOptions({ visible: showFib.value })
  if (fibTP2Series) fibTP2Series.applyOptions({ visible: showFib.value })
  if (fibSLSeries) fibSLSeries.applyOptions({ visible: showFib.value })
}

watch(() => props.coin, () => {
  fetchData()
})

onMounted(() => {
  fetchData()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
  if (chart) {
    chart.remove()
    chart = null
    markersPrimitive = null
  }
})
</script>

<style scoped>
.haonguyen-chart-container {
  width: 100%;
  height: 100%;
  min-height: 480px;
  display: flex;
  flex-direction: column;
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
}

/* Toolbar */
.hn-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
  background: #131d31;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.hn-left-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.hn-btn-group {
  display: flex;
  background: rgba(0, 0, 0, 0.3);
  padding: 2px;
  border-radius: 6px;
  gap: 2px;
}

.hn-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.hn-btn:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

.hn-btn.is-active {
  color: #ffffff;
  background: #38bdf8;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
}

.hn-indicator-toggles {
  display: flex;
  gap: 6px;
}

.hn-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.hn-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.hn-toggle-btn.is-on {
  background: rgba(56, 189, 248, 0.15);
  border-color: #38bdf8;
  color: #e0f2fe;
}

.hn-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.hn-dot--ema { background: #38bdf8; }
.hn-dot--fvg { background: #10b981; }
.hn-dot--ob { background: #f59e0b; }
.hn-dot--fib { background: #a855f7; }

/* Stats */
.hn-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}

.hn-stat-item {
  display: flex;
  gap: 4px;
}
.hn-stat-label {
  color: #64748b;
}
.hn-stat-val {
  font-weight: 700;
}

.text-green { color: #10b981; }
.text-red { color: #ef4444; }
.text-cyan { color: #38bdf8; }
.text-amber { color: #f59e0b; }

.hn-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}
.badge--bull {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.4);
}
.badge--bear {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.4);
}
.badge--sideway {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.4);
}
.hn-badge--ver {
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
  border: 1px solid rgba(168, 85, 247, 0.4);
}

/* Canvas Area */
.hn-chart-canvas {
  flex: 1;
  width: 100%;
  height: calc(100% - 45px);
  position: relative;
  min-height: 420px;
}

/* Legend Overlay */
.hn-legend-overlay {
  position: absolute;
  top: 10px;
  left: 12px;
  z-index: 10;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(6px);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  color: #cbd5e1;
  display: flex;
  gap: 10px;
  pointer-events: none;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.legend-symbol {
  font-weight: 700;
  color: #38bdf8;
}
.legend-ema9 { color: #38bdf8; }
.legend-ema21 { color: #f59e0b; }

/* Loading & Error */
.hn-loading-overlay, .hn-error-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.9);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  z-index: 20;
  color: #cbd5e1;
  font-size: 13px;
  padding: 20px;
  text-align: center;
}

.hn-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(56, 189, 248, 0.2);
  border-top-color: #38bdf8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.hn-retry-btn {
  background: #38bdf8;
  color: #0f172a;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
</style>
