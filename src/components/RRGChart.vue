<template>
  <div class="p-4">
    <div class="d-flex mb-3">
      <input
        v-model="newCoin"
        @keyup.enter="addCoin"
        type="text"
        placeholder="Nhập mã coin, ví dụ: ADAUSDT"
        class="form-control w-auto me-2"
      />
      <button class="btn btn-primary" @click="addCoin">Thêm coin</button>
    </div>

    <div class="chart-container" style="height: 500px;">
      <canvas ref="rrgCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { ref, onMounted, watch } from 'vue'
import { Chart, ScatterController, PointElement, LinearScale, Title, Tooltip, Legend } from 'chart.js'

Chart.register(ScatterController, PointElement, LinearScale, Title, Tooltip, Legend)

const props = defineProps({
  activeRRGInterval: String
})

const coins = ref([
  { symbol: 'BTCUSDT', rs: 102, momentum: 98 },
  { symbol: 'ETHUSDT', rs: 96, momentum: 104 },
  { symbol: 'BNBUSDT', rs: 105, momentum: 90 },
  { symbol: 'XRPUSDT', rs: 92, momentum: 95 },
])

const newCoin = ref('')
const chartInstance = ref(null)
const rrgCanvas = ref(null)

// Thêm coin mới
const addCoin = () => {
  const coin = newCoin.value.trim().toUpperCase()
  if (!coin || coins.value.some(c => c.symbol === coin)) return
  coins.value.push({
    symbol: coin,
    rs: 90 + Math.random() * 20,
    momentum: 90 + Math.random() * 20
  })
  newCoin.value = ''
  renderChart()
}

// Plugin vẽ 4 vùng nền
const quadrantBackground = {
  id: 'quadrantBackground',
  beforeDraw(chart) {
    const { ctx, chartArea, scales } = chart
    const midX = scales.x.getPixelForValue(100)
    const midY = scales.y.getPixelForValue(100)

    const quadrants = [
      { color: 'rgba(135,206,250,0.3)', label: 'IMPROVING', x0: chartArea.left, y0: chartArea.top, x1: midX, y1: midY, textColor: 'blue' },
      { color: 'rgba(144,238,144,0.3)', label: 'LEADING', x0: midX, y0: chartArea.top, x1: chartArea.right, y1: midY, textColor: 'green' },
      { color: 'rgba(255,182,193,0.3)', label: 'LAGGING', x0: chartArea.left, y0: midY, x1: midX, y1: chartArea.bottom, textColor: 'darkred' },
      { color: 'rgba(255,255,224,0.5)', label: 'WEAKENING', x0: midX, y0: midY, x1: chartArea.right, y1: chartArea.bottom, textColor: 'orange' },
    ]

    quadrants.forEach(q => {
      ctx.fillStyle = q.color
      ctx.fillRect(q.x0, q.y0, q.x1 - q.x0, q.y1 - q.y0)
      ctx.fillStyle = q.textColor
      ctx.font = 'bold 14px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(q.label, (q.x0 + q.x1) / 2, (q.y0 + q.y1) / 2)
    })
  }
}

const renderChart = () => {
  if (chartInstance.value) chartInstance.value.destroy()

  chartInstance.value = new Chart(rrgCanvas.value, {
    type: 'scatter',
    data: {
      datasets: coins.value.map((coin, idx) => ({
        label: coin.symbol,
        data: [{ x: coin.rs, y: coin.momentum }],
        borderColor: ['#f39c12', '#2ecc71', '#3498db', '#e74c3c'][idx % 4],
        backgroundColor: ['#f39c12', '#2ecc71', '#3498db', '#e74c3c'][idx % 4],
        pointRadius: 6,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right' },
        title: {
          display: true,
          text: `RRG Chart – ${props.activeRRGInterval || 'Interval'}`,
        },
        tooltip: {
          callbacks: {
            label: context =>
              `${context.dataset.label}: RS ${context.parsed.x.toFixed(2)}, M ${context.parsed.y.toFixed(2)}`,
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: 'Relative Strength (RS-Ratio)' },
          min: 85, max: 115,
          grid: { color: '#ddd' },
        },
        y: {
          title: { display: true, text: 'Momentum (RS-Momentum)' },
          min: 85, max: 115,
          grid: { color: '#ddd' },
        },
      },
    },
    plugins: [quadrantBackground],
  })
}

onMounted(renderChart)
watch(() => props.activeRRGInterval, renderChart)
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
}
</style>
