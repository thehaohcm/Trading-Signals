<template>
  <div class="login-page-wrapper d-flex flex-column min-vh-100">
    <div class="auth-container flex-grow-1 d-flex align-items-center justify-content-center py-5 px-3">
      <!-- Ambient Cyber Glows in Background -->
      <div class="glow-orb glow-orb-1"></div>
      <div class="glow-orb glow-orb-2"></div>

      <div class="auth-card glass-panel">
        <!-- Logo & Header -->
        <div class="text-center mb-4">
          <div class="logo-aura mb-3 d-inline-block">
            <img src="../assets/logo.png" alt="Trading Signals Logo" class="auth-logo" />
          </div>
          <h3 class="auth-title mb-1">Welcome Back</h3>
          <p class="auth-subtitle">Sign in to your Trading Signals Terminal</p>
        </div>

        <div v-if="isLoading" class="text-center py-5">
          <div class="spinner-border text-info" role="status" style="width: 2.5rem; height: 2.5rem;">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-3 text-muted small" style="color: #94a3b8 !important;">Authenticating account credentials...</p>
        </div>

        <form v-else @submit.prevent="handleSubmit" class="auth-form">
          <!-- Email / Custody Code -->
          <div class="mb-3">
            <label for="email" class="auth-label">Email or Account ID</label>
            <div class="input-icon-wrapper">
              <i class="bi bi-envelope input-icon"></i>
              <input 
                type="text" 
                class="form-control auth-input" 
                id="email" 
                v-model="email" 
                placeholder="name@example.com or Custody Code"
                required
                autocomplete="username"
              />
            </div>
          </div>

          <!-- Password -->
          <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <label for="password" class="auth-label mb-0">Password</label>
            </div>
            <div class="input-icon-wrapper">
              <i class="bi bi-lock input-icon"></i>
              <input 
                :type="showPassword ? 'text' : 'password'" 
                class="form-control auth-input" 
                id="password" 
                v-model="password" 
                placeholder="••••••••"
                required
                autocomplete="current-password"
              />
              <button 
                type="button" 
                class="btn-toggle-pwd" 
                @click="showPassword = !showPassword"
                tabindex="-1"
              >
                <i :class="showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
              </button>
            </div>
          </div>

          <!-- Remember Me -->
          <div class="mb-4 d-flex align-items-center justify-content-between">
            <div class="form-check custom-checkbox">
              <input type="checkbox" class="form-check-input" id="rememberMe">
              <label class="form-check-label small" for="rememberMe" style="color: #94a3b8;">Remember me</label>
            </div>
          </div>

          <!-- Error Alert -->
          <div v-if="errorMessage" class="alert alert-danger custom-alert mb-3" role="alert">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            <span>{{ errorMessage }}</span>
          </div>

          <!-- Login Submit Button -->
          <button type="submit" class="btn btn-primary w-100 py-2.5 auth-btn-submit mb-3">
            <span>Sign In to Terminal</span>
            <i class="bi bi-arrow-right ms-2"></i>
          </button>

          <!-- Divider -->
          <div class="auth-divider mb-3">
            <span>OR QUICK ACCESS</span>
          </div>

          <!-- Demo Login Button -->
          <button type="button" class="btn btn-demo w-100 py-2.5 d-flex align-items-center justify-content-center gap-2" @click="handleDemoLogin">
            <span class="demo-lightning">⚡</span>
            <span class="fw-bold">Launch Demo Terminal</span>
            <span class="badge demo-badge">Test Mode</span>
          </button>
        </form>

        <!-- Security Footer -->
        <div class="auth-footer text-center mt-4 pt-3 border-top" style="border-color: rgba(255, 255, 255, 0.08) !important;">
          <small class="text-muted d-flex align-items-center justify-content-center gap-1.5" style="color: #64748b !important; font-size: 0.76rem;">
            <i class="bi bi-shield-check text-success"></i> 256-bit Encrypted SSL Security
          </small>
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
    const showPassword = ref(false);
    const errorMessage = ref('');
    const router = useRouter();
    const isLoading = ref(false);

    const handleSubmit = async () => {
      isLoading.value = true;
      errorMessage.value = '';

      if (!email.value) {
        errorMessage.value = 'Please enter your email or Account ID.';
        isLoading.value = false;
        return;
      }

      if (!password.value) {
        errorMessage.value = 'Please enter your password.';
        isLoading.value = false;
        return;
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 12000); // 12 seconds timeout

      try {
        const response = await fetch('/dnse-auth-service/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: email.value.trim(),
            password: password.value,
          }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        let data = {};
        try {
          data = await response.json();
        } catch (jsonErr) {
          // If response is HTML / gateway error
          data = {};
        }

        if (response.ok && data.token) {
          localStorage.setItem('token', data.token);
          localStorage.setItem('refreshToken', data.refreshToken || '');
          localStorage.setItem('userInfo', JSON.stringify(data));
          emit('close-login');
          router.push('/my-portfolio');
        } else if (response.status === 400 || response.status === 401) {
          errorMessage.value = data.message || 'Invalid account ID or password. Please check and try again.';
        } else if (response.status === 429) {
          errorMessage.value = 'Too many login attempts. Please wait a moment or use Launch Demo Terminal.';
        } else if (response.status >= 500) {
          errorMessage.value = 'DNSE server is temporarily busy or in maintenance. You can use Launch Demo Terminal.';
        } else {
          errorMessage.value = data.message || data.error || 'Authentication failed. Please try again.';
        }
      } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
          errorMessage.value = 'Connection timed out (DNSE server is taking too long to respond). Please retry or launch Demo Terminal.';
        } else {
          errorMessage.value = 'Network error or connection blocked. Please check your internet connection.';
        }
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
      showPassword,
      handleSubmit,
      handleDemoLogin,
      errorMessage,
      isLoading
    };
  }
};
</script>

