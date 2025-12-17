<template>
  <div class="p-3">
    <div class="d-flex justify-content-between align-items-center mb-2">
      <div>
        <strong>RRG Chart ({{ customCoins.length > 0 ? 'Custom' : 'All Coins' }}) — Interval: {{ interval }}</strong>
        <small class="text-muted ms-2" v-if="coins.length > 0">({{ coins.length }} coins)</small>
      </div>
      <div>
        <small v-if="loading" class="text-muted">Loading data...</small>
        <small v-else-if="error" class="text-danger">{{ error }}</small>
      </div>
    </div>

    <!-- Custom coin input section -->
    <div class="mb-3">
      <div class="input-group">
        <input 
          type="text" 
          class="form-control" 
          v-model="customCoinInput"
          @keydown.enter="addCustomCoin"
          placeholder="Nhập mã coin (VD: BTC, ETH, SOL...) và nhấn Enter"
          :disabled="loading"
        />
        <button 
          class="btn btn-primary" 
          @click="addCustomCoin"
          :disabled="loading || !customCoinInput.trim()"
        >
          Thêm
        </button>
        <button 
          v-if="customCoins.length > 0"
          class="btn btn-secondary" 
          @click="resetToTopCoins"
          :disabled="loading"
        >
          Reset All Coins
        </button>
      </div>
      <div v-if="customCoins.length > 0" class="mt-2">
        <small class="text-muted">Custom coins: </small>
        <span 
          v-for="(coin, index) in customCoins" 
          :key="coin"
          class="badge bg-info text-dark me-1"
          style="cursor: pointer;"
          @click="removeCustomCoin(index)"
          :title="`Click để xóa ${coin}`"
        >
          {{ coin }} ×
        </span>
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
            <td :class="c.strength > 100 ? 'text-success' : 'text-danger'">{{ c.strength.toFixed(2) }}</td>
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
const customCoinInput = ref('')
const customCoins = ref([])
let chartInstance = null

const INTERVAL_MAP = {
  '1d': { days: 1, interval: 'daily' },
  '1w': { days: 7, interval: 'weekly' },
  '1month': { days: 30, interval: 'monthly' }
}

function colorFromName(name) {
  const presetColors = {
    BTC: '#f39c12', // vàng cam
    ETH: '#2ecc71', // xanh lá
    SOL: '#3498db', // xanh dương
    DOGE: '#e74c3c', // đỏ
    XRP: '#9b59b6', // tím
    BNB: '#16a085', // xanh ngọc
    ADA: '#1abc9c', // xanh teal
    AVAX: '#e67e22', // cam đậm
    TRX: '#c0392b', // đỏ tươi
    TON: '#2980b9'  // xanh navy
  }

  const upper = name.toUpperCase()
  if (presetColors[upper]) return presetColors[upper]

  // fallback: random nhưng khác biệt
  let hash = 0
  for (let i = 0; i < upper.length; i++)
    hash = upper.charCodeAt(i) + ((hash << 5) - hash)
  const hue = Math.abs(hash % 360)
  return `hsl(${hue},70%,45%)`
}


// Mapping common symbols to CoinGecko IDs
const COIN_ID_MAP = {
  'BTC': 'bitcoin',
  'ETH': 'ethereum',
  'BNB': 'binancecoin',
  'SOL': 'solana',
  'XRP': 'ripple',
  'ADA': 'cardano',
  'DOGE': 'dogecoin',
  'AVAX': 'avalanche-2',
  'DOT': 'polkadot',
  'MATIC': 'matic-network',
  'TRX': 'tron',
  'TON': 'the-open-network',
  'LINK': 'chainlink',
  'UNI': 'uniswap',
  'ATOM': 'cosmos',
  'LTC': 'litecoin',
  'BCH': 'bitcoin-cash',
  'XLM': 'stellar',
  'ALGO': 'algorand',
  'VET': 'vechain'
}

async function fetchTopCoins() {
  const res = await axios.get('https://api.coingecko.com/api/v3/coins/markets', {
    params: { vs_currency: 'usd', order: 'market_cap_desc', per_page: 10, page: 1 }
  })
  return res.data
}

