<template>
  <nav class="ts-navbar">
    <div class="ts-navbar-inner">
      <!-- Logo -->
      <router-link class="ts-brand" to="/">
        <img :src="logoImg" alt="Logo" class="ts-brand-logo" />
      </router-link>

      <!-- Mobile toggle -->
      <button class="ts-toggler" @click="toggleMenu" aria-label="Toggle navigation">
        <span class="ts-toggler-bar"></span>
        <span class="ts-toggler-bar"></span>
        <span class="ts-toggler-bar"></span>
      </button>

      <!-- Nav links -->
      <div class="ts-nav-collapse" :class="{ 'ts-nav-open': isMenuOpen }">
        <ul class="ts-nav-list">
          <li class="ts-nav-item">
            <router-link to="/crypto" class="ts-nav-link">
              <img :src="btcImg" class="ts-nav-icon" /> Crypto
            </router-link>
          </li>
          <li class="ts-nav-item">
            <router-link to="/stock" class="ts-nav-link">
              <img :src="stockImg" class="ts-nav-icon" /> Stock
            </router-link>
          </li>
          <li class="ts-nav-item">
            <router-link to="/commodities" class="ts-nav-link">
              <img :src="goldImg" class="ts-nav-icon" /> Commodities
            </router-link>
          </li>
          <li class="ts-nav-item">
            <router-link to="/forex" class="ts-nav-link">
              <img :src="forexImg" class="ts-nav-icon" /> Forex
            </router-link>
          </li>
          <li class="ts-nav-item">
            <router-link to="/real-estate" class="ts-nav-link">
              <img :src="realEstateImg" class="ts-nav-icon" /> Real Estate
            </router-link>
          </li>
          <li class="ts-nav-item" v-if="isLoggedIn">
            <router-link to="/my-portfolio" class="ts-nav-link">
              <img :src="portfolioImg" class="ts-nav-icon" /> Portfolio
            </router-link>
          </li>
          <li class="ts-nav-item" v-if="isLoggedIn">
            <router-link to="/community" class="ts-nav-link">
              <img :src="communityImg" class="ts-nav-icon" /> Community
            </router-link>
          </li>
          <li class="ts-nav-item" v-if="isLoggedIn">
            <router-link to="/macro-intel-hub" class="ts-nav-link ts-nav-link--macro">
              <span class="ts-macro-icon">🧠</span> Macro Hub
            </router-link>
          </li>
        </ul>
      </div>

      <!-- User area -->
      <div class="ts-user-area">
        <template v-if="isLoggedIn && userInfo">
          <div class="ts-user-dropdown" @mouseover="showDropdown = true" @mouseleave="showDropdown = false">
            <button class="ts-user-btn">
              <span class="ts-avatar">{{ userInfo.name ? userInfo.name.charAt(0).toUpperCase() : 'U' }}</span>
              <span class="ts-user-name">{{ userInfo.name }}</span>
              <svg class="ts-chevron" :class="{ 'ts-chevron--open': showDropdown }" width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <transition name="ts-dropdown-fade">
              <div v-if="showDropdown" class="ts-dropdown-menu">
                <div class="ts-dropdown-header">
                  <span class="ts-dropdown-name">{{ userInfo.name }}</span>
                  <span class="ts-dropdown-code">{{ userInfo.custodyCode }}</span>
                </div>
                <div class="ts-dropdown-divider"></div>
                <a class="ts-dropdown-item" @click="logout">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M6 14H3.333A1.333 1.333 0 0 1 2 12.667V3.333A1.333 1.333 0 0 1 3.333 2H6M10.667 11.333L14 8l-3.333-3.333M14 8H6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  Đăng xuất
                </a>
              </div>
            </transition>
          </div>
        </template>
        <template v-else>
          <router-link to="/login" class="ts-login-btn">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M10 2h2.667A1.333 1.333 0 0 1 14 3.333v9.334A1.333 1.333 0 0 1 12.667 14H10M6.667 11.333L10 8 6.667 4.667M10 8H2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Login
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import logoImg from '../assets/logo.png';
import btcImg from '../assets/btc.svg';
import stockImg from '../assets/stock.svg';
import goldImg from '../assets/gold.svg';
import silverImg from '../assets/silver.svg';
import forexImg from '../assets/forex.svg';
import portfolioImg from '../assets/portfolio.svg';
import communityImg from '../assets/community.svg';
import realEstateImg from '../assets/real_estate.svg';

