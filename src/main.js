import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // Import the router
import 'bootstrap/dist/css/bootstrap.min.css';
import Notifications from '@kyvg/vue3-notification'

const app = createApp(App);

// Global error handler
app.config.errorHandler = (err, instance, info) => {
  console.error('Global error:', err);
  console.error('Error info:', info);
  console.error('Component instance:', instance);
};

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled promise rejection:', event.reason);
});

app.use(router); // Use the router
app.use(Notifications)
app.mount('#app');
