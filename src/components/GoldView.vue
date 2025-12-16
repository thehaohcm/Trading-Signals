<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />

    <div class="container mt-4 flex-grow-1">
      <TradingViewChart :coin="'OANDA:XAUUSD'" />

      <!-- Gold Price in Vietnam Table -->
      <div class="card mt-4 mb-4">
        <div class="card-header bg-warning text-dark">
          <h5 class="mb-0">
            <i class="bi bi-coin"></i> Gold Price in Vietnam
            <span v-if="latestDate" class="float-end small">
              Last Updated: {{ latestDate }}
            </span>
          </h5>
        </div>
        <div class="card-body">
          <div v-if="loading" class="text-center py-4">
            <div class="spinner-border text-warning" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>

          <div v-else-if="error" class="alert alert-danger">
            <i class="bi bi-exclamation-triangle"></i> {{ error }}
          </div>

          <div v-else-if="goldPrices && goldPrices.length > 0" class="table-responsive">
            <table class="table table-hover table-striped">
              <thead class="table-warning">
                <tr>
                  <th>Type</th>
                  <th>Branch</th>
                  <th class="text-end">Buy Price</th>
                  <th class="text-end">Sell Price</th>
                  <th class="text-end">Spread</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in goldPrices" :key="item.Id">
                  <td>
                    <strong>{{ item.TypeName }}</strong>
                  </td>
                  <td>
                    <span class="badge bg-secondary">{{ item.BranchName }}</span>
                  </td>
                  <td class="text-end text-success">
                    <strong>{{ item.Buy }}</strong>
                  </td>
                  <td class="text-end text-danger">
                    <strong>{{ item.Sell }}</strong>
                  </td>
                  <td class="text-end">
                    <span class="badge bg-info">
                      {{ calculateSpread(item.BuyValue, item.SellValue) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-else class="alert alert-info">
            <i class="bi bi-info-circle"></i> No gold price data available.
          </div>
        </div>
      </div>
    </div>
  </div>
  <AppFooter />
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import TradingViewChart from './TradingViewChart.vue'

export default {
  components: {
    NavBar,
    AppFooter,
    TradingViewChart,
  },
  props: {
  },
  data() {
    return {
      goldPrices: [],
      latestDate: null,
      loading: false,
      error: null,
    };
  },
  mounted() {
    this.fetchGoldPrices();
    // Refresh every 5 minutes
    this.refreshInterval = setInterval(() => {
      this.fetchGoldPrices();
    }, 5 * 60 * 1000);
  },
  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  },
  methods: {
    async fetchGoldPrices() {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch('/goldprice/services/priceservice.ashx');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
          this.goldPrices = result.data;
          this.latestDate = result.latestDate;
        } else {
          this.error = 'Failed to fetch gold prices';
        }
      } catch (err) {
        console.error('Error fetching gold prices:', err);
        this.error = 'Unable to load gold prices. Please try again later.';
      } finally {
        this.loading = false;
      }
    },
    calculateSpread(buyValue, sellValue) {
      const spread = sellValue - buyValue;
      return new Intl.NumberFormat('vi-VN').format(spread);
    },
  },
};
</script>

<style scoped>
.table-light {
  background-color: #edf2f7;
  text-align: left;
}

.card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  font-weight: 600;
}

.table {
  margin-bottom: 0;
}

.table tbody tr:hover {
  background-color: #fff3cd;
}

.badge {
  font-size: 0.85rem;
  padding: 0.35em 0.65em;
}

.text-success {
  font-weight: 600;
}

.text-danger {
  font-weight: 600;
}

@media (max-width: 768px) {
  .float-end {
    float: none !important;
    display: block;
    margin-top: 0.5rem;
  }
}
</style>