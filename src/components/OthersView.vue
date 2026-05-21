<template>
  <div class="d-flex flex-column min-vh-100">
    <NavBar />
    <div class="container mt-4 flex-grow-1">
      <!-- Title -->
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h2 class="mb-0 fw-bold d-flex align-items-center gap-2 text-dark">
          <span>🌐</span> Useful Links & Resources
        </h2>
        <span class="badge bg-primary px-3 py-2 shadow-sm" style="background-color: #3182ce !important; font-size: 0.9rem;">
          Resource Hub
        </span>
      </div>

      <!-- Introduction Panel -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card border-0 shadow-sm" style="background: #ffffff; border-left: 4px solid #3182ce !important;">
            <div class="card-body text-dark py-3">
              <p class="mb-0" style="color: #4a5568; font-size: 0.95rem; line-height: 1.6;">
                A curated directory of useful macroeconomic websites, charting platforms, and financial portals. These external resources provide deeper insights into global monetary policy and economic trends to refine your trading analysis.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Grid of Links -->
      <div class="row">
        <div class="col-12 col-md-6 col-lg-4 mb-4" v-for="(link, index) in links" :key="index">
          <a :href="link.url" target="_blank" class="resource-card-link">
            <div class="card h-100 border-0 shadow-sm resource-card">
              <div class="card-body p-4 d-flex flex-column justify-content-between">
                <div>
                  <!-- Header Area -->
                  <div class="d-flex align-items-center justify-content-between mb-3">
                    <span class="resource-icon">{{ link.icon }}</span>
                    <span class="badge bg-light text-primary border px-2 py-1" style="font-size: 0.75rem; font-weight: 600;">
                      {{ link.category }}
                    </span>
                  </div>
                  
                  <!-- Title and Description -->
                  <h5 class="fw-bold text-dark mb-2 resource-title d-flex align-items-center gap-1">
                    {{ link.title }}
                  </h5>
                  <p class="resource-desc text-muted mb-4">
                    {{ link.description }}
                  </p>
                </div>
                
                <!-- Action Area -->
                <div class="d-flex align-items-center justify-content-between pt-2 border-top">
                  <span class="resource-domain text-truncate" style="color: #718096; font-size: 0.8rem;">
                    {{ getDomain(link.url) }}
                  </span>
                  <span class="btn-visit">
                    Visit Site ↗
                  </span>
                </div>
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>
    <AppFooter class="mt-5" />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import { ref } from 'vue';

export default {
  name: 'OthersView',
  components: {
    NavBar,
    AppFooter
  },
  setup() {
    const links = ref([
      {
        title: 'TradingView World Economy',
        description: 'Global economic indicators, banking charts, interest rates, and financial datasets in interactive formats.',
        url: 'https://www.tradingview.com/markets/world-economy/charts-banking-finance',
        icon: '📊',
        category: 'Market Charts'
      },
      {
        title: 'Central Bank Watch',
        description: 'Track rate probability charts, interest rate decisions, meeting schedules, and historical data across major central banks.',
        url: 'https://centralbank.watch/',
        icon: '🏛️',
        category: 'Monetary Policy'
      },
      {
        title: 'Real Interest Rates Tracker',
        description: 'Compare inflation-adjusted interest rates across major economies to see the true cost of borrowing.',
        url: 'https://centralbank.watch/tools/real-interest-rates/',
        icon: '📈',
        category: 'Monetary Policy'
      },
      {
        title: 'Recession Probability Tool',
        description: 'Gauge potential economic downturn risks using quantitative models and yield-based forecast probabilities.',
        url: 'https://centralbank.watch/tools/recession-probability/',
        icon: '🚨',
        category: 'Economic Indicators'
      },
      {
        title: 'Yield Curve Visualization',
        description: 'Interact with and track sovereign yield curves to identify economic cycle expansion and inversion phases.',
        url: 'https://centralbank.watch/tools/yield-curve/',
        icon: '📉',
        category: 'Market Charts'
      },
      {
        title: 'Global Inflation Tracker',
        description: 'Monitor consumer price index changes (CPI), core inflation rates, and price level trajectories worldwide.',
        url: 'https://centralbank.watch/tools/inflation-tracker/',
        icon: '💸',
        category: 'Economic Indicators'
      },
      {
        title: 'Mortgage Rates Comparison',
        description: 'Follow residential and commercial mortgage rates to analyze real estate debt markets and consumer health.',
        url: 'https://centralbank.watch/tools/mortgage-rates/',
        icon: '🏠',
        category: 'Real Estate'
      },
      {
        title: 'Macro Economic Calendar',
        description: 'Never miss high-impact monetary policy statements, job reports, GDP data, and major global macro events.',
        url: 'https://centralbank.watch/tools/economic-calendar/',
        icon: '📅',
        category: 'Calendar'
      }
    ]);

    const getDomain = (url) => {
      try {
        const parsed = new URL(url);
        return parsed.hostname.replace('www.', '');
      } catch (e) {
        return url;
      }
    };

    return {
      links,
      getDomain
    };
  }
};
</script>

<style scoped>
.resource-card-link {
  text-decoration: none;
  display: block;
  height: 100%;
}

.resource-card {
  border-radius: 12px;
  background-color: #ffffff;
  border: 1px solid #e2e8f0 !important;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}

.resource-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(49, 130, 206, 0.1) !important;
  border-color: #3182ce !important;
}

.resource-icon {
  font-size: 2rem;
  line-height: 1;
}

.resource-title {
  color: #2d3748 !important;
  font-size: 1.15rem;
  transition: color 0.2s;
}

.resource-card:hover .resource-title {
  color: #3182ce !important;
}

.resource-desc {
  font-size: 0.9rem;
  color: #4a5568 !important;
  line-height: 1.5;
}

.btn-visit {
  font-size: 0.85rem;
  font-weight: 600;
  color: #3182ce;
  transition: all 0.2s;
}

.resource-card:hover .btn-visit {
  color: #2b6cb0;
  text-decoration: underline;
}
</style>
