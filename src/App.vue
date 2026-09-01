<template>
  <div id="app">
    <AlertOverlay />
    <NavBar />
    <div @click="toggleNewsPanel" class="news-btn shadow-sm" title="Mở bảng tin tức">
      <svg class="news-btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v1m2 4a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-1"></path>
        <path d="M12 9h2"></path>
        <path d="M12 13h2"></path>
      </svg>
      <span class="text">News</span>
    </div>
    <NewsPanel :isVisible="newsPanelVisible" @toggle="toggleNewsPanel" />
    
    <!-- Global Floating Scroll-To-Top Button -->
    <button 
      class="scroll-to-top-btn" 
      :class="{ 'scroll-to-top-btn--visible': showScrollTop }" 
      @click="scrollToTop" 
      title="Cuộn lên đầu trang"
      aria-label="Cuộn lên đầu trang"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="18 15 12 9 6 15"></polyline>
      </svg>
    </button>

    <router-view></router-view>
    <Chatbox />
  </div>
</template>

<script>
import NavBar from './components/NavBar.vue';
import NewsPanel from './components/NewsPanel.vue';
import Chatbox from './components/Chatbox.vue';
import AlertOverlay from './components/AlertOverlay.vue';

export default {
  name: 'App',
  components: {
    NavBar,
    NewsPanel,
    Chatbox,
    AlertOverlay,
  },
  data() {
    return {
      newsPanelVisible: false,
      showScrollTop: false,
    };
  },
  methods: {
    toggleNewsPanel() {
      this.newsPanelVisible = !this.newsPanelVisible;
    },
    scrollToTop() {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
      if (document.documentElement) {
        document.documentElement.scrollTo({ top: 0, behavior: 'smooth' });
      }
      if (document.body) {
        document.body.scrollTo({ top: 0, behavior: 'smooth' });
      }
      const scrollables = document.querySelectorAll('.stk-table-wrap, .table-container, .table-responsive, #app, main, .macro-modal-large');
      scrollables.forEach(el => {
        if (el && el.scrollTop > 0) {
          el.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    },
    handleScroll() {
      const winTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
      let maxSubScroll = 0;
      const scrollables = document.querySelectorAll('.stk-table-wrap, .table-container, .table-responsive, #app, main');
      scrollables.forEach(el => {
        if (el && el.scrollTop > maxSubScroll) {
          maxSubScroll = el.scrollTop;
        }
      });
      const top = Math.max(winTop, maxSubScroll);
      this.showScrollTop = top > 60;
    },
  },
  mounted() {
    this.handleOpenNews = () => {
      this.newsPanelVisible = true;
    };
    window.addEventListener('open-news-panel', this.handleOpenNews);
    window.addEventListener('scroll', this.handleScroll, true);
    document.addEventListener('scroll', this.handleScroll, true);
    this._intervalCheck = setInterval(this.handleScroll, 400);
    this.handleScroll();
  },
  beforeUnmount() {
    if (this.handleOpenNews) {
      window.removeEventListener('open-news-panel', this.handleOpenNews);
    }
    window.removeEventListener('scroll', this.handleScroll, true);
    document.removeEventListener('scroll', this.handleScroll, true);
    if (this._intervalCheck) {
      clearInterval(this._intervalCheck);
    }
  },
};
</script>

<style>
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css");
@import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css");
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap");

* {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow-x: hidden;
  background-color: #0a0d14 !important;
  color: #e2e8f0 !important;
}

#app {
  font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  background-color: #0a0d14;
}

/* Custom Sleek Cyber Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: #0a0d14;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 242, 254, 0.4);
}

/* Global Dark Bootstrap Table Overrides */
.table {
  --bs-table-bg: transparent !important;
  --bs-table-color: #e2e8f0 !important;
  --bs-table-hover-color: #ffffff !important;
  --bs-table-hover-bg: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  color: #e2e8f0 !important;
  margin-top: 1rem;
}
.table th {
  background-color: rgba(18, 24, 38, 0.9) !important;
  color: #94a3b8 !important;
  font-weight: 700;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
  text-transform: uppercase;
  font-size: 0.78rem;
  letter-spacing: 0.5px;
  vertical-align: middle;
}
.table td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
  color: #e2e8f0 !important;
  vertical-align: middle;
}
.table-striped > tbody > tr:nth-of-type(odd) > * {
  --bs-table-bg-type: rgba(255, 255, 255, 0.02) !important;
  color: #e2e8f0 !important;
}

/* Global Premium News Button */
.news-btn {
  position: fixed;
  right: 0;
  top: 45%;
  transform: translateY(-50%);
  z-index: 1050;
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.2) 0%, rgba(79, 172, 254, 0.3) 100%);
  border: 1px solid rgba(0, 242, 254, 0.4);
  backdrop-filter: blur(10px);
  color: #00f2fe;
  padding: 11px 18px 11px 16px;
  border-radius: 30px 0 0 30px;
  border-right: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  font-weight: 700;
  box-shadow: -4px 0 20px rgba(0, 242, 254, 0.2);
}

