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
            <form @submit.prevent="handleSubmit">
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
              <button type="submit" class="btn btn-primary w-100">Login</button>
              <div class="mt-3 text-center">
                <a href="#" @click.prevent="handleForgotPassword">Forgot Password?</a>
              </div>
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

    const handleSubmit = async () => {
      errorMessage.value = ''; // Clear any previous error messages

      if (!email.value) {
        errorMessage.value = 'Please enter your email address.';
        return;
      }

      if (!password.value) {
        errorMessage.value = 'Please enter your password.';
        return;
      }

      try {
        const response = await fetch('https://services.entrade.com.vn/dnse-auth-service/login', {
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
          localStorage.setItem('userInfo', JSON.stringify(data.userInfo));
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
      }
    };

    const handleForgotPassword = () => {
      // Implement your forgot password logic here
      console.log('Forgot Password clicked');
      // You might want to show a modal or navigate to a different page
    };

    return {
      email,
      password,
      handleSubmit,
      handleForgotPassword,
      errorMessage
    };
  },
};
</script>

<style scoped>
.container {
  background-image: url('https://images.unsplash.com/photo-1625580794409-4577d3b77557'); /* Stock bullish image */
  background-size: cover;
  background-position: center;
  min-height: 100vh; /* Ensure the background covers the entire viewport height */
}

.card {
  background-color: rgba(255, 255, 255, 0.8); /* Semi-transparent white */
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.card-header h4 {
    color: #333;
}
.form-label{
    color:#333;
}

.form-control {
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  transition: border-color 0.2s ease-in-out;
}

.form-control:focus {
  border-color: #007bff; /* Or any other color you prefer */
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
  border-radius: 20px;
  padding: 10px 20px;
  transition: background-color 0.2s ease-in-out;
}

.btn-primary:hover {
  background-color: #0056b3;
  border-color: #0056b3;
}

.form-check-label {
    color:#333
}

a {
  color: #007bff;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* Add component-specific styles here if needed */
</style>
