<template>
  <div class="home-view container-fluid mt-3">
    <ul class="nav nav-tabs" id="myTab" role="tablist">
      <li class="nav-item" role="presentation">
        <button class="nav-link active" id="rrg-tab" data-bs-toggle="tab" data-bs-target="#rrg" type="button" role="tab" aria-controls="rrg" aria-selected="true">RRG Chart</button>
      </li>
    </ul>
    <div class="tab-content" id="myTabContent">
      <div class="tab-pane fade show active" id="rrg" role="tabpanel" aria-labelledby="rrg-tab">
        <div class="d-flex justify-content-center mt-3">
            <img src="/assets_rrgchart" class="img-fluid" alt="RRG Chart" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HomeView',
}
</script>

<style scoped>
.home-view {
    padding: 20px;
}
</style>
