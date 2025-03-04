<template>
  <div style="position: relative;">
    <div style="display: flex; justify-content: flex-end; gap: 5px; top: 10px; right: 10px;">
      <button @click="setIntervalTime(365)" class="btn btn-outline-secondary btn-sm">1y</button>
      <button @click="setIntervalTime(180)" class="btn btn-outline-secondary btn-sm">6M</button>
      <button @click="setIntervalTime(90)" class="btn btn-outline-secondary btn-sm">3M</button>
      <button @click="setIntervalTime(30)" class="btn btn-outline-secondary btn-sm">1M</button>
      <button @click="setIntervalTime(7)" class="btn btn-outline-secondary btn-sm">1w</button>
    </div>
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

export default {
  name: 'StockChart',
  props: {
    ticker: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const chartCanvas = ref(null);
    let myChart = null;
    const intervalTime = ref(365);

    const fetchData = async () => {
      if (!props.ticker) {
        return;
      }
      const currentUnixTs = String(Math.floor(Date.now() / 1000));
      
      const url = `/stock-insight/v2/stock/bars-long-term?ticker=${props.ticker}&type=stock&resolution=D&to=${currentUnixTs}&countBack=${intervalTime.value}`;

      try {
        console.log("Fetching URL:", url); // Log the URL
        const res = await fetch(url);
        console.log("Response status:", res.status); // Log the response status
        if (res.ok) {
          const jsonBody = await res.json();
          console.log("API response:", jsonBody);
          const dataList = jsonBody.data;
          console.log("dataList:", dataList);

          if (!dataList || dataList.length === 0) {
            console.error('No data found for', props.ticker);
            return;
          }
          if (myChart) {
            myChart.destroy();
          }
          myChart = new Chart(chartCanvas.value, {
            type: 'line',
            data: {
              labels: dataList.map((_, index) => index + 1),
              datasets: [
                {
                  label: props.ticker,
                  data: dataList.map(data => data.close),
                  borderColor: 'green',
                  backgroundColor: 'rgba(0, 0, 255, 0.1)',
                },
              ],
            },
          });
        } else {
          console.error('Error fetching data:', res.status);
        }
      } catch (e) {
        console.error('exception', e);
      }
    };

     const setIntervalTime = (days) => {
        intervalTime.value = days;
        fetchData();
    }

    watch(() => props.ticker, (newTicker, oldTicker) => {
      if (newTicker !== oldTicker) {
        fetchData();
      }
    });

    onMounted(fetchData);

    return {
      chartCanvas,
      setIntervalTime
    };
  },
};
</script>

<style scoped>
/* Add component-specific styles here if needed */
</style>