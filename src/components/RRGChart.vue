<template>
  <div class="p-3">
    <div class="d-flex justify-content-between align-items-center mb-2">
      <div>
        <strong>RRG Chart (Top 10) — Interval: {{ interval }}</strong>
      </div>
      <div>
        <small v-if="loading" class="text-muted">Loading data...</small>
        <small v-else-if="error" class="text-danger">{{ error }}</small>
      </div>
    </div>

    <div class="chart-container" style="height: 520px; position: relative;">
      <canvas ref="rrgCanvas"></canvas>
    </div>

    <!-- Optional data table -->
    <div class="mt-3">
      <table class="table table-sm table-striped">
        <thead>
          <tr><th>Coin</th><th>Strength</th><th>Momentum (%)</th></tr>
        </thead>
        <tbody>
          <tr v-for="c in coins" :key="c.id">
            <td><b>{{ c.symbol }}</b></td>
            <td :class="c.strength > 1 ? 'text-success' : 'text-danger'">{{ c.strength.toFixed(2) }}</td>
            <td :class="c.momentum > 0 ? 'text-success' : 'text-danger'">{{ c.momentum.toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import {
  Chart,
  ScatterController,
  PointElement,
  LinearScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

// register Chart.js elements we need
Chart.register(ScatterController, PointElement, LinearScale, Title, Tooltip, Legend)

// accept interval prop from parent
const props = defineProps({
  interval: { type: String, default: '1d' } // e.g. '5m','30m','1h','4h','1d','1w','1month'
})

// reactive state
const coins = ref([])         // array of {id, symbol, name, strength, momentum}
const loading = ref(false)
const error = ref(null)

const rrgCanvas = ref(null)
let chartInstance = null

// mapping from interval -> coinGecko params (approx)
const INTERVAL_MAP = {
  '1d': { days: 1, interval: 'daily' },
  '1w': { days: 7, interval: 'weekly' },
  '1month': { days: 30, interval: 'monthly' }
}

// create deterministic color from symbol
function colorFromName(name) {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  const hue = Math.abs(hash % 360)
  return `hsl(${hue}, 70%, 45%)`
}

// fetch top 10 coins by marketcap (CoinGecko public API)
async function fetchTopCoins() {
  const res = await axios.get('https://api.coingecko.com/api/v3/coins/markets', {
    params: { vs_currency: 'usd', order: 'market_cap_desc', per_page: 10, page: 1 }
  })
  return res.data // array
}

// fetch price series (prices array) for a coin id
async function fetchCoinHistory(id, intervalKey) {
  const map = INTERVAL_MAP[intervalKey] || INTERVAL_MAP['1d']
  try {
    // CoinGecko market_chart endpoint
    const res = await axios.get(`https://api.coingecko.com/api/v3/coins/${id}/market_chart`, {
      params: { vs_currency: 'usd', days: map.days, interval: map.interval }
    })
    // res.data.prices is array of [ts, price]
    return (res.data.prices || []).map(p => p[1])
  } catch (e) {
    console.warn('fetchCoinHistory error', id, e && e.message)
    return []
  }
}

// compute strength & momentum for coin list using BTC as benchmark
async function loadData() {
  loading.value = true
  error.value = null
  coins.value = []

  try {
    const top = await fetchTopCoins()
    // fetch BTC history once
    const btcHistory = await fetchCoinHistory('bitcoin', props.interval)
    if (!btcHistory || btcHistory.length < 2) throw new Error('Không lấy được dữ liệu BTC')

    const btcNow = btcHistory[btcHistory.length - 1]
    const btcPrev = btcHistory[0]

    // fetch all coin histories in parallel but limit concurrency to avoid rate-limits
    // simple Promise.all for now
    const promises = top.map(async (coin) => {
      const hist = await fetchCoinHistory(coin.id, props.interval)
      if (!hist || hist.length < 2) return null
      const now = hist[hist.length - 1]
      const prev = hist[0]
      const momentum = prev === 0 ? 0 : ((now - prev) / prev) * 100
      const denom = (btcNow / btcPrev - 1)
      const strength = (denom === 0) ? 0 : ((now / prev - 1) / denom)
      return {
        id: coin.id,
        symbol: (coin.symbol || coin.id).toUpperCase(),
        name: coin.name,
        strength,
        momentum
      }
    })

    const results = await Promise.all(promises)
    coins.value = results.filter(Boolean)
    // after data ready, render chart
    renderChart()
  } catch (err) {
    console.error(err)
    error.value = (err && err.message) || 'Lỗi khi tải dữ liệu'
  } finally {
    loading.value = false
  }
}

// draw RRG chart with quadrants and points
function renderChart() {
  // destroy old chart
  if (chartInstance) {
    try { chartInstance.destroy() } catch (e) { /* ignore */ }
    chartInstance = null
  }
  if (!rrgCanvas.value) return

  // Prepare datasets: points from coins with x=strength? no — we want x = strength ratio or RS? 
  // We will use: x = strengthNormalized * 100 (so that center ~100), y = momentumNormalized + 100 (so center ~100)
  // But earlier we computed 'strength' as ratio; to be consistent with RRG center at 100, we map:
  // RS_value = 100 * strength  (so strength=1 => 100)
  // Momentum_value = 100 + momentumPercent (so momentum 0% => 100)
  const items = coins.value.map(c => {
    const rsVal = 100 * (isFinite(c.strength) ? c.strength : 0)
    const momVal = 100 + (isFinite(c.momentum) ? c.momentum : 0)
    return {
      id: c.id,
      label: c.symbol,
      x: rsVal,
      y: momVal,
      color: colorFromName(c.symbol)
    }
  })

  // Chart middle reference
  const midX = 100
  const midY = 100

  chartInstance = new Chart(rrgCanvas.value, {
    type: 'scatter',
    data: {
      datasets: items.map(it => ({
        label: it.label,
        data: [{ x: it.x, y: it.y }],
        pointRadius: 6,
        backgroundColor: it.color,
        borderColor: it.color
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { usePointStyle: true } },
        title: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const ds = ctx.dataset
              const d = ctx.parsed
              return `${ds.label}: RS ${d.x.toFixed(1)}, M ${d.y.toFixed(1)}`
            }
          }
        }
      },
      scales: {
        x: {
          title: { display: true, text: 'Relative Strength (center=100)' },
          min: 80,
          max: 120,
          grid: { color: '#eee' }
        },
        y: {
          title: { display: true, text: 'Momentum (center=100)' },
          min: 80,
          max: 120,
          grid: { color: '#eee' }
        }
      },
      animation: false
    },
    plugins: [
      {
        id: 'rrgQuadrants',
        beforeDraw(chart) {
          const { ctx, chartArea, scales } = chart
          const left = chartArea.left, right = chartArea.right, top = chartArea.top, bottom = chartArea.bottom
          const midXpx = scales.x.getPixelForValue(midX)
          const midYpx = scales.y.getPixelForValue(midY)

          ctx.save()
          // Improving (top-left)
          ctx.fillStyle = 'rgba(135,206,250,0.12)'
          ctx.fillRect(left, top, midXpx - left, midYpx - top)
          // Leading (top-right)
          ctx.fillStyle = 'rgba(144,238,144,0.12)'
          ctx.fillRect(midXpx, top, right - midXpx, midYpx - top)
          // Lagging (bottom-left)
          ctx.fillStyle = 'rgba(255,182,193,0.12)'
          ctx.fillRect(left, midYpx, midXpx - left, bottom - midYpx)
          // Weakening (bottom-right)
          ctx.fillStyle = 'rgba(255,218,185,0.12)'
          ctx.fillRect(midXpx, midYpx, right - midXpx, bottom - midYpx)

          // Labels - render with small background rectangle for readability
          const labels = [
            { text: 'IMPROVING', x: left + (midXpx - left) * 0.5, y: top + (midYpx - top) * 0.5, color: '#0b63b6' },
            { text: 'LEADING', x: midXpx + (right - midXpx) * 0.5, y: top + (midYpx - top) * 0.5, color: '#116611' },
            { text: 'LAGGING', x: left + (midXpx - left) * 0.5, y: midYpx + (bottom - midYpx) * 0.5, color: '#8b0000' },
            { text: 'WEAKENING', x: midXpx + (right - midXpx) * 0.5, y: midYpx + (bottom - midYpx) * 0.5, color: '#b35900' }
          ]

          ctx.font = 'bold 14px sans-serif'
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          labels.forEach(l => {
            // background pill
            const paddingX = 8, paddingY = 4
            const metrics = ctx.measureText(l.text)
            const w = metrics.width + paddingX * 2
            const h = 18 + paddingY * 2
            ctx.fillStyle = 'rgba(255,255,255,0.85)'
            ctx.fillRect(l.x - w/2, l.y - h/2, w, h)
            ctx.fillStyle = l.color
            ctx.fillText(l.text, l.x, l.y)
          })

          // draw center crosshairs
          ctx.strokeStyle = '#aaa'
          ctx.lineWidth = 1
          ctx.beginPath()
          ctx.moveTo(midXpx, top); ctx.lineTo(midXpx, bottom)
          ctx.moveTo(left, midYpx); ctx.lineTo(right, midYpx)
          ctx.stroke()

          ctx.restore()
        }
      }
    ]
  })
}

// watch interval prop changes
onMounted(loadData)
watch(() => props.interval, loadData)
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 520px;
}
</style>
