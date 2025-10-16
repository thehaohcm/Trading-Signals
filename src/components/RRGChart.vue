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

Chart.register(ScatterController, PointElement, LinearScale, Title, Tooltip, Legend)

const props = defineProps({
  interval: { type: String, default: '1d' }
})

const coins = ref([])
const loading = ref(false)
const error = ref(null)
const rrgCanvas = ref(null)
let chartInstance = null

const INTERVAL_MAP = {
  '1d': { days: 1, interval: 'daily' },
  '1w': { days: 7, interval: 'weekly' },
  '1month': { days: 30, interval: 'monthly' }
}

function colorFromName(name) {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  const hue = Math.abs(hash % 360)
  return `hsl(${hue},70%,45%)`
}

async function fetchTopCoins() {
  const res = await axios.get('https://api.coingecko.com/api/v3/coins/markets', {
    params: { vs_currency: 'usd', order: 'market_cap_desc', per_page: 10, page: 1 }
  })
  return res.data
}

async function fetchCoinHistory(id, intervalKey) {
  const map = INTERVAL_MAP[intervalKey] || INTERVAL_MAP['1d']
  try {
    const res = await axios.get(`https://api.coingecko.com/api/v3/coins/${id}/market_chart`, {
      params: { vs_currency: 'usd', days: map.days, interval: map.interval }
    })
    return (res.data.prices || []).map(p => p[1])
  } catch (e) {
    console.warn('fetchCoinHistory error', id, e && e.message)
    return []
  }
}

async function loadData() {
  loading.value = true
  error.value = null
  coins.value = []

  try {
    const top = await fetchTopCoins()
    const btcHistory = await fetchCoinHistory('bitcoin', props.interval)
    if (!btcHistory.length) throw new Error('Không lấy được dữ liệu BTC')

    const btcNow = btcHistory.at(-1)
    const btcPrev = btcHistory[0]
    const denom = btcPrev === 0 ? 0 : (btcNow - btcPrev) / btcPrev

    const results = await Promise.all(top.map(async coin => {
      const hist = await fetchCoinHistory(coin.id, props.interval)
      if (hist.length < 2) return null
      const now = hist.at(-1)
      const prev = hist[0]
      const momentum = prev === 0 ? 0 : ((now - prev) / prev) * 100
      const strength = denom === 0 ? 1 : ((now / prev - 1) / denom)
      return {
        id: coin.id,
        symbol: (coin.symbol || coin.id).toUpperCase(),
        strength,
        momentum
      }
    }))

    coins.value = results.filter(Boolean)
    renderChart()
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Lỗi tải dữ liệu'
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (chartInstance) chartInstance.destroy()
  if (!rrgCanvas.value) return

  const items = coins.value.map(c => ({
    label: c.symbol,
    x: 100 * c.strength,
    y: 100 + c.momentum,
    color: colorFromName(c.symbol)
  }))

  // dynamic bounds
  const xs = items.map(i => i.x)
  const ys = items.map(i => i.y)
  const minX = Math.min(...xs, 80)
  const maxX = Math.max(...xs, 120)
  const minY = Math.min(...ys, 80)
  const maxY = Math.max(...ys, 120)
  const midX = 100
  const midY = 100

  chartInstance = new Chart(rrgCanvas.value, {
    type: 'scatter',
    data: {
      datasets: items.map(it => ({
        label: it.label,
        data: [{ x: it.x, y: it.y }],
        backgroundColor: it.color,
        borderColor: it.color,
        pointRadius: 6
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { usePointStyle: true } },
        tooltip: {
          callbacks: {
            label: ctx => {
              const d = ctx.parsed
              return `${ctx.dataset.label}: RS ${d.x.toFixed(1)}, M ${d.y.toFixed(1)}`
            }
          }
        }
      },
      scales: {
        x: { title: { display: true, text: 'Relative Strength (center=100)' }, min: minX - 5, max: maxX + 5 },
        y: { title: { display: true, text: 'Momentum (center=100)' }, min: minY - 5, max: maxY + 5 }
      },
      animation: false
    },
    plugins: [
      {
        id: 'rrgQuadrants',
        beforeDraw(chart) {
          const { ctx, chartArea, scales } = chart
          const { left, right, top, bottom } = chartArea
          const midXpx = scales.x.getPixelForValue(midX)
          const midYpx = scales.y.getPixelForValue(midY)

          ctx.save()
          // Quadrants
          ctx.fillStyle = 'rgba(135,206,250,0.12)'
          ctx.fillRect(left, top, midXpx - left, midYpx - top)
          ctx.fillStyle = 'rgba(144,238,144,0.12)'
          ctx.fillRect(midXpx, top, right - midXpx, midYpx - top)
          ctx.fillStyle = 'rgba(255,182,193,0.12)'
          ctx.fillRect(left, midYpx, midXpx - left, bottom - midYpx)
          ctx.fillStyle = 'rgba(255,218,185,0.12)'
          ctx.fillRect(midXpx, midYpx, right - midXpx, bottom - midYpx)

          const labels = [
            { text: 'IMPROVING', x: left + (midXpx - left) / 2, y: top + (midYpx - top) / 2, color: '#0b63b6' },
            { text: 'LEADING', x: midXpx + (right - midXpx) / 2, y: top + (midYpx - top) / 2, color: '#116611' },
            { text: 'LAGGING', x: left + (midXpx - left) / 2, y: midYpx + (bottom - midYpx) / 2, color: '#8b0000' },
            { text: 'WEAKENING', x: midXpx + (right - midXpx) / 2, y: midYpx + (bottom - midYpx) / 2, color: '#b35900' }
          ]

          ctx.font = 'bold 14px sans-serif'
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          labels.forEach(l => {
            const padding = 6
            const metrics = ctx.measureText(l.text)
            const w = metrics.width + padding * 2
            ctx.fillStyle = 'rgba(255,255,255,0.85)'
            ctx.fillRect(l.x - w / 2, l.y - 10, w, 20)
            ctx.fillStyle = l.color
            ctx.fillText(l.text, l.x, l.y)
          })

          ctx.strokeStyle = '#aaa'
          ctx.beginPath()
          ctx.moveTo(midXpx, top)
          ctx.lineTo(midXpx, bottom)
          ctx.moveTo(left, midYpx)
          ctx.lineTo(right, midYpx)
          ctx.stroke()
          ctx.restore()
        }
      }
    ]
  })
}

onMounted(loadData)
watch(() => props.interval, loadData)
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 520px;
}
</style>
