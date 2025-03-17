<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />
    <div class="container mt-4 flex-grow-1">
      <table class="table table-hover">
        <tbody>
          <tr>
            <td colspan="2" class="table-light">
              <img :src="require(`../assets/gold.svg`)" style="width: 25px; height: 25px; margin-right: 5px;" />
              <strong>Gold</strong>
              <div style="float: right;">USD</div>
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
              <th>Code</th>
              <th>Buying Price</th>
              <th>Selling Price</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(price, index) in goldPrices.data" :key="index">
              <td><strong>{{ price.code }}</strong></td>
              <td>
                <span style="display: block; font-size: 15px;" class="badge bg-success">
                  {{ price.buyingPrice }}
                </span>
              </td>
              <td>
                <span style="display: block; font-size: 15px;" class="badge bg-warning">
                  {{ price.sellingPrice }}
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

    <p style="font-weight: bold;" :style="{ color: isConnected ? 'green' : 'red' }">
      WebSocket is {{ isConnected ? 'connected' : 'disconnected' }}
    </p>
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
    isConnected: {
      type: Boolean,
      required: true,
    },
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