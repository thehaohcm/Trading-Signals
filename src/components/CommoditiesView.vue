<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />

    <div class="container mt-4 flex-grow-1">
      <!-- Main Commodities Tabs -->
      <ul class="nav nav-pills nav-fill mb-4 p-2 bg-light rounded shadow-sm" role="tablist">
        <li class="nav-item" role="presentation">
          <button 
            class="nav-link fw-bold" 
            :class="{ active: selectedCommodity === 'gold', 'bg-warning text-dark': selectedCommodity === 'gold' }"
            @click="selectedCommodity = 'gold'"
            type="button"
          >
            <i class="bi bi-stopwatch"></i> Gold
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button 
            class="nav-link fw-bold" 
            :class="{ active: selectedCommodity === 'silver', 'bg-secondary text-white': selectedCommodity === 'silver' }"
            @click="selectedCommodity = 'silver'"
            type="button"
          >
            <i class="bi bi-moon-stars"></i> Silver
          </button>
        </li>
      </ul>

      <!-- Toggle Content based on Commodity -->
      <div v-show="selectedCommodity === 'gold'">
        <!-- Gold Sub-Tabs -->
        <ul class="nav nav-tabs mb-3" role="tablist">
          <li class="nav-item">
            <button class="nav-link" :class="{ active: goldTab === 'world' }" @click="goldTab = 'world'">
              <i class="bi bi-globe"></i> World Gold Price
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" :class="{ active: goldTab === 'vietnam' }" @click="goldTab = 'vietnam'">
              <i class="bi bi-flag"></i> Vietnam Gold Price
            </button>
          </li>
        </ul>

        <!-- Gold Content -->
        <div class="tab-content">
          <div v-show="goldTab === 'world'" class="tab-pane fade show active">
            <TradingViewChart :coin="'OANDA:XAUUSD'" />
            <PriceAlertWidget symbol="XAUUSD" assetType="gold" />
          </div>

          <div v-show="goldTab === 'vietnam'" class="tab-pane fade show active">
            <div class="card shadow-sm">
              <div class="card-header bg-warning text-dark d-flex justify-content-between align-items-center">
                 <h5 class="mb-0"><i class="bi bi-coin"></i> Gold Price in Vietnam</h5>
                 <span v-if="goldValues.latestDate" class="small">Updated: {{ goldValues.latestDate }}</span>
              </div>
              <div class="card-body">
                <div v-if="goldValues.loading" class="text-center py-4">
                  <div class="spinner-border text-warning" role="status"></div>
                </div>
                <div v-else-if="goldValues.error" class="alert alert-danger">
                  {{ goldValues.error }}
                </div>
                <div v-else-if="goldValues.data.length" class="table-responsive">
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
                      <tr v-for="item in goldValues.data" :key="item.Id">
                        <td><strong>{{ item.TypeName }}</strong></td>
                        <td><span class="badge bg-secondary">{{ item.BranchName }}</span></td>
                        <td class="text-end text-success"><strong>{{ item.Buy }}</strong></td>
                        <td class="text-end text-danger"><strong>{{ item.Sell }}</strong></td>
                        <td class="text-end"><span class="badge bg-info">{{ calculateSpread(item.BuyValue, item.SellValue) }}</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="alert alert-info">No data available.</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-show="selectedCommodity === 'silver'">
        <!-- Silver Sub-Tabs -->
        <ul class="nav nav-tabs mb-3" role="tablist">
          <li class="nav-item">
            <button class="nav-link" :class="{ active: silverTab === 'world' }" @click="silverTab = 'world'">
              <i class="bi bi-globe"></i> World Silver Price
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" :class="{ active: silverTab === 'vietnam' }" @click="silverTab = 'vietnam'">
              <i class="bi bi-flag"></i> Vietnam Silver Price
            </button>
          </li>
        </ul>

         <!-- Silver Content -->
         <div class="tab-content">
          <div v-show="silverTab === 'world'" class="tab-pane fade show active">
             <TradingViewChart :coin="'OANDA:XAGUSD'" />
             <PriceAlertWidget symbol="XAGUSD" assetType="silver" />
          </div>

          <div v-show="silverTab === 'vietnam'" class="tab-pane fade show active">
             <div class="card shadow-sm">
               <div class="card-header bg-secondary text-white d-flex justify-content-between align-items-center">
                  <h5 class="mb-0"><i class="bi bi-coin"></i> Silver Price in Vietnam</h5>
                  <span v-if="silverValues.lastUpdated" class="small">Updated: {{ silverValues.lastUpdated }}</span>
               </div>
               <div class="card-body">
                   <div v-if="silverValues.loading" class="text-center py-4">
                     <div class="spinner-border text-secondary" role="status"></div>
                   </div>
                   <div v-else-if="silverValues.error" class="alert alert-danger">{{ silverValues.error }}</div>
                   <div v-else-if="silverValues.htmlContent" v-html="silverValues.htmlContent" class="silver-content"></div>
                   <div v-else class="alert alert-info">No data available.</div>
               </div>
             </div>
          </div>
        </div>
      </div>

    </div>
    <AppFooter />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import TradingViewChart from './TradingViewChart.vue'
