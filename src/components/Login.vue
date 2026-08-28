<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-body">
            <div class="text-center mb-4">
              <img src="../assets/logo.png" alt="Logo" class="img-fluid" style="max-height: 100px;">
            </div>
            <h4 class="text-center mb-4">Login</h4>
           <div v-if="isLoading" class="text-center"><div class="spinner"></div></div>
           <form v-else @submit.prevent="handleSubmit">
             <div class="mb-3">
               <label for="email" class="form-label">Email address</label>
               <input type="email" class="form-control" id="email" v-model="email" required>
             </div>
             <div class="mb-3">
               <label for="password" class="form-label">Password</label>
               <input type="password" class="form-control" id="password" v-model="password" required>
             </div>
             <div class="mb-3 d-flex align-items-center">
               <input type="checkbox" class="form-check-input" id="rememberMe" style="margin-right: 10px;">
               <label class="form-check-label" for="rememberMe">Remember me</label>
             </div>
             <div v-if="errorMessage" class="alert alert-danger" role="alert">
               {{ errorMessage }}
             </div>
             <button type="submit" class="btn btn-primary w-100 mb-3">Login</button>
             <button type="button" class="btn btn-secondary w-100" @click="handleDemoLogin">Demo Login (Test Mode)</button>
           </form>
         </div>
       </div>
     </div>
   </div>
 </div>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'LoginPage',
  emits: ['close-login'],
  setup(props, { emit }) {
    const email = ref('');
    const password = ref('');
    const errorMessage = ref('');
    const router = useRouter();
    const isLoading = ref(false);
    const handleSubmit = async () => {
     isLoading.value = true;
      errorMessage.value = ''; // Clear any previous error messages

      if (!email.value) {
        errorMessage.value = 'Please enter your email address.';
       isLoading.value = false;
        return;
      }

      if (!password.value) {
        errorMessage.value = 'Please enter your password.';
       isLoading.value = false;
        return;
      }

      try {
        const response = await fetch('/dnse-auth-service/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: email.value,
            password: password.value,
          }),
        });

        const data = await response.json();

        if (response.ok && data.token) { // Check for HTTP status and accessToken
          // Store the token and user info in local storage
          localStorage.setItem('token', data.token);
          localStorage.setItem('refreshToken', data.refreshToken);
          localStorage.setItem('userInfo', JSON.stringify(data)); // Store the entire data object
          // Emit the close-login event
          emit('close-login');
          // Redirect to the my-portfolio page
          router.push('/my-portfolio');
        } else {
          // Handle API errors (e.g., invalid credentials)
          errorMessage.value = data.message || data.error || 'Invalid credentials. Please try again.';
        }
      } catch (error) {
        // Handle network errors
        errorMessage.value = 'An error occurred. Please check your network connection.';
      } finally {
       isLoading.value = false;
      }
    };

    const handleDemoLogin = () => {
      const demoUser = {
        name: 'Demo User',
        custodyCode: 'DEMO123',
        id: 'demo-user-id',
        email: 'demo@example.com'
      };
      const demoToken = 'demo-token-' + Date.now();
      
      localStorage.setItem('token', demoToken);
      localStorage.setItem('refreshToken', 'demo-refresh-token');
      localStorage.setItem('userInfo', JSON.stringify(demoUser));
      
      emit('close-login');
      router.push('/my-portfolio');
    };

    return {
      email,
      password,
      handleSubmit,
      handleDemoLogin,
      errorMessage
    };
  },
};
</script>

<style scoped>
.container {
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card {
  background: rgba(18, 24, 38, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
  border-radius: 20px;
  backdrop-filter: blur(16px);
  color: #ffffff;
}

.card h4 {
  color: #ffffff;
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
}

.form-label {
  color: #94a3b8;
  font-weight: 600;
  font-size: 0.85rem;
}

.form-control {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(10, 13, 20, 0.8);
  color: #ffffff;
  padding: 10px 16px;
  transition: all 0.2s ease-in-out;
}

.form-control:focus {
  background: rgba(10, 13, 20, 0.95);
  color: #ffffff;
  border-color: #00f2fe;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15);
}

.btn-primary {
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  border: none;
  border-radius: 12px;
  padding: 12px 20px;
  font-weight: 700;
  color: #0a0d14;
  transition: all 0.25s ease-in-out;
}

.btn-primary:hover {
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.4);
  transform: translateY(-1px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  color: #e2e8f0;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.form-check-label {
  color: #94a3b8;
  font-size: 0.85rem;
}

a {
  color: #00f2fe;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

.spinner {
  border: 4px solid rgba(255, 255, 255, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #00f2fe;
  animation: spin 1s ease infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