export default {
  props: {
  },
  setup() {
    const router = useRouter();
    var userInfo = ref(null);
    const isMenuOpen = ref(false);
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };
    const showDropdown = ref(false);
    
    onMounted(() => {
      fetchUserInfo(); // Fetch user info on mount
    });

    const fetchUserInfo = async () => {
      // First try to load from localStorage
      const storedUserInfo = localStorage.getItem('userInfo');
      if (storedUserInfo) {
        try {
          userInfo.value = JSON.parse(storedUserInfo);
        } catch (e) {
          console.error("Error parsing stored user info:", e);
        }
      }

      // Then fetch from API to update
      const token = localStorage.getItem('token');
      if (token) {
        try {
          // Use relative URL to leverage proxy
          const response = await fetch('/dnse-user-service/api/me', {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (response.ok) {
            const data = await response.json();
            userInfo.value = data;
            localStorage.setItem('userInfo', JSON.stringify(data));
          } else {
             console.error("Failed to fetch user info:", response.status);
             if (response.status === 401) {
                 // Token might be invalid
                 logout();
             }
          }
        } catch (error) {
          console.error('Error fetching user info:', error);
        }
      }
    };

    const logout = () => {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userInfo');
      userInfo.value = null;
      router.push('/');
    }


    const isLoggedIn = computed(() => {
      try {
        const loggedIn = userInfo.value && userInfo.value.custodyCode;
        return loggedIn;
      } catch (error) {
        console.error('Error parsing userInfo:', error);
      }
      return false; // Return false if parsing fails
    });

    return {
      isMenuOpen,
      toggleMenu,
      showDropdown,
      logout,
      isLoggedIn,
      userInfo,
      logoImg,
      btcImg,
      stockImg,
      goldImg,
      silverImg,
      forexImg,
      portfolioImg,
      communityImg,
      realEstateImg
    };
  },
};
</script>

<style scoped>
/* ── Navbar shell ────────────────────────────────────── */
.ts-navbar {
  position: sticky;
  top: 0;
  z-index: 1050;
  background: linear-gradient(135deg, #1a1d29 0%, #252836 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.35);
}
.ts-navbar-inner {
  display: flex;
  align-items: center;
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 20px;
  height: 60px;
}

/* ── Brand / Logo ────────────────────────────────────── */
.ts-brand {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-right: 12px;
}
.ts-brand-logo {
  width: 38px;
  height: 38px;
  object-fit: contain;
  transition: transform 0.25s;
}
.ts-brand:hover .ts-brand-logo {
  transform: scale(1.08) rotate(-4deg);
}

/* ── Mobile toggler ──────────────────────────────────── */
.ts-toggler {
  display: none;
  flex-direction: column;
  gap: 5px;
  padding: 8px;
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  cursor: pointer;
  margin-left: auto;
}
.ts-toggler-bar {
  display: block;
  width: 22px;
  height: 2px;
  background: #ffffffcc;
  border-radius: 2px;
  transition: 0.25s;
}

/* ── Nav list ────────────────────────────────────────── */
.ts-nav-collapse {
  flex: 1;
  display: flex;
  align-items: center;
  overflow-x: auto;
  scrollbar-width: none;
}
.ts-nav-collapse::-webkit-scrollbar { display: none; }

.ts-nav-list {
  display: flex;
  align-items: center;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 2px;
}
.ts-nav-item {
  flex-shrink: 0;
}
.ts-nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13.5px;
  font-weight: 500;
  color: #a0aec0;
  text-decoration: none;
  border-radius: 8px;
  white-space: nowrap;
  transition: all 0.2s ease;
  position: relative;
}
.ts-nav-link:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.07);
}
.ts-nav-link.router-link-active {
  color: #63b3ed;
  background: rgba(99, 179, 237, 0.1);
  font-weight: 600;
}
.ts-nav-link.router-link-active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 2px;
  background: #63b3ed;
  border-radius: 2px;
}
.ts-nav-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
  flex-shrink: 0;
}