import PriceAlertWidget from './PriceAlertWidget.vue';
import { ref, onMounted, watch, onBeforeUnmount } from 'vue';

export default {
  name: 'CommoditiesView',
  components: {
    NavBar,
    AppFooter,
    TradingViewChart,
    PriceAlertWidget,
  },
  setup() {
    const selectedCommodity = ref('gold');
    const goldTab = ref('world');
    const silverTab = ref('world');

    // Gold State
    const goldValues = ref({
        data: [],
        latestDate: null,
        loading: false,
        error: null
    });

    // Silver State
    const silverValues = ref({
        htmlContent: null,
        lastUpdated: null,
        loading: false,
        error: null
    });

    // Fetch Methods
    const fetchGoldPrices = async () => {
      goldValues.value.loading = true;
      goldValues.value.error = null;
      try {
        const response = await fetch('/goldprice/services/priceservice.ashx');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const result = await response.json();
        if (result.success) {
            goldValues.value.data = result.data;
            goldValues.value.latestDate = result.latestDate;
        } else {
            goldValues.value.error = 'Failed to fetch gold prices';
        }
      } catch (err) {
          console.error(err);
          goldValues.value.error = 'Unable to load gold prices.';
      } finally {
          goldValues.value.loading = false;
      }
    };

    const fetchSilverPrices = async () => {
      silverValues.value.loading = true;
      silverValues.value.error = null;
      try {
        const response = await fetch('/silverprice/silverpricePartial', {
          headers: { 'Accept': 'text/html, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        silverValues.value.htmlContent = await response.text();
        silverValues.value.lastUpdated = new Date().toLocaleString('vi-VN');
      } catch (err) {
          console.error(err);
          silverValues.value.error = 'Unable to load silver prices.';
      } finally {
          silverValues.value.loading = false;
      }
    };

    // Helpers
    const calculateSpread = (buy, sell) => {
       return new Intl.NumberFormat('vi-VN').format(sell - buy);
    };

    let intervalId = null;

    onMounted(() => {
        // Initial fetch if needed, though we only fetch when tab is active to save resources?
        // Or fetch both aggressively. Let's fetch on demand or init.
        fetchGoldPrices();
        fetchSilverPrices();

        intervalId = setInterval(() => {
            if (selectedCommodity.value === 'gold' && goldTab.value === 'vietnam') fetchGoldPrices();
            if (selectedCommodity.value === 'silver' && silverTab.value === 'vietnam') fetchSilverPrices();
        }, 5 * 60 * 1000);
    });

    onBeforeUnmount(() => {
        if(intervalId) clearInterval(intervalId);
    });

    watch(goldTab, (newVal) => {
        if (newVal === 'vietnam' && !goldValues.value.data.length) fetchGoldPrices();
    });

    watch(silverTab, (newVal) => {
        if (newVal === 'vietnam' && !silverValues.value.htmlContent) fetchSilverPrices();
    });

    return {
        selectedCommodity,
        goldTab,
        silverTab,
        goldValues,
        silverValues,
        calculateSpread
    };
  }
};
</script>

<style scoped>
.nav-pills .nav-link {
    border-radius: 0.5rem;
    transition: all 0.3s;
}
.nav-pills .nav-link:hover {
    transform: translateY(-2px);
}
.nav-tabs .nav-link {
    cursor: pointer;
}
.silver-content {
  width: 100%;
  overflow-x: auto;
}
.silver-content :deep(table) {
  width: 100%;
  margin-bottom: 0;
}
.silver-content :deep(table tbody tr:hover) {
  background-color: #e2e3e5;
}
</style>
