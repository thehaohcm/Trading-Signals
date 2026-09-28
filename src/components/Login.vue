<template>
  <div class="login-page-wrapper d-flex flex-column min-vh-100">
    <div class="auth-container flex-grow-1 d-flex flex-column align-items-center justify-content-center py-5 px-3">
      <!-- Ambient Cyber Glows in Background -->
      <div class="glow-orb glow-orb-1"></div>
      <div class="glow-orb glow-orb-2"></div>

      <!-- Header & Brand Logo -->
      <div class="text-center mb-4" style="z-index: 2;">
        <router-link to="/" class="d-inline-block logo-link">
          <div class="logo-aura mb-2 d-inline-block">
            <img src="../assets/logo.png" alt="Trading Signals Logo" class="auth-logo" />
          </div>
        </router-link>
        <h3 class="auth-title mb-1">Trading Signals Terminal</h3>
        <p class="auth-subtitle">Sign in to your account</p>
      </div>

      <!-- Clerk SignIn Component -->
      <div class="clerk-container" style="z-index: 2;">
        <SignIn routing="path" path="/login" sign-up-url="/sign-up" />
      </div>

      <!-- Security Footer -->
      <div class="auth-footer text-center mt-4 pt-3" style="z-index: 2;">
        <small class="text-muted d-flex align-items-center justify-content-center gap-1.5" style="color: #64748b !important; font-size: 0.78rem;">
          <i class="bi bi-shield-check text-info me-1"></i> Powered by Clerk Authentication Security
        </small>
      </div>
    </div>
  </div>
</template>

<script>
import { SignIn } from '@clerk/vue';

export default {
  name: 'LoginPage',
  components: {
    SignIn,
  },
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

.logo-aura {
  padding: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(0, 242, 254, 0.1);
}

.auth-logo {
  max-height: 65px;
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

.clerk-container {
  display: flex;
  justify-content: center;
  width: 100%;
}
</style>
