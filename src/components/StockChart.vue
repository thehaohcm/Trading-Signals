<template>
  <div>
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

    const fetchData = async () => {
      if (!props.ticker) {
        return;
      }
      const currentUnixTs = String(Math.floor(Date.now() / 1000));
      const url = `/stock-insight/v2/stock/bars-long-term?ticker=${props.ticker}&type=stock&resolution=D&to=${currentUnixTs}&countBack=120`;

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
            type: 'line', // Change to line chart
            data: {
              labels: dataList.map((_, index) => index + 1), // Simple x-axis (1 to 30)
              datasets: [
                {
                  label: `Data (Incorrect Ticker)`, // Generic label
                  data: dataList.map(data => data.close), // Use 'close' values
                  borderColor: 'blue',
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

    watch(() => props.ticker, (newTicker, oldTicker) => {
      if (newTicker !== oldTicker) {
        fetchData();
      }
    });

    onMounted(fetchData);

    return {
      chartCanvas,
    };
  },
};
</script>

<style scoped>
/* Add component-specific styles here if needed */
</style>