.news-btn:hover {
  transform: translateY(-50%) translateX(-4px);
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.35) 0%, rgba(79, 172, 254, 0.45) 100%);
  box-shadow: -6px 0 25px rgba(0, 242, 254, 0.35);
  color: #ffffff;
}

.news-btn:active {
  transform: translateY(-50%) translateX(-2px) scale(0.96);
}

.news-btn-icon {
  width: 18px;
  height: 18px;
  color: currentColor;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  animation: gentle-pulse 2s infinite alternate;
}

.news-btn .text {
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-size: 0.8rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

@keyframes gentle-pulse {
  0% { transform: scale(1); }
  100% { transform: scale(1.1); }
}

/* Global Dark Theme Utility Overrides */
.text-dark,
.text-slate-800,
.text-slate-900,
.text-slate-700,
.text-slate-600 {
  color: #e2e8f0 !important;
}

.text-secondary,
.text-muted,
.text-slate-500 {
  color: #94a3b8 !important;
}

.bg-white,
.bg-light {
  background-color: rgba(18, 24, 38, 0.75) !important;
  color: #e2e8f0 !important;
}

.card {
  background-color: rgba(18, 24, 38, 0.75) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #e2e8f0 !important;
}

.card-header,
.card-footer {
  background-color: rgba(10, 13, 20, 0.6) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  color: #ffffff !important;
}

.form-control,
.form-select,
.stk-input {
  background-color: rgba(10, 13, 20, 0.8) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: #ffffff !important;
}

.form-control:focus,
.form-select:focus,
.stk-input:focus {
  border-color: #00f2fe !important;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15) !important;
  color: #ffffff !important;
  background-color: rgba(10, 13, 20, 0.95) !important;
}

.form-control::placeholder,
.stk-input::placeholder {
  color: #64748b !important;
}

.modal-content {
  background-color: #111726 !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: #e2e8f0 !important;
}

/* Global Floating Scroll-To-Top Button */
.scroll-to-top-btn {
  position: fixed;
  bottom: 90px;
  right: 24px;
  z-index: 999999 !important;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: rgba(18, 24, 38, 0.92);
  border: 1.5px solid rgba(0, 242, 254, 0.5);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: #00f2fe;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6), 0 0 15px rgba(0, 242, 254, 0.25);
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: translateY(16px) scale(0.85);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  outline: none;
  padding: 0;
}

.scroll-to-top-btn--visible {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
  transform: translateY(0) scale(1);
}

.scroll-to-top-btn:hover {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.3) 0%, rgba(79, 172, 254, 0.4) 100%);
  border-color: #00f2fe;
  color: #ffffff;
  box-shadow: 0 6px 24px rgba(0, 242, 254, 0.5), 0 0 20px rgba(0, 242, 254, 0.4);
  transform: translateY(-4px) scale(1.08);
}

.scroll-to-top-btn:active {
  transform: translateY(-1px) scale(0.96);
}

@media (max-width: 768px) {
  .news-btn {
    top: 45%;
    padding: 8px 12px 8px 10px;
    font-size: 0.75rem;
  }
  .news-btn-icon {
    width: 15px;
    height: 15px;
  }
  .scroll-to-top-btn {
    bottom: 82px;
    right: 18px;
    width: 40px;
    height: 40px;
  }
}
</style>