/* Macro Hub special styling */
.ts-nav-link--macro {
  color: #f6ad55;
}
.ts-nav-link--macro:hover {
  color: #fbd38d;
  background: rgba(246, 173, 85, 0.1);
}
.ts-nav-link--macro.router-link-active {
  color: #f6ad55;
  background: rgba(246, 173, 85, 0.12);
}
.ts-nav-link--macro.router-link-active::after {
  background: #f6ad55;
}
.ts-macro-icon {
  font-size: 16px;
  line-height: 1;
}

/* ── User area ───────────────────────────────────────── */
.ts-user-area {
  flex-shrink: 0;
  margin-left: 12px;
}
.ts-user-dropdown {
  position: relative;
}
.ts-user-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px 5px 5px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 40px;
  color: #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  font-weight: 500;
}
.ts-user-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.15);
}
.ts-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}
.ts-user-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ts-chevron {
  color: #a0aec0;
  transition: transform 0.2s;
  flex-shrink: 0;
}
.ts-chevron--open {
  transform: rotate(180deg);
}

/* Dropdown menu */
.ts-dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 200px;
  background: #2d3148;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  z-index: 1100;
}
.ts-dropdown-header {
  padding: 14px 16px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ts-dropdown-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}
.ts-dropdown-code {
  font-size: 12px;
  color: #718096;
}
.ts-dropdown-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.06);
  margin: 0 12px;
}
.ts-dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  font-size: 13.5px;
  color: #e2e8f0;
  cursor: pointer;
  transition: background 0.15s;
  text-decoration: none;
}
.ts-dropdown-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fc8181;
}
.ts-dropdown-item svg {
  flex-shrink: 0;
}

/* Dropdown animation */
.ts-dropdown-fade-enter-active,
.ts-dropdown-fade-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.ts-dropdown-fade-enter-from,
.ts-dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ── Login button ────────────────────────────────────── */
.ts-login-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  font-size: 13.5px;
  font-weight: 600;
  color: #e2e8f0;
  background: rgba(99, 179, 237, 0.15);
  border: 1px solid rgba(99, 179, 237, 0.3);
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.2s;
}
.ts-login-btn:hover {
  background: rgba(99, 179, 237, 0.25);
  border-color: rgba(99, 179, 237, 0.5);
  color: #fff;
}

/* ── Responsive ──────────────────────────────────────── */
@media (max-width: 1100px) {
  .ts-nav-link {
    font-size: 12.5px;
    padding: 7px 10px;
    gap: 5px;
  }
  .ts-nav-icon { width: 16px; height: 16px; }
}

@media (max-width: 991px) {
  .ts-toggler {
    display: flex;
  }
  .ts-nav-collapse {
    display: none;
    position: absolute;
    top: 60px;
    left: 0;
    right: 0;
    background: #252836;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    padding: 12px 16px;
    z-index: 1040;
  }
  .ts-nav-collapse.ts-nav-open {
    display: block;
  }
  .ts-nav-list {
    flex-direction: column;
    gap: 4px;
  }
  .ts-nav-link {
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 14px;
  }
  .ts-nav-link.router-link-active::after {
    display: none;
  }
  .ts-user-name {
    display: none;
  }
  .ts-user-btn {
    padding: 4px;
    border-radius: 50%;
  }
  .ts-chevron {
    display: none;
  }
}
</style>