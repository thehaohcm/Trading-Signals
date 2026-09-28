<template>
  <div class="clerk-auth-container d-flex flex-column min-vh-100 align-items-center justify-content-center py-5 px-3">
    <div class="glow-orb glow-orb-1"></div>
    <div class="glow-orb glow-orb-2"></div>
    <div class="text-center mb-4" style="z-index: 2;">
      <router-link to="/" class="d-inline-block logo-link">
        <img src="../assets/logo.png" alt="Trading Signals Logo" class="auth-logo mb-2" />
      </router-link>
      <h3 class="auth-title mb-1">Trading Signals</h3>
      <p class="auth-subtitle">Sign in to your account</p>
    </div>
    <div class="clerk-card-wrapper" style="z-index: 2;">
      <SignIn routing="path" path="/sign-in" sign-up-url="/sign-up" />
    </div>
  </div>
</template>

<script setup>
import { SignIn } from "@clerk/vue";
</script>

<style scoped>
.clerk-auth-container {
  background: #0a0d14;
  color: #e2e8f0;
  position: relative;
  overflow: hidden;
  min-height: 100vh;
}
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
.auth-logo {
  max-height: 65px;
  filter: drop-shadow(0 4px 12px rgba(0, 242, 254, 0.2));
}
.auth-title {
  font-family: 'Outfit', sans-serif;
  font-weight: 800;
  font-size: 1.6rem;
  color: #ffffff;
  letter-spacing: -0.5px;
}
.auth-subtitle {
  color: #94a3b8;
  font-size: 0.9rem;
}
.clerk-card-wrapper {
  display: flex;
  justify-content: center;
}
</style>
