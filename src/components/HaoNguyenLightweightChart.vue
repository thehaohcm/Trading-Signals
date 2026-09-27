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
            :class="{ 'is-on': showVCP }" 
            @click="toggleVCP"
            title="Bật/Tắt VCP Nén & Hộp mờ Box 21/Box 9"
          >
            <span class="hn-dot hn-dot--vcp"></span> ⚡ Hộp VCP Nén
          </button>
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
            title="Bật/Tắt Vùng mờ Fair Value Gap (FVG - SMC)"
          >
            <span class="hn-dot hn-dot--fvg"></span> Hộp FVG
          </button>
          <button 
            class="hn-toggle-btn" 
            :class="{ 'is-on': showOB }" 
            @click="toggleOB"
            title="Bật/Tắt Order Blocks (OB - SMC)"
          >
            <span class="hn-dot hn-dot--ob"></span> Order Blocks
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

        <!-- VCP Badge Status -->
        <div class="hn-stat-item" v-if="vcpInfo">
          <span 
            class="hn-badge" 
            :class="vcpInfo.isVCP ? 'badge--vcp-active' : 'badge--vcp-normal'"
            :title="`Tỷ lệ nén Box9/Box21: ${(vcpInfo.ratio * 100).toFixed(1)}%`"
          >
            ⚡ VCP {{ vcpInfo.isVCP ? `NÉN ✓ (${(vcpInfo.ratio * 100).toFixed(0)}%)` : `${(vcpInfo.ratio * 100).toFixed(0)}%` }}
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
      <!-- HTML5 Canvas Overlay for Beautiful Shaded Boxes & Labels -->
      <canvas ref="overlayCanvasRef" class="hn-overlay-canvas"></canvas>

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
        <span v-if="vcpInfo && vcpInfo.isVCP" class="legend-vcp">VCP: <b>NÉN ({{ (vcpInfo.ratio * 100).toFixed(0) }}%)</b></span>
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
const overlayCanvasRef = ref(null)
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
const showVCP = ref(true)
const showEMA = ref(true)
const showFVG = ref(true)
const showOB = ref(true)

const latestBar = ref(null)
const priceChange = ref(0)
const currentRSI = ref(null)
const trendStatus = ref('')
const trendClass = ref('text-cyan')
const vcpInfo = ref(null)
const legendData = ref(null)

let chart = null
let candleSeries = null
let volumeSeries = null
let ema9Series = null
let ema21Series = null
let markersPrimitive = null