<style scoped>
.login-page-wrapper {
  background: #0a0d14;
  color: #e2e8f0;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.auth-container {
  position: relative;
  z-index: 1;
}

/* ── Ambient glow orbs ── */
.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  pointer-events: none;
  z-index: 0;
}
.glow-orb-1 {
  width: 350px;
  height: 350px;
  background: rgba(0, 242, 254, 0.12);
  top: 20%;
  left: 50%;
  transform: translate(-50%, -30%);
}
.glow-orb-2 {
  width: 300px;
  height: 300px;
  background: rgba(59, 130, 246, 0.08);
  bottom: 10%;
  left: 50%;
  transform: translate(-50%, 0);
}

/* ── Auth Card ── */
.auth-card {
  width: 100%;
  max-width: 460px;
  background: rgba(18, 24, 38, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 2.5rem 2rem;
  box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.7), 0 0 40px rgba(0, 242, 254, 0.05);
  backdrop-filter: blur(20px);
  position: relative;
  z-index: 2;
  animation: cardFadeIn 0.35s ease-out;
}

@keyframes cardFadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.logo-aura {
  padding: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(0, 242, 254, 0.1);
}

.auth-logo {
  max-height: 75px;
  display: block;
}

.auth-title {
  font-family: 'Outfit', sans-serif;
  font-weight: 800;
  font-size: 1.65rem;
  color: #ffffff;
  letter-spacing: -0.5px;
}

.auth-subtitle {
  color: #94a3b8;
  font-size: 0.88rem;
  margin: 0;
}

/* ── Inputs ── */
.auth-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.4rem;
}

.input-icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  color: #64748b;
  font-size: 1rem;
  pointer-events: none;
}

.auth-input {
  padding-left: 44px;
  padding-right: 44px;
  height: 48px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(10, 13, 20, 0.8) !important;
  color: #ffffff !important;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.auth-input:focus {
  background: rgba(10, 13, 20, 0.95) !important;
  border-color: #00f2fe;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15);
  outline: none;
}

.auth-input::placeholder {
  color: #475569;
}

.btn-toggle-pwd {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: #64748b;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 4px 8px;
  transition: color 0.15s;
}

.btn-toggle-pwd:hover {
  color: #00f2fe;
}

/* ── Custom Checkbox ── */
.custom-checkbox .form-check-input {
  background-color: rgba(10, 13, 20, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
}

.custom-checkbox .form-check-input:checked {
  background-color: #00f2fe;
  border-color: #00f2fe;
}

/* ── Alert ── */
.custom-alert {
  background: rgba(255, 75, 114, 0.12);
  border: 1px solid rgba(255, 75, 114, 0.3);
  color: #ff4b72;
  border-radius: 10px;
  font-size: 0.85rem;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
}

/* ── Buttons ── */
.auth-btn-submit {
  height: 48px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.95rem;
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  border: none;
  color: #0a0d14;
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.3);
  transition: all 0.25s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.auth-btn-submit:hover {
  box-shadow: 0 8px 25px rgba(0, 242, 254, 0.45);
  transform: translateY(-1px);
}

.auth-divider {
  display: flex;
  align-items: center;
  text-align: center;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 1px;
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.auth-divider span {
  padding: 0 12px;
}

.btn-demo {
  height: 46px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e2e8f0;
  font-size: 0.9rem;
  transition: all 0.25s ease;
}

.btn-demo:hover {
  background: rgba(0, 242, 254, 0.1);
  border-color: rgba(0, 242, 254, 0.3);
  color: #00f2fe;
  transform: translateY(-1px);
}

.demo-lightning {
  color: #f6d365;
}

.demo-badge {
  background: rgba(0, 242, 254, 0.15);
  color: #00f2fe;
  border: 1px solid rgba(0, 242, 254, 0.3);
  font-size: 0.7rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
}

@media (max-width: 576px) {
  .auth-card {
    padding: 2rem 1.25rem;
    border-radius: 18px;
  }
}
</style>
