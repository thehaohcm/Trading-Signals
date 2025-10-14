<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />

    <div class="container mt-4 flex-grow-1">
      <TradingViewChart :coin="'OANDA:XAUUSD'" />
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
      goldPrices: null,
      error: null,
    };
  },
  mounted() {
  },
  methods: {
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