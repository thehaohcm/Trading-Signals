<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />

    <div>
      <button @click="fetchGoldPrices" class="btn btn-primary mb-3">Refresh Gold Price</button>
      <div v-if="goldPrices && goldPrices.data && goldPrices.data.length > 0">
        <p>Latest updated: {{ goldPrices.data[0].dateTime }}</p>
      </div>
    </div>

    <div class="container mt-4 flex-grow-1">
      <table class="table table-hover">
        <tbody>
          <tr>
            <td colspan="2" class="table-light">
              <img :src="require(`../assets/gold.svg`)" style="width: 25px; height: 25px; margin-right: 5px;" />
              <strong>Gold</strong>
              <div style="float: right;">VND</div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="error">
        <p>Error: {{ error }}</p>
      </div>
      <div v-else-if="goldPrices">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Gold</th>
              <th>Buying Price</th>
              <th>Selling Price</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(price, index) in goldPrices.data" :key="index">
              <td><strong>{{ price.code }}</strong></td>
              <td>
                <span style="display: block; font-size: 15px;" class="badge bg-success">
                  {{ formatNumber(price.sellingPrice) }}
                </span>
              </td>
              <td>
                <span style="display: block; font-size: 15px;" class="badge bg-danger">
                  {{ formatNumber(price.buyingPrice) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else>
        <p>Loading gold prices...</p>
      </div>
    </div>
  </div>
  <AppFooter />
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';

export default {
  components: {
    NavBar,
    AppFooter,
  },
  props: {
  },
  data() {
    return {
      goldPrices: null,
      error: null,
    };
  },
  mounted() {
    this.fetchGoldPrices();
  },
  methods: {
    async fetchGoldPrices() {
      try {
        const response = await fetch('/api/v1/gold/prices/current');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        this.goldPrices = data;
      } catch (error) {
        this.error = error.message;
        console.error('Error fetching gold prices:', error);
      }
    },
    formatNumber(number) {
      if (number === null || number === undefined) {
        return 'N/A';
      }
      return number.toLocaleString() + ' VND';
    },
  },
};
</script>

<style>
.table-light {
  background-color: #edf2f7;
  text-align: left;
}

.badge {
    width: 100%;
    text-align: center;
}
</style>