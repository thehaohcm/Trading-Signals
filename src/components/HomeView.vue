<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />
    <notifications />
    <div class="home-view container mt-4 flex-grow-1">
      <ul class="nav nav-tabs" id="myTab" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active" id="rrg-tab" data-bs-toggle="tab" data-bs-target="#rrg" type="button" role="tab" aria-controls="rrg" aria-selected="true">RRG Chart</button>
        </li>
      </ul>
      <div class="tab-content" id="myTabContent">
        <div class="tab-pane fade show active" id="rrg" role="tabpanel" aria-labelledby="rrg-tab">
          <div class="text-center mt-3">
            <div class="mb-3">
              <button
                class="btn btn-primary btn-lg"
                @click="runSSHScript('assets_rrg')"
                :disabled="isRunningScript"
                style="min-width: 180px;"
              >
                <span v-if="isRunningScript" class="spinner-border spinner-border-sm me-2"></span>
                <span v-else style="display: inline-flex; align-items: center; gap: 6px;">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                  Generate RRG Chart
                </span>
              </button>
            </div>
            <div class="d-flex justify-content-center">
              <img :src="assetsRRGUrl" class="img-fluid rounded shadow-lg" style="max-width: 100%; border: 1px solid #ddd;" alt="RRG Chart" />
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
import AppFooter  from './AppFooter.vue';
import { ref, computed } from 'vue';
import { useNotification } from "@kyvg/vue3-notification";

export default {
  name: 'HomeView',
  components: {
    NavBar,
    AppFooter,
  },
  setup() {
    const { notify } = useNotification();
    const isRunningScript = ref(false);
    const assetsRRGKey = ref(Date.now());
    const assetsRRGUrl = computed(() => `/assets_rrgchart?t=${assetsRRGKey.value}`);

    const runSSHScript = async (scriptType) => {
      isRunningScript.value = true;
      try {
        const response = await fetch('/runSSHScript', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ script_type: scriptType }),
        });
        const data = await response.json();
        if (response.ok && data.success) {
          notify({
            type: 'success',
            title: 'Success',
            text: 'Assets RRG Chart has been updated successfully!',
          });
          assetsRRGKey.value = Date.now();
        } else {
          throw new Error(data.error || 'Server returned an error');
        }
      } catch (error) {
        console.error('Error running SSH script:', error);
        notify({
          type: 'error',
          title: 'Execution Failed',
          text: error.message || 'Failed to connect or run the SSH script.',
        });
      } finally {
        isRunningScript.value = false;
      }
    };

    return {
      isRunningScript,
      assetsRRGUrl,
      runSSHScript,
    };
  }
}
</script>

<style scoped>
/* Scoped styles if necessary */
</style>
