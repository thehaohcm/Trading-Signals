<template>
  <div class="d-flex flex-column min-vh-100">
    <NavBar />
    <div class="container mt-4 flex-grow-1">
      <h2 class="mb-4">Real Estate Market Prices</h2>
      
      <!-- Filters -->
      <div class="row mb-3">
        <div class="col-md-3">
          <label class="form-label">Region</label>
          <select v-model="selectedRegion" class="form-select" @change="fetchData">
            <option value="">All Regions</option>
            <option v-for="r in regions" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>
        <div class="col-md-3">
          <label class="form-label">Property Type</label>
          <select v-model="selectedType" class="form-select" @change="fetchData">
            <option value="">All Types</option>
            <option v-for="t in types" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
        <div class="col-md-3">
          <label class="form-label">Location</label>
          <input v-model="filterLocation" class="form-control" placeholder="Search location..." @keyup.enter="fetchData" />
        </div>
        <div class="col-md-3 d-flex align-items-end">
             <button class="btn btn-primary w-100" @click="fetchData">Refresh</button>
        </div>
      </div>

      <!-- Chart Section -->
      <div class="card mb-4">
        <div class="card-header bg-secondary text-white">Price History (Average)</div>
        <div class="card-body" style="height: 400px; position: relative;">
          <Line v-if="loaded" :data="chartData" :options="chartOptions" />
          <div v-else class="text-center p-5">Loading Chart...</div>
        </div>
      </div>

      <!-- Listings Table -->
      <div class="card">
        <div class="card-header bg-light">Recent Listings</div>
        <div class="card-body p-0 table-responsive">
          <table class="table table-striped mb-0">
            <thead>
              <tr>
                <th>Date</th>
                <th>Region</th>
                <th>Type</th>
                <th>Location</th>
                <th>Title</th>
                <th>Price</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id">
                <td>{{ formatDate(item.fetched_at) }}</td>
                <td>{{ item.region }}</td>
                <td>{{ item.property_type }}</td>
                <td>{{ item.location }}</td>
                <td>
                    <a :href="item.url" target="_blank" class="text-decoration-none">
                        {{ truncate(item.title, 40) }}
                    </a>
                </td>
                <td class="fw-bold">{{ item.price_text }}</td>
              </tr>
              <tr v-if="items.length === 0">
                <td colspan="6" class="text-center p-3">No data found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line } from 'vue-chartjs';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default {
  name: 'RealEstateView',
  components: {
    NavBar,
    AppFooter,
    Line
  },
  setup() {
    const items = ref([]);
    const loaded = ref(false);
    const selectedRegion = ref('');
    const selectedType = ref('');
    const filterLocation = ref('');
    
    // Hardcoded for now based on scraper script
    const regions = ["Hồ Chí Minh", "Bình Dương", "Bà Rịa - Vũng Tàu", "Đồng Nai"];
    const types = ["House", "Land", "Apartment"];

    const fetchData = async () => {
      loaded.value = false;
      try {
        const params = {};
        if (selectedRegion.value) params.region = selectedRegion.value;
        if (selectedType.value) params.type = selectedType.value;
        if (filterLocation.value) params.location = filterLocation.value;
        
        // Ensure endpoint handles CORS or proxy setup in vue.config.js
        const response = await axios.get('/getRealEstate', { params });
        items.value = response.data || [];
      } catch (e) {
        console.error("Error loading real estate data", e);
      } finally {
        loaded.value = true;
      }
    };

    const chartData = computed(() => {
        // Group by Date and Region to compute average
        const grouped = {};
        items.value.forEach(item => {
            const date = new Date(item.fetched_at).toLocaleDateString();
            if (!grouped[date]) grouped[date] = [];
            if (item.price_numeric > 0) grouped[date].push(item.price_numeric);
        });

        const labels = Object.keys(grouped).sort();
        const dataPoints = labels.map(date => {
            const prices = grouped[date];
            const sum = prices.reduce((a, b) => a + b, 0);
            return prices.length ? sum / prices.length : 0;
        });

        return {
            labels: labels,
            datasets: [
                {
                    label: 'Average Price (VND)',
                    backgroundColor: '#42A5F5',
                    borderColor: '#42A5F5',
                    data: dataPoints,
                    fill: false,
                    tension: 0.1
                }
            ]
        };
    });

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
          x: {
              title: { display: true, text: 'Date' }
          },
          y: {
              title: { display: true, text: 'Price (VND)' },
              ticks: {
                  callback: function(value) {
                      return value.toLocaleString() + ' đ';
                  }
              }
          }
      },
      plugins: {
          tooltip: {
              callbacks: {
                  label: function(context) {
                      return context.raw.toLocaleString() + ' đ';
                  }
              }
          }
      }
    };

    const formatDate = (str) => {
        if(!str) return '';
        return new Date(str).toLocaleString();
    };

    const truncate = (str, len) => {
        if (!str) return '';
        return str.length > len ? str.substring(0, len) + "..." : str;
    };

    onMounted(() => {
        fetchData();
    });

    return {
        items,
        loaded,
        selectedRegion,
        selectedType,
        filterLocation,
        regions,
        types,
        fetchData,
        chartData,
        chartOptions,
        formatDate,
        truncate
    };
  }
};
</script>

<style scoped>
.table-responsive {
    max-height: 600px;
}
</style>
