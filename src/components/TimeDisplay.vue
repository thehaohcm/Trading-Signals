<template>
  <div class="d-flex align-items-center">
    <span class="time-display">{{ currentTime }}</span>
    <select v-model="selectedTimezone">
      <option value="UTC">UTC</option>
      <option value="America/Los_Angeles">Los Angeles</option>
      <option value="America/New_York">New York</option>
      <option value="Europe/London">London</option>
      <option value="Asia/Tokyo">Tokyo</option>
      <option value="Asia/Ho_Chi_Minh">Ho Chi Minh</option>
    </select>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue';
import moment from 'moment-timezone';

export default {
  setup() {
    const currentTime = ref('');
    const selectedTimezone = ref('Asia/Ho_Chi_Minh'); // Default timezone
    let intervalId = null;

    const updateTime = () => {
      currentTime.value = moment().tz(selectedTimezone.value).format('YYYY-MM-DD HH:mm:ss');
    };

    onMounted(() => {
      updateTime(); // Initial time
      intervalId = setInterval(updateTime, 1000);
    });

    onUnmounted(() => {
      clearInterval(intervalId);
    });

    return {
      currentTime,
      selectedTimezone,
    };
  },
};
</script>

<style scoped>
/* Add any necessary styling here */
</style>

<style scoped>
.time-display {
  font-weight: bold;
  margin-right: 5px; /* Add some spacing between time and dropdown */
}

select {
  padding: 2px 5px;
  border-radius: 4px;
  border: 1px solid #ced4da;
  background-color: #fff;
  color: #495057;
}

.time-display {
  font-size: 1.1rem; /* Slightly larger font */
  color: #6c757d;     /* Subtle text color */
  margin-right: 0.5rem; /* Space from the dropdown */
}
</style>