let calculatedOverlayData = null
let rawBars = []
let ws = null
let resizeObserver = null

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
// TECHNICAL INDICATOR CALCULATIONS
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
  const n = bars.length

  // 1. Calculate EMAs
  const ema9Data = calculateEMA(bars, 9)
  const ema21Data = calculateEMA(bars, 21)

  const markers = []
  const fvgBands = []

  // 2. Scan FVG (Fair Value Gaps)
  for (let i = 2; i < n; i++) {
    const c0 = bars[i - 2]
    const c1 = bars[i - 1]
    const c2 = bars[i]

    if (c2.low > c0.high) {
      fvgBands.push({
        type: 'BULL_FVG',
        startTime: c0.time,
        endTime: c2.time,
        top: c2.low,
        bottom: c0.high
      })
      if (i >= n - 25) {
        markers.push({
          time: c1.time,
          position: 'belowBar',
          color: '#10b981',
          shape: 'arrowUp',
          text: 'Bull FVG'
        })
      }
    }
    else if (c2.high < c0.low) {
      fvgBands.push({
        type: 'BEAR_FVG',
        startTime: c0.time,
        endTime: c2.time,
        top: c0.low,
        bottom: c2.high
      })
      if (i >= n - 25) {
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
  for (let i = 2; i < n; i++) {
    const prev = bars[i - 1]
    const curr = bars[i]
    if (curr.close > curr.open && (curr.close - curr.open) > (curr.high - curr.low) * 0.6 && prev.close < prev.open) {
      if (i >= n - 20) {
        markers.push({
          time: prev.time,
          position: 'belowBar',
          color: '#38bdf8',
          shape: 'circle',
          text: 'OB Bull'
        })
      }
    }
    if (curr.close < curr.open && (curr.open - curr.close) > (curr.high - curr.low) * 0.6 && prev.close > prev.open) {
      if (i >= n - 20) {
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

  // 4. VCP (Volatility Contraction Pattern) Box 21 & Box 9
  let h21 = -Infinity, l21 = Infinity
  let h9 = -Infinity, l9 = Infinity
  const startIdx21 = Math.max(0, n - 21)
  const startIdx9 = Math.max(0, n - 9)

  for (let i = startIdx21; i < n; i++) {
    const bH = Math.max(bars[i].open, bars[i].close)
    const bL = Math.min(bars[i].open, bars[i].close)
    if (bH > h21) h21 = bH
    if (bL < l21) l21 = bL
  }
  for (let i = startIdx9; i < n; i++) {
    const bH = Math.max(bars[i].open, bars[i].close)
    const bL = Math.min(bars[i].open, bars[i].close)
    if (bH > h9) h9 = bH
    if (bL < l9) l9 = bL
  }

  const range21 = h21 - l21
  const range9 = h9 - l9
  const vcpRatio = range21 > 0 ? (range9 / range21) : 1
  const isVCP = range21 > 0 && vcpRatio <= 0.5

  // 5. Wyckoff Sideway Box & Fib Targets
  const lookback = Math.min(30, n)
  const startIdx30 = n - lookback
  let boxHigh = -Infinity
  let boxLow = Infinity
  for (let i = startIdx30; i < n; i++) {
    if (bars[i].high > boxHigh) boxHigh = bars[i].high
    if (bars[i].low < boxLow) boxLow = bars[i].low
  }

  const boxRange = boxHigh - boxLow
  const fibTP1 = boxHigh + boxRange * 0.272
  const fibTP2 = boxHigh + boxRange * 0.618
  const fibSL = boxHigh - boxRange * 0.5

  return {
    ema9Data,
    ema21Data,
    markers,
    fvgBands,
    vcp: {
      isVCP,
      ratio: vcpRatio,
      startTime21: bars[startIdx21]?.time,
      startTime9: bars[startIdx9]?.time,
      endTime: bars[n - 1]?.time,
      h21,
      l21,
      h9,
      l9
    },
    fib: {
      startTime: bars[startIdx30]?.time,
      endTime: bars[n - 1]?.time,
      boxHigh,
      boxLow,
      fibTP1,
      fibTP2,
      fibSL
    }
  }
}

// -------------------------------------------------------------
// DRAW CANVAS OVERLAY (TRANSLUCENT SHADED BOXES & LABELS)
// -------------------------------------------------------------
const drawBoxesOverlay = () => {
  const canvas = overlayCanvasRef.value
  const div = chartDivRef.value
  if (!canvas || !div || !chart || !candleSeries || !calculatedOverlayData) return

  const rect = div.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1

  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  canvas.style.width = `${rect.width}px`
  canvas.style.height = `${rect.height}px`

  const ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, rect.width, rect.height)

  const timeScale = chart.timeScale()
  const lastBarTime = calculatedOverlayData.vcp?.endTime
  if (!lastBarTime) return

  const lastX = timeScale.timeToCoordinate(lastBarTime)
  if (lastX === null) return
  const futureOffsetX = lastX + 130 // Extend boxes forward into future margin

  // Helper rounded rect
  const drawRoundedRect = (x, y, w, h, radius, fillStyle, strokeStyle, isDashed = false) => {
    if (w <= 0 || h <= 0 || isNaN(x) || isNaN(y)) return
    ctx.save()
    ctx.beginPath()
    ctx.roundRect(x, y, w, h, radius)
    if (fillStyle) {
      ctx.fillStyle = fillStyle
      ctx.fill()
    }
    if (strokeStyle) {
      ctx.strokeStyle = strokeStyle
      ctx.lineWidth = 1.5
      if (isDashed) ctx.setLineDash([5, 4])
      else ctx.setLineDash([])
      ctx.stroke()
    }
    ctx.restore()
  }

  // Helper draw pill label
  const drawPillBadge = (x, y, text, bgColor, textColor = '#ffffff') => {
    ctx.save()
    ctx.font = 'bold 10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    const paddingX = 7
    const paddingY = 3
    const metrics = ctx.measureText(text)
    const badgeW = metrics.width + paddingX * 2
    const badgeH = 18
    const badgeX = x
    const badgeY = y - badgeH / 2

    // Shadow
    ctx.shadowColor = 'rgba(0,0,0,0.4)'
    ctx.shadowBlur = 6
    ctx.beginPath()
    ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 4)
    ctx.fillStyle = bgColor
    ctx.fill()

    ctx.shadowBlur = 0
    ctx.fillStyle = textColor
    ctx.textBaseline = 'middle'
    ctx.fillText(text, badgeX + paddingX, y)
    ctx.restore()
  }

  // 1. DRAW FVG SHADED RECTANGLES (Fair Value Gaps)
  if (showFVG.value && calculatedOverlayData.fvgBands) {
    const recentFVGs = calculatedOverlayData.fvgBands.slice(-10)
    recentFVGs.forEach(fvg => {
      const x1 = timeScale.timeToCoordinate(fvg.startTime)
      const x2 = timeScale.timeToCoordinate(fvg.endTime)
      const y1 = candleSeries.priceToCoordinate(fvg.top)
      const y2 = candleSeries.priceToCoordinate(fvg.bottom)

      if (x1 !== null && y1 !== null && y2 !== null) {
        const boxX = x1
        const boxW = Math.max(30, (x2 !== null ? x2 - x1 : 40) + 40)
        const boxY = Math.min(y1, y2)
        const boxH = Math.abs(y2 - y1)

        if (fvg.type === 'BULL_FVG') {
          drawRoundedRect(boxX, boxY, boxW, boxH, 3, 'rgba(16, 185, 129, 0.14)', 'rgba(16, 185, 129, 0.45)', true)
        } else {
          drawRoundedRect(boxX, boxY, boxW, boxH, 3, 'rgba(239, 68, 68, 0.14)', 'rgba(239, 68, 68, 0.45)', true)
        }
      }
    })
  }

  // 2. DRAW VCP BOX 21 & BOX 9 SHADED RECTANGLES
  if (showVCP.value && calculatedOverlayData.vcp) {
    const vcp = calculatedOverlayData.vcp
    const x21 = timeScale.timeToCoordinate(vcp.startTime21)
    const x9 = timeScale.timeToCoordinate(vcp.startTime9)
    const y21Top = candleSeries.priceToCoordinate(vcp.h21)
    const y21Bot = candleSeries.priceToCoordinate(vcp.l21)
    const y9Top = candleSeries.priceToCoordinate(vcp.h9)
    const y9Bot = candleSeries.priceToCoordinate(vcp.l9)

    // Box 21 (Base box - translucent navy)
    if (x21 !== null && y21Top !== null && y21Bot !== null) {
      const b21W = futureOffsetX - x21
      const b21H = Math.abs(y21Bot - y21Top)
      const b21Y = Math.min(y21Top, y21Bot)
      drawRoundedRect(x21, b21Y, b21W, b21H, 4, 'rgba(99, 102, 241, 0.10)', 'rgba(99, 102, 241, 0.45)', true)
      drawPillBadge(x21 + 4, b21Y + 10, 'Box 21', 'rgba(99, 102, 241, 0.75)')
    }

    // Box 9 (Contraction box - translucent cyan)
    if (x9 !== null && y9Top !== null && y9Bot !== null) {
      const b9W = futureOffsetX - x9
      const b9H = Math.abs(y9Bot - y9Top)
      const b9Y = Math.min(y9Top, y9Bot)
      const isVCP = vcp.isVCP

      drawRoundedRect(
        x9,
        b9Y,
        b9W,
        b9H,
        4,
        isVCP ? 'rgba(0, 242, 254, 0.18)' : 'rgba(20, 184, 166, 0.12)',
        isVCP ? '#00f2fe' : 'rgba(20, 184, 166, 0.5)',
        false
      )

      // Draw Midline dashed
      const midY = (y9Top + y9Bot) / 2
      ctx.save()
      ctx.beginPath()
      ctx.strokeStyle = isVCP ? 'rgba(0, 242, 254, 0.4)' : 'rgba(20, 184, 166, 0.3)'
      ctx.setLineDash([4, 4])
      ctx.moveTo(x9, midY)
      ctx.lineTo(futureOffsetX, midY)
      ctx.stroke()
      ctx.restore()

      // VCP Nén Badge Callout (like in Figure 2)
      if (isVCP) {
        drawPillBadge(x9 + (b9W / 2) - 30, b9Y - 10, `⚡ VCP Nén (${(vcp.ratio * 100).toFixed(0)}%)`, '#00bcd4')
      } else {
        drawPillBadge(x9 + 4, b9Y + 10, 'Box 9', 'rgba(20, 184, 166, 0.75)')
      }
    }
  }
}

// -------------------------------------------------------------
// INIT & RENDER CHART
// -------------------------------------------------------------
const initChart = () => {
  if (!chartDivRef.value) return

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
      vertLines: { color: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.04)' },
      horzLines: { color: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.04)' }
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

  // Candlestick series
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

  // Subscribe view changes to redraw canvas boxes in real-time
  chart.timeScale().subscribeVisibleLogicalRangeChange(() => {
    requestAnimationFrame(drawBoxesOverlay)
  })
  chart.timeScale().subscribeVisibleTimeRangeChange(() => {
    requestAnimationFrame(drawBoxesOverlay)
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

  // Resize observer to keep overlay canvas in perfect sync
  if (resizeObserver) resizeObserver.disconnect()
  resizeObserver = new ResizeObserver(() => {
    requestAnimationFrame(drawBoxesOverlay)
  })
  resizeObserver.observe(chartDivRef.value)
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

    // 2. Try Binance USD-M Futures
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
        console.warn('Binance futures failed:', e.message)
      }
    }

    // 3. Try Yahoo Finance
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

    rawBars = candleData

    // Populate data to series
    candleSeries.setData(candleData)
    volumeSeries.setData(volData)

    // Compute indicator features
    const calc = computeHaoNguyenV14(candleData)
    calculatedOverlayData = calc

    ema9Series.setData(calc.ema9Data)
    ema21Series.setData(calc.ema21Data)

    // Set markers on candles (FVG & Order Blocks)
    const validMarkers = calc.markers.sort((a, b) => a.time - b.time)
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
    vcpInfo.value = calc.vcp

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

    // Hiển thị nến ở khoảng 2/3 khung hình, để trống 1/3 bên phải
    const totalBars = candleData.length
    const visibleCount = Math.min(100, totalBars)
    chart.timeScale().setVisibleLogicalRange({
      from: totalBars - visibleCount,
      to: totalBars + 35
    })

    // Draw canvas overlay
    setTimeout(drawBoxesOverlay, 80)

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
          drawBoxesOverlay()
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

const toggleVCP = () => {
  showVCP.value = !showVCP.value
  drawBoxesOverlay()
}

const toggleEMA = () => {
  showEMA.value = !showEMA.value
  if (ema9Series) ema9Series.applyOptions({ visible: showEMA.value })
  if (ema21Series) ema21Series.applyOptions({ visible: showEMA.value })
}

const toggleFVG = () => {
  showFVG.value = !showFVG.value
  drawBoxesOverlay()
}

const toggleOB = () => {
  showOB.value = !showOB.value
  fetchData()
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
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
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
.hn-dot--vcp { background: #00f2fe; box-shadow: 0 0 6px #00f2fe; }
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
.badge--vcp-active {
  background: rgba(0, 242, 254, 0.25);
  color: #00f2fe;
  border: 1px solid #00f2fe;
  box-shadow: 0 0 8px rgba(0, 242, 254, 0.35);
  animation: pulse-vcp 1.8s infinite;
}
.badge--vcp-normal {
  background: rgba(100, 116, 139, 0.15);
  color: #94a3b8;
  border: 1px solid rgba(100, 116, 139, 0.3);
}

@keyframes pulse-vcp {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.85; transform: scale(1.03); }
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

/* Overlay Canvas for Shaded Rectangles */
.hn-overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 5;
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
.legend-vcp { color: #00f2fe; font-weight: 700; }

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
