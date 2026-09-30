import { clerkPlugin } from '@clerk/vue';
import { createApp } from 'vue';
import App from './App.vue';
import router from './router'; // Import the router
import 'bootstrap/dist/css/bootstrap.min.css';
import Notifications from '@kyvg/vue3-notification';
import 'vue3-select/dist/vue3-select.css';

const PUBLISHABLE_KEY = process.env.VUE_APP_CLERK_PUBLISHABLE_KEY || 'pk_test_aG90LXN1bmJpcmQtNTY5LmNsZXJrLmFjY291bnRzLmRldiQ';
if (!PUBLISHABLE_KEY) {
  throw new Error("Missing VUE_APP_CLERK_PUBLISHABLE_KEY. Add your key to .env.local.");
}

// iOS Safari error logging
window.addEventListener('error', (event) => {
  console.error('Window error:', event.error);
  // Try to send error to a logging service if needed
  const errorInfo = {
    message: event.message,
    source: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error?.stack
  };
  console.log('Error details:', JSON.stringify(errorInfo));
});

const app = createApp(App);

// Global error handler
app.config.errorHandler = (err, instance, info) => {
  console.error('Global error:', err?.message || err, err?.stack);
  console.error('Error info:', info);
  console.error('Component instance name:', instance?.$options?.name || 'anonymous');
  
  // Log to console for iOS debugging
  try {
    const errorDetails = {
      message: err.message,
      stack: err.stack,
      info: info,
      component: instance?.$options?.name
    };
    console.log('Vue error details:', JSON.stringify(errorDetails));
  } catch (e) {
    console.error('Error logging failed:', e);
  }
};

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled promise rejection:', event.reason);
  const rejectInfo = {
    reason: event.reason?.message || String(event.reason),
    promise: String(event.promise)
  };
  console.log('Rejection details:', JSON.stringify(rejectInfo));
});

app.use(router); // Use the router
app.use(Notifications);
app.use(clerkPlugin, {
  publishableKey: PUBLISHABLE_KEY,
  signInUrl: '/sign-in',
  signUpUrl: '/sign-up',
  afterSignInUrl: '/',
  afterSignUpUrl: '/',
});

// Ensure app mounts after DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    app.mount('#app');
  });
} else {
  app.mount('#app');
}