async function searchCoinId(symbol) {
  const upperSymbol = symbol.toUpperCase()
  
  // Check predefined map first
  if (COIN_ID_MAP[upperSymbol]) {
    return COIN_ID_MAP[upperSymbol]
  }
  
  // Search via API
  try {
    const res = await axios.get('https://api.coingecko.com/api/v3/search', {
      params: { query: symbol }
    })
    
    if (res.data.coins && res.data.coins.length > 0) {
      // Try to find exact match first
      const exactMatch = res.data.coins.find(c => 
        c.symbol.toUpperCase() === upperSymbol
      )
      return exactMatch ? exactMatch.id : res.data.coins[0].id
    }
  } catch (e) {
    console.warn('searchCoinId error', symbol, e && e.message)
  }
  
  return null
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
    let coinsToFetch = []
    
    // Use custom coins if provided, otherwise use all coins from COIN_ID_MAP
    if (customCoins.value.length > 0) {
      // Convert custom coin symbols to CoinGecko IDs
      const coinPromises = customCoins.value.map(async symbol => {
        const coinId = await searchCoinId(symbol)
        if (!coinId) {
          console.warn(`Không tìm thấy coin: ${symbol}`)
          return null
        }
        return { id: coinId, symbol: symbol.toUpperCase() }
      })
      
      const resolvedCoins = await Promise.all(coinPromises)
      coinsToFetch = resolvedCoins.filter(Boolean)
      
      if (coinsToFetch.length === 0) {
        throw new Error('Không tìm thấy coin nào trong danh sách')
      }
    } else {
      // Use all coins from COIN_ID_MAP by default
      coinsToFetch = Object.entries(COIN_ID_MAP).map(([symbol, id]) => ({
        id: id,
        symbol: symbol
      }))
      console.log(`Loading default ${coinsToFetch.length} coins from COIN_ID_MAP`)
    }

    // Fetch BTC as benchmark
    const btcHistory = await fetchCoinHistory('bitcoin', props.interval)
    if (!btcHistory.length) throw new Error('Không lấy được dữ liệu BTC')

    const btcNow = btcHistory.at(-1)
    const btcPrev = btcHistory[0]
    const btcReturn = btcPrev === 0 ? 0 : (btcNow - btcPrev) / btcPrev

    const results = await Promise.all(coinsToFetch.map(async coin => {
      const hist = await fetchCoinHistory(coin.id, props.interval)
      if (hist.length < 2) {
        console.warn(`Not enough data for ${coin.symbol}`)
        return null
      }
      
      const now = hist.at(-1)
      const prev = hist[0]
      
      // Validate prices
      if (!now || !prev || now <= 0 || prev <= 0) {
        console.warn(`Invalid price data for ${coin.symbol}`, { now, prev })
        return null
      }
      
      // Calculate momentum as percentage change
      const momentum = ((now - prev) / prev) * 100
      
      // Calculate relative strength vs BTC
      // RS = (coin return / BTC return) * 100
      const coinReturn = (now - prev) / prev
      let strength = 100 // Default neutral
      
      if (Math.abs(btcReturn) > 0.0001) { // Avoid division by very small numbers
        strength = (coinReturn / btcReturn) * 100
        // Clamp extreme values to keep chart readable
        strength = Math.max(-200, Math.min(400, strength))
      } else if (Math.abs(coinReturn) > 0.0001) {
        // If BTC is flat but coin moved, show strong/weak
        strength = coinReturn > 0 ? 150 : 50
      }
      
      console.log(`${coin.symbol}: strength=${strength.toFixed(2)}, momentum=${momentum.toFixed(2)}`)
      
      return {
        id: coin.id,
        symbol: coin.symbol,
        strength,
        momentum
      }
    }))

    coins.value = results.filter(Boolean)
    
    console.log('Loaded coins data:', coins.value) // Debug log
    
    if (coins.value.length === 0) {
      throw new Error('Không có dữ liệu hợp lệ để hiển thị')
    }
    
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
    x: c.strength, // Already in 100-based scale
    y: 100 + c.momentum, // Center at 100
    color: colorFromName(c.symbol)
  }))

  console.log('RRG Chart items:', items) // Debug log

  // Dynamic bounds with padding - ensure we include all points
  const xs = items.map(i => i.x)
  const ys = items.map(i => i.y)
  
  const dataMinX = Math.min(...xs)
  const dataMaxX = Math.max(...xs)
  const dataMinY = Math.min(...ys)
  const dataMaxY = Math.max(...ys)
  
  // Ensure bounds include 100 (center) and all data points
  const minX = Math.min(dataMinX, 80) - 10
  const maxX = Math.max(dataMaxX, 120) + 10
  const minY = Math.min(dataMinY, 80) - 10
  const maxY = Math.max(dataMaxY, 120) + 10
  
  const midX = 100
  const midY = 100

  console.log('Chart bounds:', { minX, maxX, minY, maxY }) // Debug log

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
        x: { title: { display: true, text: 'Relative Strength (center=100)' }, min: minX, max: maxX },
        y: { title: { display: true, text: 'Momentum (center=100)' }, min: minY, max: maxY }
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

function addCustomCoin() {
  const symbol = customCoinInput.value.trim().toUpperCase()
  if (!symbol) return
  
  // Avoid duplicates
  if (customCoins.value.includes(symbol)) {
    error.value = `${symbol} đã có trong danh sách`
    setTimeout(() => error.value = null, 2000)
    return
  }
  
  customCoins.value.push(symbol)
  customCoinInput.value = ''
  loadData()
}

function removeCustomCoin(index) {
  customCoins.value.splice(index, 1)
  loadData()
}

function resetToTopCoins() {
  customCoins.value = []
  customCoinInput.value = ''
  loadData()
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
