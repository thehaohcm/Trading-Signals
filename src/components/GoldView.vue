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
          <tr>
            <td><strong>5m</strong></td>
            <td><span style="display: block; font-size: 15px;" class="badge bg-secondary">Waiting...</span></td>
          </tr>
          <tr>
            <td><strong>15m</strong></td>
            <td><span style="display: block; font-size: 15px;" class="badge bg-secondary">Waiting...</span></td>
          </tr>
          <tr>
            <td><strong>1h</strong></td>
            <td><span style="display: block; font-size: 15px;" class="badge bg-secondary">Waiting...</span></td>
          </tr>
          <tr>
            <td><strong>4h</strong></td>
            <td><span style="display: block; font-size: 15px;" class="badge bg-secondary">Waiting...</span></td>
          </tr>
          <tr>
            <td><strong>1d</strong></td>
            <td><span style="display: block; font-size: 15px;" class="badge bg-secondary">Waiting...</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <p style="font-weight: bold;" :style="{ color: isConnected ? 'green' : 'red' }">WebSocket is {{ isConnected ? 'connected' : 'disconnected' }}</p>
  </div>
  <AppFooter />
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';

export default {
  components: {
    NavBar,
    AppFooter
  },
  props: {
    isConnected: {
      type: Boolean,
      required: true
    }
  },
};
</script>

<style>
.table-light {
    background-color: #edf2f7;
    text-align: left;
}
</style>