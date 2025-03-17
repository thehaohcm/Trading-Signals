<template>
  <NavBar />
  <div class="container mt-4">
    <h2>Economic Calendar</h2>
    <div v-if="isLoading" class="d-flex justify-content-center">
        <div class="spinner"></div>
    </div>
    <table class="table table-striped">
      <thead>
        <tr>
          <th>Date</th>
          <th>Country</th>
          <th>Title</th>
          <th>Impact</th>
          <th>Forecast</th>
          <th>Previous</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in sortedData" :key="item.date + item.title">
          <td>{{ formatDate(item.date) }}</td>
          <td>{{ item.country }}</td>
          <td>{{ item.title }}</td>
          <td>{{ item.impact }}</td>
          <td>{{ item.forecast }}</td>
          <td>{{ item.previous }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <AppFooter />
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

export default {
  components: {
    NavBar,
    AppFooter
  },
  setup() {
    const data = ref([]);
    const isLoading = ref(false);

    onMounted(async () => {
      isLoading.value = true;
      try {
        const response = await axios.get('/ff_calendar_thisweek.json');
        data.value = response.data;
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        isLoading.value = false;
      }
    });

    const sortedData = computed(() => {
      return [...data.value].sort((a, b) => new Date(a.date) - new Date(b.date));
    });

    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleString(); // Or any other desired format
    }

    return {
      data,
      sortedData,
      formatDate
    };
  },
};
</script>