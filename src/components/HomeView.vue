<template>
  <div id="home-view-root" class="d-flex flex-column min-vh-100">
    <notifications />
    
    <div class="home-view container flex-grow-1 pt-4 pb-5">
      <!-- Economic Calendar Section -->
      <div class="mb-5">
        <div class="stk-panel" style="border-bottom-left-radius: 0; border-bottom-right-radius: 0; margin-bottom: 0;">
          <div class="stk-header d-flex justify-content-between align-items-center flex-wrap gap-3">
            <div class="d-flex align-items-center gap-3">
              <div class="stk-header__icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              </div>
              <div>
                <h2 class="stk-header__title">Economic Calendar</h2>
                <p class="stk-header__sub">Track macro events and economic indicators impact</p>
              </div>
            </div>
            
            <div class="d-flex gap-2 align-items-center">
              <button class="stk-btn stk-btn--outline py-2 px-3" @click="goToPreviousDay" :disabled="isPreviousDisabled">&lt; Previous</button>
              <div class="position-relative" style="min-width: 150px;">
                <!-- Styled visual placeholder matching calendar aesthetic -->
                <div class="stk-input py-2 px-3 d-flex align-items-center justify-content-between" style="font-size: 0.85rem; pointer-events: none; background: rgba(10, 13, 20, 0.8); border: 1px solid rgba(255, 255, 255, 0.12); color: #ffffff;">
                  <span class="fw-semibold">{{ formatInputDate(selectedDate) }}</span>
                  <i class="bi bi-calendar3 text-cyan" style="font-size: 0.9rem; color: #00f2fe;"></i>
                </div>
                <!-- Hidden native date input sitting on top -->
                <input 
                  type="date" 
                  id="dateFilter" 
                  v-model="selectedDate" 
                  style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; z-index: 2;"
                >
              </div>
              <button class="stk-btn stk-btn--outline py-2 px-3" @click="goToNextDay" :disabled="isNextDisabled">Next &gt;</button>
            </div>
          </div>
          
          <div class="px-4 py-2 border-top d-flex justify-content-between align-items-center flex-wrap gap-2 text-start" style="font-weight: 700; color: #94a3b8; font-size: 0.85rem; background-color: rgba(10, 13, 20, 0.6); border-color: rgba(255, 255, 255, 0.08) !important;">
            <div class="d-flex align-items-center gap-2 flex-wrap">
              <span>📅 Selected: {{ formattedDateLong }}</span>
              <span v-if="sortedCalendarData.length > 6 && isCalendarCollapsed" class="badge bg-info bg-opacity-10 text-cyan border border-info border-opacity-25 px-2 py-1" style="font-size: 0.72rem; font-weight: 600;">
                <i class="bi bi-funnel me-1"></i>Tập trung: {{ displayCalendarData.length }}/{{ sortedCalendarData.length }} sự kiện (Hiện tại & Sắp tới)
              </span>
            </div>

            <!-- Collapse / Expand Toggle Button -->
            <button 
              v-if="sortedCalendarData.length > 6"
              @click="toggleCalendarCollapse"
              class="btn btn-sm d-inline-flex align-items-center gap-1 px-3 py-1 text-nowrap"
              :style="isCalendarCollapsed 
                ? 'background: rgba(0, 242, 254, 0.12); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.35); border-radius: 20px; font-size: 0.78rem; font-weight: 600;' 
                : 'background: rgba(255, 255, 255, 0.08); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 20px; font-size: 0.78rem; font-weight: 600;'"
              :title="isCalendarCollapsed ? 'Mở rộng hiển thị tất cả sự kiện trong ngày' : 'Thu gọn tập trung sự kiện hiện tại và sắp tới'"
            >
              <i :class="isCalendarCollapsed ? 'bi bi-arrows-expand' : 'bi bi-arrows-collapse'"></i>
              <span>{{ isCalendarCollapsed ? `Mở rộng (Xem tất cả ${sortedCalendarData.length} sự kiện)` : 'Thu gọn (Tập trung)' }}</span>
            </button>
          </div>
        </div>

        <div v-if="isLoadingCalendar" class="stk-loading py-5 rounded-bottom-4" style="background: rgba(18, 24, 38, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); border-top: none;">
          <div class="stk-spinner"></div>
        </div>
        
        <div v-else>
          <div class="stk-panel border-top-0 rounded-top-0" v-if="sortedCalendarData.length > 0" style="margin-bottom: 0;">
            <div class="stk-table-wrap" style="border: none; border-radius: 0 0 16px 16px;">
              <table class="stk-table">
                <thead>
                  <tr>
                    <th class="stk-th">Date</th>
                    <th class="stk-th">Country</th>
                    <th class="stk-th">Title</th>
                    <th class="stk-th">Impact</th>
                    <th class="stk-th stk-th--right">Forecast</th>
                    <th class="stk-th stk-th--right">Actual</th>
                    <th class="stk-th stk-th--right">Previous</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in displayCalendarData" :key="item.date + item.title" :class="{ 'stk-row--active': item === closestCalendarItem }" class="stk-row">
                    <td class="stk-td">{{ formatCalendarDate(item.date) }}</td>
                    <td class="stk-td"><strong>{{ item.country }}</strong></td>
                    <td class="stk-td" style="text-align: left;"><strong>{{ item.title }}</strong></td>
                    <td class="stk-td">
                      <span class="stk-signal" :class="'stk-signal--' + String(item.impact).toLowerCase()">
                        {{ item.impact }}
                      </span>
                    </td>
                    <td class="stk-td stk-td--right">{{ item.forecast || '-' }}</td>
                    <td class="stk-td stk-td--right">
                      <span v-if="item.actual" class="stk-val-badge" :class="getActualBadgeClass(item)">
                        {{ item.actual }}
                      </span>
                      <span v-else class="text-muted" style="font-size: 0.78rem;">—</span>
                    </td>
                    <td class="stk-td stk-td--right">{{ item.previous }}</td>
                  </tr>
                </tbody>
              </table>

              <!-- Footer expand hint when collapsed -->
              <div v-if="isCalendarCollapsed && sortedCalendarData.length > displayCalendarData.length" class="text-center py-2 border-top" style="background: rgba(10, 13, 20, 0.4); border-color: rgba(255, 255, 255, 0.06) !important;">
                <button @click="toggleCalendarCollapse" class="btn btn-link btn-sm text-cyan text-decoration-none py-0 d-inline-flex align-items-center gap-1" style="color: #00f2fe; font-size: 0.8rem; font-weight: 500;">
                  <i class="bi bi-chevron-down"></i>
                  <span>Xem thêm {{ sortedCalendarData.length - displayCalendarData.length }} sự kiện khác trong ngày</span>
                </button>
              </div>
            </div>
          </div>
          <div v-else class="stk-message p-5 border border-top-0 rounded-bottom-4 text-center" style="background: rgba(18, 24, 38, 0.75); border-color: rgba(255, 255, 255, 0.08) !important; color: #94a3b8;">
            No economic events scheduled for this day.
          </div>
        </div>
      </div>

      <!-- Live Trade - Vị Thế Đang Mở (Live Trades) Section -->
      <div class="mb-5">
        <div class="stk-panel p-0 overflow-hidden">
          <div class="panel-header-glass py-3 px-4 d-flex justify-content-between align-items-center flex-wrap gap-3 border-bottom border-glass">
            <div class="d-flex align-items-center gap-3">
              <div class="stk-header__icon" style="background: rgba(0, 242, 254, 0.15); color: #00f2fe;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
              </div>
              <div>
                <div class="d-flex align-items-center gap-2 flex-wrap">
                  <h3 class="stk-header__title m-0">Live Trade</h3>
                  <span class="badge-tag-mini">QUANT LIVE</span>
                </div>
                <p class="stk-header__sub m-0">Vị thế phá vỡ mức giá xác định & chiến lược nhồi lệnh Pyramiding tự động</p>
              </div>
            </div>

            <!-- Stats & Quick Actions -->
            <div class="d-flex align-items-center gap-2 flex-wrap">
              <div class="live-pnl-summary d-flex align-items-center gap-2 px-3 py-2 rounded-3" v-if="breakoutOpenPositions.length > 0">
                <span class="text-muted small">Live PnL:</span>
                <span :class="totalUnrealizedBreakout >= 0 ? 'text-neon-green fw-bold' : 'text-neon-red fw-bold'">
                  {{ totalUnrealizedBreakout >= 0 ? '+' : '' }}{{ formatCurrency(totalUnrealizedBreakout) }}
                  ({{ avgRoiBreakout >= 0 ? '+' : '' }}{{ avgRoiBreakout.toFixed(2) }}%)
                </span>
              </div>
              
              <button 
                class="stk-btn stk-btn--outline d-flex align-items-center gap-1 py-2 px-3 rounded-3 text-cyan border-cyan" 
                style="font-size: 0.82rem; font-weight: 600;"
                @click="router.push('/breakout-radar')"
                title="Mở toàn bộ Live Trade"
              >
                <span>Quản Lý Live Trade</span>
                <i class="fa-solid fa-arrow-up-right-from-square ms-1" style="font-size: 0.75rem;"></i>
              </button>

              <button 
                class="stk-btn stk-btn--outline d-flex align-items-center justify-content-center p-2 rounded-3" 
                @click="fetchBreakoutPositions" 
                :disabled="loadingBreakout"
                title="Làm mới vị thế"
              >
                <i class="fa-solid fa-rotate-right" :class="{ 'spinning': loadingBreakout }" style="font-size: 0.85rem;"></i>
              </button>
            </div>
          </div>

          <!-- Loading state -->
          <div v-if="loadingBreakout && isInitialBreakoutLoad" class="stk-loading py-5 text-center">
            <div class="stk-spinner"></div>
            <p class="text-muted small mt-2">Đang tải danh sách vị thế Live Trade...</p>
          </div>

          <!-- Empty state -->
          <div v-else-if="breakoutOpenPositions.length === 0" class="p-5 text-center" style="background: rgba(18, 24, 38, 0.5);">
            <div style="font-size: 2rem; margin-bottom: 8px;">📡</div>
            <h5 class="fw-bold mb-2 text-white" style="font-size: 1rem;">Chưa có vị thế phá đỉnh nào đang mở</h5>
            <p class="text-muted mb-3 mx-auto" style="max-width: 480px; font-size: 0.85rem;">
              Hệ thống tự động theo dõi danh sách Watchlist và kích hoạt vị thế ngay khi giá vượt qua mức kháng cự / ATH.
            </p>
            <button class="stk-btn stk-btn--primary py-2 px-4" @click="router.push('/breakout-radar')">
              Xem Danh Sách Watchlist & Live Trade
            </button>
          </div>

          <!-- Live Positions Table -->
          <div v-else class="stk-table-wrap p-0">
            <table class="stk-table">
              <thead>
                <tr>
                  <th class="stk-th">Tài Sản</th>
                  <th class="stk-th">Thị Trường</th>
                  <th class="stk-th">Tiến Trình Nhồi</th>
                  <th class="stk-th stk-th--right">Giá Vào / Hòa Vốn</th>
                  <th class="stk-th stk-th--right">Giá Hiện Tại</th>
                  <th class="stk-th">Cắt Lỗ (SL)</th>
                  <th class="stk-th">Điểm Nhồi Kế</th>
                  <th class="stk-th stk-th--right">PnL ($)</th>
                  <th class="stk-th stk-th--right">ROI (%)</th>
                  <th class="stk-th text-center">Hành Động</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="pos in breakoutOpenPositions" 
                  :key="pos.id"
                  class="stk-row cursor-pointer"
                  @click="selectBreakoutSymbolForChart(pos)"
                  title="Nhấn để tải biểu đồ xuống khung Chart bên dưới"
                >
                  <td class="stk-td">
                    <div class="d-flex align-items-center gap-2">
                      <span class="fw-bold text-white sym-hover-link">{{ pos.symbol }}</span>
                      <span class="badge-mini-chart" title="Xem biểu đồ">📊</span>
                    </div>
                  </td>
                  <td class="stk-td">
                    <span class="asset-badge-mini" :class="'badge-' + pos.asset_type">
                      {{ formatAssetType(pos.asset_type) }}
                    </span>
                  </td>
                  <td class="stk-td">
                    <div class="d-flex align-items-center gap-2">
                      <span class="badge-layer">Tầng {{ pos.current_layer }}/3</span>
                      <div class="mini-layer-progress">
                        <div class="mini-layer-fill" :style="{ width: (pos.current_layer / 3 * 100) + '%' }"></div>
                      </div>
                    </div>
                  </td>
                  <td class="stk-td stk-td--right font-monospace">
                    <div class="d-flex flex-column align-items-end">
                      <span class="text-white">{{ formatPrice(pos.avg_entry_price, pos.asset_type) }}</span>
                      <span class="small" :class="pos.current_price >= (pos.breakeven_price || pos.avg_entry_price * (1 + (pos.spread_pct || 0.1)/100)) ? 'text-neon-green fw-bold' : 'text-muted'" style="font-size: 0.72rem;" :title="'Giá hòa vốn sau phí/spread ' + (pos.spread_pct || 0.1) + '%'">
                        HV: {{ formatPrice(pos.breakeven_price || pos.avg_entry_price * (1 + (pos.spread_pct || 0.1)/100), pos.asset_type) }}
                      </span>
                    </div>
                  </td>
                  <td class="stk-td stk-td--right font-monospace text-cyan fw-bold">
                    {{ formatPrice(pos.current_price, pos.asset_type) }}
                  </td>
                  <td class="stk-td">
                    <span class="text-neon-red font-monospace fw-semibold">
                      {{ formatPrice(pos.stop_loss_price, pos.asset_type) }}
                    </span>
                  </td>
                  <td class="stk-td">
                    <span v-if="pos.current_layer < 3" class="text-gold font-monospace fw-semibold">
                      {{ formatPrice(pos.next_pyramid_price, pos.asset_type) }}
                    </span>
                    <span v-else class="text-gold small fw-bold">🏆 Max 3 Tầng</span>
                  </td>
                  <td class="stk-td stk-td--right">
                    <span :class="pos.unrealized_pnl >= 0 ? 'text-neon-green fw-bold' : 'text-neon-red fw-bold'">
                      {{ pos.unrealized_pnl >= 0 ? '+' : '' }}{{ formatCurrency(pos.unrealized_pnl) }}
                    </span>
                  </td>
                  <td class="stk-td stk-td--right">
                    <span class="stk-val-badge" :class="pos.unrealized_roi_pct >= 0 ? 'stk-val-badge--up' : 'stk-val-badge--down'">
                      {{ pos.unrealized_roi_pct >= 0 ? '+' : '' }}{{ pos.unrealized_roi_pct.toFixed(2) }}%
                    </span>
                  </td>
                  <td class="stk-td text-center" @click.stop>
                    <button 
                      class="btn-chart-quick btn-radar-link" 
                      @click="router.push('/breakout-radar')"
                      title="Mở trang Quản lý Live Trade"
                    >
                      <span>Live Trade</span>
                      <i class="fa-solid fa-arrow-up-right-from-square ms-1" style="font-size: 0.68rem;"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Interactive Charts Hub (TradingView & VN Stock) -->
      <div id="interactive-charts-hub" class="mb-5">
        <div class="stk-panel p-0 overflow-hidden">
          <!-- Header with Tabs and Search Bar -->
          <div class="chart-hub-header py-3 px-4 d-flex justify-content-between align-items-center flex-wrap gap-3">
            <div class="d-flex align-items-center gap-3 flex-wrap">
              <div class="chart-tab-pills d-flex align-items-center p-1 rounded-3">
                <button 
                  class="chart-tab-btn" 
                  :class="{ active: activeChartTab === 'tradingview' }"
                  @click="activeChartTab = 'tradingview'"
                >
                  <i class="bi bi-graph-up me-1"></i> TradingView
                </button>
                <button 
                  class="chart-tab-btn" 
                  :class="{ active: activeChartTab === 'vnstock' }"
                  @click="activeChartTab = 'vnstock'"
                >
                  <i class="bi bi-building me-1"></i> VN Stock (Vietstock)
                </button>
              </div>
            </div>

            <!-- Search bar & controls for active tab -->
            <div class="d-flex align-items-center gap-2 flex-grow-1 justify-content-end" style="max-width: 520px;">
              <template v-if="activeChartTab === 'tradingview'">
                <div class="position-relative flex-grow-1">
                  <input 
                    type="text"
                    class="form-control chart-symbol-input"
                    v-model="tvSymbolInput"
                    @keydown.enter="updateTvChart"
                    @input="tvSymbolInput = $event.target.value.toUpperCase()"
                    placeholder="Nhập mã (VD: XAUUSD, BTCUSDT, WTI, BRENT, DXY, US10Y, NVDA...)"
                  />
                </div>
                <button class="stk-btn stk-btn--primary px-3 py-2 text-nowrap" @click="updateTvChart" :disabled="!tvSymbolInput.trim()">
                  <i class="bi bi-search me-1"></i> Xem Chart
                </button>
              </template>
              
              <template v-else>
                <div class="position-relative flex-grow-1">
                  <input 
                    type="text"
                    class="form-control chart-symbol-input"
                    v-model="vnSymbolInput"
                    @keydown.enter="updateVnChart"
                    @input="vnSymbolInput = $event.target.value.toUpperCase()"
                    placeholder="Nhập mã CK VN (VD: VNINDEX, FPT, VCB, HPG, SSI...)"
                  />
                </div>
                <button class="stk-btn stk-btn--primary px-3 py-2 text-nowrap" @click="updateVnChart" :disabled="!vnSymbolInput.trim()">
                  <i class="bi bi-search me-1"></i> Xem Chart
                </button>
              </template>
            </div>
          </div>

          <!-- Quick pick chips row -->
          <div class="chart-quick-chips px-4 py-2 d-flex align-items-center gap-2 flex-wrap border-top border-glass">
            <span class="text-muted small fw-semibold me-1" style="font-size: 0.75rem;">Phổ biến:</span>
            <template v-if="activeChartTab === 'tradingview'">
              <button 
                v-for="sym in ['XAUUSD', 'BTCUSDT', 'WTI', 'BRENT', 'DXY', 'US10Y', 'NIKKEI225', 'KOSPI', 'SHANGHAI', 'VNINDEX', 'FTSE', 'DAX', 'SPX', 'NVDA']" 
                :key="sym"
                class="quick-chip-btn"
                :class="{ active: currentTvSymbol === sym }"
                @click="setTvQuickSymbol(sym)"
              >
                {{ sym }}
              </button>
            </template>
            <template v-else>
              <button 
                v-for="sym in ['VNINDEX', 'VN30', 'VN30FM1', 'HNXINDEX', 'UPCOMINDEX', 'FPT', 'VCB', 'HPG', 'SSI', 'VHM', 'TCB', 'MWG']" 
                :key="sym"
                class="quick-chip-btn"
                :class="{ active: currentVnSymbol === sym }"
                @click="setVnQuickSymbol(sym)"
              >
                {{ sym }}
              </button>
            </template>
          </div>

          <!-- Chart Body Display -->
          <div class="chart-hub-body">
            <div v-show="activeChartTab === 'tradingview'" class="tradingview-wrapper">
              <TradingViewChart :key="currentTvSymbol" :coin="currentTvSymbol" :height="560" />
            </div>
            
            <div v-show="activeChartTab === 'vnstock'" class="vietstock-wrapper">
              <iframe
                :key="currentVnSymbol"
                :src="`https://stockchart.vietstock.vn/?stockcode=${resolveVnStockCode(currentVnSymbol)}`"
                width="100%"
                height="560"
                frameborder="0"
                allowfullscreen
                style="display: block; border: none; background: #ffffff;"
              ></iframe>
            </div>
          </div>
        </div>
      </div>

      <!-- Insights Area -->
      <div class="row g-4 mb-4">
        <!-- Unified Column: Platform Intelligence & Current World State -->
        <div class="col-lg-12">
          <div class="feature-panel p-4">
            <h3 class="panel-heading mb-4 d-flex align-items-center justify-content-between flex-wrap gap-2 w-100">
              <span class="d-flex align-items-center gap-2">
                <span>🧠</span> Platform Intelligence
              </span>
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <button 
                  class="stk-btn stk-btn--outline d-flex align-items-center gap-1 py-1 px-2 rounded-3 text-info border-info" 
                  style="font-size: 0.75rem; font-weight: 600;"
                  @click="openPromptModal"
                  title="Chỉnh sửa AI Prompt Template"
                >
                  <i class="fa-solid fa-pen-to-square" style="font-size: 0.85rem;"></i>
                  <span>Sửa Prompt AI</span>
                </button>
                <button 
                  class="stk-btn stk-btn--outline d-flex align-items-center gap-1 py-1 px-2 rounded-3 text-success border-success" 
                  style="font-size: 0.75rem; font-weight: 600;"
                  @click="runAIAnalysis"
                  :disabled="loadingTheses || runningAI"
                  title="Yêu cầu AI phân tích tin tức và cập nhật nhận định mới nhất"
                >
                  <i v-if="!runningAI" class="fa-solid fa-microchip" style="font-size: 0.85rem;"></i>
                  <span v-else class="spinner-border spinner-border-sm text-success" role="status" style="width: 0.85rem; height: 0.85rem; border-width: 1.5px;"></span>
                  <span>Chạy phân tích AI mới nhất</span>
                </button>
                <button 
                  class="stk-btn stk-btn--outline d-flex align-items-center gap-1 py-1 px-2 rounded-3" 
                  style="font-size: 0.75rem; font-weight: 600;"
                  @click="refreshThesesManual"
                  :disabled="loadingTheses"
                  title="Làm mới nhận định (Bỏ qua cache)"
                >
                  <i v-if="!loadingTheses" class="fa-solid fa-rotate-right" style="font-size: 0.85rem;"></i>
                  <span v-else class="spinner-border spinner-border-sm" role="status" style="width: 0.85rem; height: 0.85rem; border-width: 1.5px;"></span>
                  <span>Refresh</span>
                </button>
              </div>

            </h3>

            <div v-if="loadingTheses" class="text-center py-5">
              <div class="spinner-border text-info" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p class="mt-3 text-muted small" style="color: #94a3b8 !important;">AI đang tổng hợp và phân tích dữ liệu...</p>
            </div>
            
            <div v-else-if="macroTheses && macroTheses.length > 0" class="theses-container mb-4" style="padding-right: 5px;">
              <div class="thesis-card p-4 rounded-4" style="background: linear-gradient(145deg, rgba(0, 242, 254, 0.05) 0%, rgba(18, 24, 38, 0.9) 100%); border: 1px solid rgba(0, 242, 254, 0.2); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);">
                <div class="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom" style="border-color: rgba(255, 255, 255, 0.08) !important;">
                  <div class="confidence-badge" :class="getConfidenceClass(macroTheses[0].confidence)">
                    <span class="confidence-dot"></span>
                    <span>ĐỘ TIN CẬY: {{ (macroTheses[0].confidence * 100).toFixed(0) }}%</span>
                  </div>
                  <span class="small fw-medium" style="color: #94a3b8;"><i class="bi bi-clock-history me-1"></i>Cập nhật: {{ formatDateWithOffset(macroTheses[0].updated_at) }}</span>
                </div>
                
                <div>
                  <h5 class="feature-title fw-bold mb-3 d-flex align-items-center" style="color: #00f2fe;"><span class="fs-4 me-2">🌍</span> Tổng hợp Vĩ mô:</h5>
                  <div class="feature-desc mb-4" style="font-size: 0.95rem; line-height: 1.7; text-align: justify; color: #e2e8f0;" v-html="formatThesisText(macroTheses[0].thesis)"></div>
                  
                  <h5 class="feature-title text-success fw-bold mb-3 d-flex align-items-center mt-4"><span class="fs-4 me-2">🛡️</span> Tư vấn Danh mục:</h5>
                  <div class="feature-desc mb-0 p-3 rounded-3" style="font-size: 0.95rem; line-height: 1.7; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-left: 4px solid #10b981; color: #e2e8f0;" v-html="formatThesisText(macroTheses[0].supporting_evidence)"></div>

                  <!-- Ask AI Button linked with Telegram DB and Chat -->
                  <div class="d-flex justify-content-end mt-4 pt-3 border-top" style="border-color: rgba(255, 255, 255, 0.08) !important;">
                    <button 
                      class="stk-btn stk-btn--outline d-flex align-items-center gap-2 py-2 px-4" 
                      style="font-size: 0.85rem; font-weight: 600;"
                      @click="askAIAboutThesis(macroTheses[0])"
                      :disabled="isAskingAI"
                    >
                      <span v-if="isAskingAI" class="spinner-border spinner-border-sm me-1" role="status"></span>
                      <span v-else>💬</span>
                      Ask AI
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="theses-container mb-4">
              <div class="thesis-card p-3 rounded-3" style="background: rgba(18, 24, 38, 0.75); border: 1px solid rgba(255, 255, 255, 0.08);">
                <h5 class="feature-title fw-bold mb-2" style="color: #00f2fe;"><span class="me-2">🌍</span> Nhận định Vĩ mô hiện tại:</h5>
                <p class="feature-desc mb-3" style="font-size: 0.85rem; color: #94a3b8;">AI đang phân tích các luồng tin tức từ ngân hàng trung ương và thị trường tài chính để đưa ra nhận định vĩ mô mới nhất.</p>
                
                <h5 class="feature-title text-success fw-bold mb-2"><span class="me-2">🛡️</span> Chuẩn bị tài sản:</h5>
                <p class="feature-desc mb-0" style="font-size: 0.85rem; color: #94a3b8;">Danh mục sẽ được tự động gợi ý điều chỉnh dựa trên rủi ro thanh khoản toàn cầu. (Đang chờ dữ liệu từ DB...)</p>
              </div>
            </div>

            <!-- Current World State Toggle & Component (OSINT) -->
            <div class="mt-4 pt-4 border-top" style="border-color: rgba(255, 255, 255, 0.08) !important;">
              <div 
                class="d-flex justify-content-between align-items-center cursor-pointer" 
                style="cursor: pointer;"
                @click="isWorldStateExpanded = !isWorldStateExpanded"
              >
                <h5 class="feature-title fw-bold mb-0 d-flex align-items-center gap-2" style="font-size: 0.95rem; color: #00f2fe;">
                  <span>🌐</span> Current World State (OSINT)
                </h5>
                <div class="d-flex align-items-center gap-1 fw-semibold" style="font-size: 0.82rem; user-select: none; color: #00f2fe;">
                  <span>{{ isWorldStateExpanded ? 'Collapse' : 'Expand' }}</span>
                  <span :style="{ display: 'inline-block', transform: isWorldStateExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }">▼</span>
                </div>
              </div>
              
              <div v-if="isWorldStateExpanded" class="mt-4">
                <WorldStateComponent :worldState="worldState" :loading="loadingState" :borderless="true" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- RRG Section Row -->
      <div class="row mb-5">
        <div class="col-12">
          <div class="feature-panel p-0 overflow-hidden">
            <div class="panel-header-glass py-3 px-4 d-flex justify-content-between align-items-center border-bottom border-glass">
              <h3 class="panel-heading m-0 d-flex align-items-center gap-2">
                <span>🔄</span> Sector Rotation Graph (RRG)
              </h3>
              <button
                class="btn-generate d-flex align-items-center gap-2"
                @click="runSSHScript('assets_rrg')"
                :disabled="isRunningScript"
              >
                <span v-if="isRunningScript" class="spinner-border spinner-border-sm"></span>
                <span v-else style="display: inline-flex; align-items: center; gap: 6px;">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                  Generate RRG
                </span>
              </button>
            </div>
            
            <div class="p-4 text-center">
              <div class="rrg-frame position-relative mx-auto rounded-4 overflow-hidden shadow-lg border border-glass">
                <img :src="assetsRRGUrl" class="img-fluid rrg-image" alt="Assets RRG Chart" />
                <div class="rrg-frame-overlay"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Prompt Template Modal -->
    <AIPromptModal 
      v-model="showPromptModal" 
      @run-analysis="runAIAnalysis" 
    />

    <AppFooter />
  </div>
</template>

<script>
import AppFooter  from './AppFooter.vue';
import WorldStateComponent from './MacroIntelHub/WorldState.vue';
import AIPromptModal from './AIPromptModal.vue';
import TradingViewChart from './TradingViewChart.vue';
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useNotification } from "@kyvg/vue3-notification";
import { parseMarkdown } from '@/utils/markdown';

export default {
  name: 'HomeView',
  components: {
    AppFooter,
    WorldStateComponent,
    AIPromptModal,
    TradingViewChart,
  },
  setup() {
    const router = useRouter();
    const { notify } = useNotification();
    const isRunningScript = ref(false);
    const assetsRRGKey = ref(Date.now());
    const assetsRRGUrl = computed(() => `/assets_rrgchart?t=${assetsRRGKey.value}`);
    
    // Economic Calendar state
    const calendarData = ref([]);
    const isLoadingCalendar = ref(false);
    const calendarCurrentDateTime = ref(new Date());

    const today = new Date();
    const formattedToday = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
    const selectedDate = ref(formattedToday);

    const sortedCalendarData = computed(() => {
      let filteredData = [...calendarData.value];

      if (selectedDate.value) {
        const selected = new Date(selectedDate.value);
        filteredData = filteredData.filter(item => {
          const itemDate = new Date(item.date);
          return itemDate.getFullYear() === selected.getFullYear() &&
                 itemDate.getMonth() === selected.getMonth() &&
                 itemDate.getDate() === selected.getDate();
        });
      }

      return filteredData.sort((a, b) => new Date(a.date) - new Date(b.date));
    });

    const isCalendarCollapsed = ref(true);
    const toggleCalendarCollapse = () => {
      isCalendarCollapsed.value = !isCalendarCollapsed.value;
    };

    const displayCalendarData = computed(() => {
      const all = sortedCalendarData.value;
      if (!isCalendarCollapsed.value || all.length <= 6) {
        return all;
      }
      const now = calendarCurrentDateTime.value.getTime();
      // Find index of first event scheduled around now or near future (within last 20 mins or upcoming)
      const upcomingIdx = all.findIndex(item => new Date(item.date).getTime() >= now - 20 * 60 * 1000);
      
      if (upcomingIdx === -1) {
        // If all events of the day already completed, focus on the last 5 events
        return all.slice(-5);
      }
      // Include 1 event right before now for immediate historical context, plus upcoming events (total 5-6)
      const start = Math.max(0, upcomingIdx - 1);
      const end = Math.min(all.length, start + 6);
      return all.slice(start, end);
    });

    const formatCalendarDate = (dateString) => {
      const date = new Date(dateString);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const month = months[date.getMonth()];
      const day = String(date.getDate()).padStart(2, '0');
      const year = date.getFullYear();
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${month} ${day}, ${year} ${hours}:${minutes}`;
    };

    const formatInputDate = (dateStr) => {
      if (!dateStr) return '';
      const parts = dateStr.split('-');
      if (parts.length !== 3) return dateStr;
      const year = parts[0];
      const monthIndex = parseInt(parts[1], 10) - 1;
      const day = parts[2];
      
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const monthName = months[monthIndex] || '';
      const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const date = new Date(year, monthIndex, day);
      const dayOfWeek = daysOfWeek[date.getDay()];
      return `${dayOfWeek}, ${monthName} ${day}, ${year}`;
    };

    const formattedDateLong = computed(() => {
      if (!selectedDate.value) return '';
      const parts = selectedDate.value.split('-');
      if (parts.length !== 3) return selectedDate.value;
      const date = new Date(parts[0], parts[1] - 1, parts[2]);
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    });

    const closestCalendarItem = computed(() => {
      if (sortedCalendarData.value.length === 0) {
        return null;
      }
      
      const now = calendarCurrentDateTime.value.getTime();
      let closest = null;
      let minDiff = Infinity;

      sortedCalendarData.value.forEach(item => {
        const itemTime = new Date(item.date).getTime();
        const diff = Math.abs(itemTime - now);
        if (diff < minDiff) {
          minDiff = diff;
          closest = item;
        }
      });

      return closest;
    });

    const isPreviousDisabled = computed(() => false);
    const isNextDisabled = computed(() => false);

    const goToPreviousDay = () => {
      if (!selectedDate.value) return;
      const date = new Date(selectedDate.value);
      date.setDate(date.getDate() - 1);
      selectedDate.value = date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0') + '-' + String(date.getDate()).padStart(2, '0');
    };

    const goToNextDay = () => {
      if (!selectedDate.value) return;
      const date = new Date(selectedDate.value);
      date.setDate(date.getDate() + 1);
      selectedDate.value = date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0') + '-' + String(date.getDate()).padStart(2, '0');
    };

    const parseNum = (str) => {
      if (!str) return null;
      const clean = String(str).replace(/[^\d.-]/g, '');
      const num = parseFloat(clean);
      return Number.isFinite(num) ? num : null;
    };

    const getActualBadgeClass = (item) => {
      if (!item || !item.actual) return '';
      if (item.forecast) {
        const a = parseNum(item.actual);
        const f = parseNum(item.forecast);
        if (a !== null && f !== null) {
          if (a > f) return 'stk-val-badge--up';
          if (a < f) return 'stk-val-badge--down';
        }
      }
      return 'stk-val-badge--neutral';
    };

    const fetchCalendarData = async (isSilent = false) => {
      if (!isSilent) {
        isLoadingCalendar.value = true;
      }
      try {
        let loaded = false;
        try {
          const response = await fetch('/api/economic-calendar');
          if (response.ok) {
            const data = await response.json();
            if (Array.isArray(data) && data.length > 0) {
              calendarData.value = data;
              loaded = true;
            }
          }
        } catch (e) {
          console.warn('API /api/economic-calendar fallback...', e);
        }

        if (!loaded && (!calendarData.value || calendarData.value.length === 0)) {
          const response = await fetch('/ff_calendar_thisweek.json');
          if (response.ok) {
            calendarData.value = await response.json();
          }
        }
      } catch (error) {
        console.error('Error fetching calendar data:', error);
      } finally {
        if (!isSilent) {
          isLoadingCalendar.value = false;
        }
      }
    };

    let calendarInterval = null;
    let calendarPollInterval = null;
    const macroTheses = ref([]);
    const loadingTheses = ref(true);
    let thesesInterval = null;

    // Breakout Radar Live Positions state
    const breakoutPositions = ref([]);
    const loadingBreakout = ref(false);
    const isInitialBreakoutLoad = ref(true);
    let breakoutInterval = null;

    const breakoutOpenPositions = computed(() => {
      return breakoutPositions.value.filter(p => p.status === 'OPEN');
    });

    const totalInvestedBreakout = computed(() => {
      return breakoutOpenPositions.value.reduce((sum, p) => sum + (p.total_invested || 0), 0);
    });

    const totalUnrealizedBreakout = computed(() => {
      return breakoutOpenPositions.value.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0);
    });

    const avgRoiBreakout = computed(() => {
      if (breakoutOpenPositions.value.length === 0) return 0;
      const sum = breakoutOpenPositions.value.reduce((s, p) => s + (p.unrealized_roi_pct || 0), 0);
      return sum / breakoutOpenPositions.value.length;
    });

    const fetchBreakoutPositions = async () => {
      loadingBreakout.value = true;
      try {
        const res = await fetch('/breakout/positions');
        if (res.ok) {
          const data = await res.json();
          breakoutPositions.value = data || [];
        }
      } catch (err) {
        console.error('Error fetching breakout positions in HomeView:', err);
      } finally {
        loadingBreakout.value = false;
        isInitialBreakoutLoad.value = false;
      }
    };

    onMounted(() => {
      fetchMacroTheses();
      fetchWorldState();
      fetchCalendarData();
      fetchBreakoutPositions();

      // Auto refresh theses + world state every 5 minutes (300,000ms)
      thesesInterval = setInterval(() => {
        fetchMacroTheses();
        fetchWorldState();
      }, 300000);
      
      // Update local time clock every 1 second for active event highlight
      calendarInterval = setInterval(() => {
        calendarCurrentDateTime.value = new Date();
      }, 1000);

      // Auto refresh economic calendar actual data silently every 30 seconds
      calendarPollInterval = setInterval(() => {
        fetchCalendarData(true);
      }, 30000);

      // Auto refresh breakout positions every 10s for real-time tracking
      breakoutInterval = setInterval(() => {
        fetchBreakoutPositions();
      }, 10000);
    });

    const fetchMacroTheses = async (forceRefresh = false) => {
      loadingTheses.value = true;
      try {
        const token = localStorage.getItem('token');
        let userId = '';
        try {
          const userInfoStr = localStorage.getItem('userInfo');
          if (userInfoStr) {
            const userInfo = JSON.parse(userInfoStr);
            userId = userInfo.id || userInfo.user_id || userInfo.userId || '';
          }
        } catch (e) {
          console.error('Error parsing userInfo', e);
        }
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        let url = '/api/osint/theses';
        const params = [];
        if (userId) {
          params.push(`user_id=${userId}`);
        }
        if (forceRefresh) {
          params.push('refresh=true');
        }
        if (params.length > 0) {
          url += `?${params.join('&')}`;
        }
        const response = await fetch(url, { headers });
        if (response.ok) {
          const data = await response.json();
          macroTheses.value = data || [];
        }
      } catch (error) {
        console.error('Error fetching theses:', error);
      } finally {
        loadingTheses.value = false;
      }
    };

    const runningAI = ref(false);
    const runAIAnalysis = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        router.push({ name: 'Login' });
        return;
      }
      runningAI.value = true;
      try {
        const response = await fetch('/api/osint/theses/trigger', {
          method: 'POST'
        });
        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          alert(errData.message || 'Lỗi khi chạy phân tích AI');
        } else {
          // Re-fetch macro theses after successful update
          await fetchMacroTheses(true);
          await fetchWorldState();
          alert('Cập nhật nhận định vĩ mô thành công!');
        }
      } catch (error) {
        console.error('Error running AI analysis:', error);
        alert('Lỗi kết nối khi chạy phân tích AI');
      } finally {
        runningAI.value = false;
      }
    };

    const showPromptModal = ref(false);
    const openPromptModal = () => {
      const token = localStorage.getItem('token');
      if (!token) {
        router.push({ name: 'Login' });
        return;
      }
      showPromptModal.value = true;
    };

    const refreshThesesManual = () => {
      fetchMacroTheses(true);
      fetchWorldState();
    };

    onUnmounted(() => {
      if (calendarInterval) {
        clearInterval(calendarInterval);
      }
      if (calendarPollInterval) {
        clearInterval(calendarPollInterval);
      }
      if (thesesInterval) {
        clearInterval(thesesInterval);
      }
      if (breakoutInterval) {
        clearInterval(breakoutInterval);
      }
    });

    const runSSHScript = async (scriptType) => {
      isRunningScript.value = true;
      try {
        const response = await fetch('/runSSHScript', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ script_type: scriptType }),
        });
        const data = await response.json();
        if (response.ok && data.success) {
          notify({
            type: 'success',
            title: 'Success',
            text: 'Assets RRG Chart has been updated successfully!',
          });
          assetsRRGKey.value = Date.now();
        } else {
          throw new Error(data.error || 'Server returned an error');
        }
      } catch (error) {
        console.error('Error running SSH script:', error);
        notify({
          type: 'error',
          title: 'Execution Failed',
          text: error.message || 'Failed to connect or run the SSH script.',
        });
      } finally {
        isRunningScript.value = false;
      }
    };



    const isLoggedIn = ref(!!localStorage.getItem('token'));

    const worldState = ref({});
    const loadingState = ref(false);
    const isWorldStateExpanded = ref(false);

    const authHeader = () => {
      const token = localStorage.getItem('token');
      return token ? { 'Authorization': `Bearer ${token}` } : {};
    };

    const fetchWorldState = () => {
      loadingState.value = true;
      fetch('/api/osint/world-state', { headers: authHeader() })
        .then(r => r.json())
        .then(data => worldState.value = data || {})
        .catch(e => console.error('fetchWorldState error:', e))
        .finally(() => loadingState.value = false);
    };

    const isAskingAI = ref(false);

    const formatWorldStateContext = (ws) => {
      if (!ws || Object.keys(ws).length === 0) return "";
      let text = "";
      for (const [entity, fields] of Object.entries(ws)) {
        if (typeof fields === 'object' && fields !== null) {
          const fieldEntries = Object.entries(fields)
            .map(([k, v]) => `${k}: ${v}`)
            .join(' | ');
          text += `• ${entity}: ${fieldEntries}\n`;
        } else {
          text += `• ${entity}: ${fields}\n`;
        }
      }
      return text.trim();
    };

    const fetchPortfolioContext = async () => {
      const token = localStorage.getItem('token');
      if (!token) return "";
      try {
        const accRes = await fetch('/dnse-order-service/accounts', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!accRes.ok) return "";
        const accData = await accRes.json();
        const accountId = accData.default?.id || accData.accounts?.[0]?.id;
        if (!accountId) return "";

        let summary = `Tài khoản DNSE: ${accountId}\n`;

        // Fetch balance
        try {
          const balRes = await fetch(`/dnse-order-service/account-balances/${accountId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (balRes.ok) {
            const bal = await balRes.json();
            const nav = bal.netAssetValue || bal.totalAsset || 0;
            const cash = bal.cash || bal.purchasingPower || 0;
            const stockVal = bal.stockValue || (nav - cash) || 0;
            summary += `- Tổng tài sản (NAV): ${Number(nav).toLocaleString('vi-VN')} VND\n`;
            summary += `- Tiền mặt khả dụng: ${Number(cash).toLocaleString('vi-VN')} VND\n`;
            summary += `- Giá trị danh mục CP: ${Number(stockVal).toLocaleString('vi-VN')} VND\n`;
          }
        } catch (e) {
          console.warn('Balance fetch error:', e);
        }

        // Fetch deals (open positions)
        try {
          const dealsRes = await fetch(`/dnse-deal-service/deals?accountNo=${accountId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (dealsRes.ok) {
            const dealsData = await dealsRes.json();
            const deals = dealsData.deals || [];
            if (deals.length > 0) {
              summary += `- Danh sách cổ phiếu đang nắm giữ (${deals.length} mã):\n`;
              for (const deal of deals) {
                const sym = deal.symbol || deal.stockCode;
                const qty = deal.quantity || deal.closedQuantity || 0;
                const cost = deal.costPrice || deal.price || 0;
                const cur = deal.marketPrice || deal.currentPrice || cost;
                const pnlPct = deal.unrealizedProfitRatio !== undefined ? (deal.unrealizedProfitRatio * 100).toFixed(2) : ((cur - cost) / (cost || 1) * 100).toFixed(2);
                const pnlVal = deal.unrealizedProfit || ((cur - cost) * qty);
                summary += `  + ${sym}: KL ${Number(qty).toLocaleString('vi-VN')} CP | Giá vốn: ${Number(cost).toLocaleString('vi-VN')} | Giá HT: ${Number(cur).toLocaleString('vi-VN')} | Lãi/Lỗ: ${pnlPct}% (${Number(pnlVal).toLocaleString('vi-VN')} VND)\n`;
              }
            } else {
              summary += `- Hiện tại tài khoản đang nắm giữ 100% tiền mặt, chưa có vị thế cổ phiếu.\n`;
            }
          }
        } catch (e) {
          console.warn('Deals fetch error:', e);
        }

        return summary.trim();
      } catch (err) {
        console.warn('Error building portfolio context:', err);
        return "";
      }
    };

    const askAIAboutThesis = async (thesis) => {
      isAskingAI.value = true;
      try {
        // 1. Fetch Telegram news
        let telegramContext = "";
        try {
          const response = await fetch('/api/news/telegram');
          if (response.ok) {
            const data = await response.json();
            const channels = data.channels || [];
            const news = data.news || {};
            for (const channel of channels) {
              const items = news[channel] || [];
              if (items.length > 0) {
                telegramContext += `Kênh ${channel}:\n`;
                for (let i = 0; i < Math.min(items.length, 3); i++) {
                  const descClean = items[i].description ? items[i].description.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').substring(0, 150) : "";
                  telegramContext += `- [${new Date(items[i].date_published).toLocaleDateString('vi-VN')}] ${items[i].title}: ${descClean}\n`;
                }
                telegramContext += `\n`;
              }
            }
          }
        } catch (e) {
          console.warn('Telegram news fetch error:', e);
        }

        // 2. Fetch World State if empty
        if (!worldState.value || Object.keys(worldState.value).length === 0) {
          try {
            const wsRes = await fetch('/api/osint/world-state', { headers: authHeader() });
            if (wsRes.ok) worldState.value = await wsRes.json();
          } catch (e) {
            console.warn('World state fetch error:', e);
          }
        }
        const worldStateContext = formatWorldStateContext(worldState.value);

        // 3. Fetch Portfolio context
        const portfolioContext = await fetchPortfolioContext();

        // 4. Dispatch open-chat-with-context
        window.dispatchEvent(new CustomEvent('open-chat-with-context', {
          detail: {
            thesis: thesis ? thesis.thesis : '',
            advice: thesis ? thesis.supporting_evidence : '',
            worldStateContext: worldStateContext,
            portfolioContext: portfolioContext,
            telegramContext: telegramContext.trim()
          }
        }));
      } catch (error) {
        console.error('Error in askAIAboutThesis:', error);
      } finally {
        isAskingAI.value = false;
      }
    };

    const formatDateWithOffset = (dateString) => {
      if (!dateString) return '';
      try {
        const d = new Date(dateString);
        const formatted = d.toLocaleString(undefined, {
          year: 'numeric',
          month: 'numeric',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
        
        // Calculate dynamic timezone offset string
        const offset = -d.getTimezoneOffset();
        const sign = offset >= 0 ? '+' : '-';
        const hours = Math.floor(Math.abs(offset) / 60);
        const minutes = Math.abs(offset) % 60;
        const minutesStr = minutes > 0 ? `:${String(minutes).padStart(2, '0')}` : '';
        const offsetStr = `(UTC${sign}${hours}${minutesStr})`;
        
        return `${formatted} ${offsetStr}`;
      } catch (e) {
        return dateString;
      }
    };

    const formatThesisText = (text) => {
      if (!text) return '';
      // Preprocess to insert newlines before list items of form "**Item**:"
      let formatted = text.replace(/\s+(\*\*[^*]+\*\*:)/g, '\n$1');
      return parseMarkdown(formatted);
    };

    const getConfidenceClass = (conf) => {
      const val = parseFloat(conf || 0);
      if (val >= 0.75) return 'confidence-high';
      if (val >= 0.5) return 'confidence-med';
      return 'confidence-low';
    };

    // Chart section state
    const activeChartTab = ref('tradingview'); // 'tradingview' | 'vnstock'
    const tvSymbolInput = ref('XAUUSD');
    const currentTvSymbol = ref('XAUUSD');

    const vnSymbolInput = ref('VNINDEX');
    const currentVnSymbol = ref('VNINDEX');

    const updateTvChart = () => {
      if (tvSymbolInput.value && tvSymbolInput.value.trim()) {
        currentTvSymbol.value = tvSymbolInput.value.trim().toUpperCase();
      }
    };

    const setTvQuickSymbol = (sym) => {
      tvSymbolInput.value = sym;
      currentTvSymbol.value = sym;
    };

    const updateVnChart = () => {
      if (vnSymbolInput.value && vnSymbolInput.value.trim()) {
        currentVnSymbol.value = vnSymbolInput.value.trim().toUpperCase();
      }
    };

    const setVnQuickSymbol = (sym) => {
      vnSymbolInput.value = sym;
      currentVnSymbol.value = sym;
    };

    const resolveVnStockCode = (code) => {
      const upper = String(code || '').trim().toUpperCase();
      if (upper === 'VN30FM1') return 'VN30F1M';
      if (upper === 'UPCOMINDEX') return 'UPCOM';
      return upper;
    };

    const selectBreakoutSymbolForChart = (pos) => {
      if (!pos) return;
      const sym = pos.symbol;
      const type = pos.asset_type;
      
      if (type === 'stock_vn') {
        activeChartTab.value = 'vnstock';
        vnSymbolInput.value = sym;
        currentVnSymbol.value = sym;
      } else {
        activeChartTab.value = 'tradingview';
        tvSymbolInput.value = sym;
        
        if (type === 'futures' && sym.toUpperCase().endsWith('USDT')) {
          currentTvSymbol.value = `BINANCE:${sym}.P`;
        } else if (type === 'crypto' && sym.toUpperCase().endsWith('USDT')) {
          currentTvSymbol.value = `BINANCE:${sym}`;
        } else if (type === 'commodity') {
          const comMap = {
            'GC=F': 'OANDA:XAUUSD',
            'XAUUSD': 'OANDA:XAUUSD',
            'SI=F': 'OANDA:XAGUSD',
            'XAGUSD': 'OANDA:XAGUSD',
            'CL=F': 'TVC:USOIL',
            'BZ=F': 'TVC:UKOIL'
          };
          currentTvSymbol.value = comMap[sym.toUpperCase()] || sym;
        } else if (type === 'forex') {
          currentTvSymbol.value = sym.toUpperCase() === 'USDVND' ? 'USDVND' : `FX:${sym}`;
        } else {
          currentTvSymbol.value = sym;
        }
      }

      // Smooth scroll to charts hub
      const hubEl = document.getElementById('interactive-charts-hub');
      if (hubEl) {
        hubEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    };

    const formatPrice = (price, assetType) => {
      if (!price && price !== 0) return '--';
      if (assetType === 'stock_vn') {
        return price.toLocaleString('vi-VN') + 'đ';
      }
      return '$' + Number(price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
    };

    const formatCurrency = (val) => {
      if (!val && val !== 0) return '$0.00';
      return '$' + Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };

    const formatAssetType = (type) => {
      const map = {
        'crypto': 'Crypto Spot',
        'futures': 'Futures',
        'stock_vn': 'Stock VN',
        'stock_us': 'Stock US',
        'commodity': 'Commodity',
        'forex': 'Forex'
      };
      return map[type] || type;
    };

    return {
      router,
      formatDateWithOffset,
      isRunningScript,
      assetsRRGUrl,
      runSSHScript,
      macroTheses,
      loadingTheses,
      isLoggedIn,
      worldState,
      loadingState,
      isWorldStateExpanded,
      resolveVnStockCode,
      calendarData,
      isLoadingCalendar,
      selectedDate,
      sortedCalendarData,
      isCalendarCollapsed,
      toggleCalendarCollapse,
      displayCalendarData,
      formatCalendarDate,
      formattedDateLong,
      isAskingAI,
      askAIAboutThesis,
      formatThesisText,
      closestCalendarItem,
      isPreviousDisabled,
      isNextDisabled,
      goToPreviousDay,
      goToNextDay,
      refreshThesesManual,
      formatInputDate,
      runningAI,
      runAIAnalysis,
      showPromptModal,
      openPromptModal,
      getActualBadgeClass,
      getConfidenceClass,
      activeChartTab,
      tvSymbolInput,
      currentTvSymbol,
      vnSymbolInput,
      currentVnSymbol,
      updateTvChart,
      setTvQuickSymbol,
      updateVnChart,
      setVnQuickSymbol,
      // Breakout Radar returns
      breakoutPositions,
      loadingBreakout,
      isInitialBreakoutLoad,
      breakoutOpenPositions,
      totalInvestedBreakout,
      totalUnrealizedBreakout,
      avgRoiBreakout,
      fetchBreakoutPositions,
      selectBreakoutSymbolForChart,
      formatPrice,
      formatCurrency,
      formatAssetType
    };
  }
}
</script>

<style scoped>
/* ── Confidence Badge ────────────────────────────────── */
.confidence-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.95rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  backdrop-filter: blur(8px);
  transition: all 0.25s ease;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
}

.confidence-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
  animation: pulseDot 2s infinite ease-in-out;
}

@keyframes pulseDot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}

.confidence-high {
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: #34d399;
}
.confidence-high .confidence-dot {
  background: #34d399;
}

.confidence-med {
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.35);
  color: #38bdf8;
}
.confidence-med .confidence-dot {
  background: #38bdf8;
}

.confidence-low {
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.35);
  color: #fbbf24;
}
.confidence-low .confidence-dot {
  background: #fbbf24;
}

/* ============================== */
/*  HOME PAGE – Dark Cyber UI     */
/* ============================== */

.home-view-wrapper {
  background: #0a0d14;
  color: #e2e8f0;
  min-height: 100vh;
}

/* ── Hero Section ────────────────────────────────────── */
.hero-section {
  background: linear-gradient(135deg, rgba(18, 24, 38, 0.85) 0%, rgba(10, 13, 20, 0.95) 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.hero-glow-1 {
  position: absolute;
  top: -100px;
  left: 25%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(0, 242, 254, 0.1) 0%, transparent 70%);
  filter: blur(60px);
}
.hero-glow-2 {
  position: absolute;
  top: -50px;
  right: 25%;
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(79, 172, 254, 0.08) 0%, transparent 70%);
  filter: blur(50px);
}
.hero-badge {
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.3);
  color: #00f2fe;
  font-weight: 700;
  letter-spacing: 0.5px;
  font-size: 0.72rem;
  border-radius: 999px;
  display: inline-block;
}
.hero-title {
  font-family: 'Outfit', sans-serif;
  font-weight: 900;
  font-size: 2.6rem;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #ffffff 0%, #00f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero-subtitle {
  font-size: 1.05rem;
  color: #94a3b8;
  max-width: 680px;
  line-height: 1.6;
}

/* ── Buttons ─────────────────────────────────────────── */
.btn-glow {
  padding: 11px 24px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.92rem;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.btn-glow--primary {
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  color: #0a0d14;
  box-shadow: 0 4px 20px rgba(0, 242, 254, 0.35);
}
.btn-glow--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 242, 254, 0.5);
  color: #0a0d14;
}
.btn-glow--secondary {
  background: rgba(255, 255, 255, 0.04);
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.btn-glow--secondary:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(0, 242, 254, 0.3);
  transform: translateY(-2px);
  color: #ffffff;
}

/* ── Market Grid ─────────────────────────────────────── */
.market-card-link {
  text-decoration: none;
  color: inherit;
  display: block;
}
.market-card {
  background: rgba(18, 24, 38, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(12px);
}
.market-card:hover {
  transform: translateY(-4px);
  border-color: rgba(0, 242, 254, 0.4);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4), 0 0 15px rgba(0, 242, 254, 0.2);
}
.market-card__icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
}
.market-card__change {
  font-weight: 700;
  font-size: 0.8rem;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.04);
}
.text-neon-green {
  color: #00f5a0;
  text-shadow: 0 0 8px rgba(0, 245, 160, 0.4);
}
.text-neon-red {
  color: #ff4b72;
  text-shadow: 0 0 8px rgba(255, 75, 114, 0.4);
}
.market-card__title {
  font-size: 0.82rem;
  font-weight: 700;
  color: #94a3b8;
  margin-bottom: 4px;
}
.market-card__price {
  font-size: 1.25rem;
  font-weight: 800;
  color: #ffffff;
}
.market-card__sparkline {
  height: 30px;
}
.sparkline-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

/* ── Group & Marquee ─────────────────────────────────── */
.group-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.25rem;
  font-weight: 800;
  color: #ffffff;
}

.marquee-container {
  overflow: hidden;
  white-space: nowrap;
  display: flex;
  width: 100%;
  position: relative;
}
.marquee-content {
  display: flex;
  width: max-content;
  height: 100%;
  animation: marquee-left linear infinite;
}
.marquee-track {
  display: flex;
  height: 100%;
  gap: 1.5rem;
  padding-right: 1.5rem;
}
.market-card-wrapper {
  width: 280px;
  flex-shrink: 0;
  white-space: normal;
}
@keyframes marquee-left {
  0% {
    transform: translateX(0%);
  }
  100% {
    transform: translateX(-50%);
  }
}

/* ── Panels ─────────────────────────────────────────── */
.feature-panel {
  background: rgba(18, 24, 38, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(16px);
}
.panel-heading {
  font-family: 'Outfit', sans-serif;
  font-size: 1.2rem;
  font-weight: 800;
  color: #ffffff;
  margin: 0;
}
.feature-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  flex-shrink: 0;
}
.bg-blue { background: rgba(0, 242, 254, 0.12); color: #00f2fe; }
.bg-green { background: rgba(0, 245, 160, 0.12); color: #00f5a0; }
.bg-gold { background: rgba(246, 211, 101, 0.12); color: #f6d365; }

.feature-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 2px;
}
.feature-desc {
  font-size: 0.85rem;
  color: #94a3b8;
  line-height: 1.6;
}

/* ── RRG Section ─────────────────────────────────────── */
.panel-header-glass {
  background: rgba(10, 13, 20, 0.6);
}
.border-bottom {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}
.btn-generate {
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  color: #0a0d14;
  border: none;
  padding: 6px 16px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(0, 242, 254, 0.3);
}
.btn-generate:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(0, 242, 254, 0.5);
}
.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rrg-frame {
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  background: rgba(18, 24, 38, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}
.rrg-image {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.rrg-frame:hover .rrg-image {
  transform: scale(1.015);
}
.border-glass {
  border-color: rgba(255, 255, 255, 0.08) !important;
}

/* ── Modal ───────────────────────────────────────────── */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(6px);
}
.custom-modal {
  background: #111726;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16px 40px rgba(0,0,0,0.6);
}
.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(10, 13, 20, 0.8);
}
.modal-title-text {
  font-family: 'Outfit', sans-serif;
  font-weight: 800;
  color: #ffffff;
  font-size: 1.1rem;
}
.modal-symbol-bar {
  display: flex;
  gap: 10px;
  padding: 12px 1.5rem;
  background: rgba(18, 24, 38, 0.6);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  align-items: center;
}
.modal-input-group {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
}
.modal-search-icon {
  position: absolute;
  left: 12px;
  color: #94a3b8;
  pointer-events: none;
}
.modal-symbol-input {
  width: 100%;
  padding: 9px 14px 9px 38px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 600;
  color: #ffffff;
  background: rgba(10, 13, 20, 0.8);
  outline: none;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}
.modal-symbol-input:focus {
  border-color: #00f2fe;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15);
}
.modal-symbol-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  color: #0a0d14;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 242, 254, 0.3);
  transition: all 0.2s ease;
  white-space: nowrap;
}
.modal-symbol-btn:hover:not(:disabled) {
  box-shadow: 0 4px 14px rgba(0, 242, 254, 0.5);
  transform: translateY(-1px);
}
.modal-symbol-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.modal-body {
  padding: 0;
  overflow-y: auto;
}

/* ---------- ECONOMIC CALENDAR STYLES ---------- */
.stk-panel {
  background: rgba(18, 24, 38, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  overflow: hidden;
  margin-bottom: 20px;
  backdrop-filter: blur(16px);
}
.stk-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 22px 24px;
  background: rgba(10, 13, 20, 0.6);
  color: #ffffff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.stk-header__icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #00f2fe;
}
.stk-header__title {
  font-size: 1.25rem;
  font-weight: 800;
  margin: 0;
  line-height: 1.3;
  font-family: 'Outfit', sans-serif;
  color: #ffffff;
}
.stk-header__sub {
  font-size: 0.82rem;
  color: #94a3b8;
  margin: 2px 0 0;
}
.stk-section {
  padding: 20px 24px;
}
.stk-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: #94a3b8;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
.stk-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  font-size: 0.85rem;
  color: #ffffff;
  background: rgba(10, 13, 20, 0.8);
  transition: all 0.2s;
  outline: none;
}
.stk-input:focus {
  border-color: #00f2fe;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15);
}
.stk-table-wrap {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  background: rgba(18, 24, 38, 0.6);
}
.stk-table-wrap::-webkit-scrollbar {
  height: 6px;
}
.stk-table-wrap::-webkit-scrollbar-track {
  background: rgba(10, 13, 20, 0.6);
  border-radius: 4px;
}
.stk-table-wrap::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}
.stk-table-wrap::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 242, 254, 0.4);
}
.stk-table {
  width: 100%;
  min-width: 900px;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.stk-th {
  padding: 12px 14px;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
  background: rgba(10, 13, 20, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  z-index: 2;
  white-space: nowrap;
}
.stk-th--right { text-align: right; }
.stk-row {
  cursor: pointer;
  transition: background 0.15s ease;
}
.stk-row:hover {
  background: rgba(255, 255, 255, 0.03);
}
.stk-row--active {
  background: rgba(0, 242, 254, 0.08) !important;
  border-left: 3px solid #00f2fe;
}
.stk-td {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  vertical-align: middle;
  color: #e2e8f0;
  white-space: nowrap;
}
.stk-td--right { text-align: right; }
.stk-signal {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  white-space: nowrap;
}
.stk-signal--low { background: rgba(0, 245, 160, 0.12); color: #00f5a0; border: 1px solid rgba(0, 245, 160, 0.3); }
.stk-signal--medium { background: rgba(246, 211, 101, 0.12); color: #f6d365; border: 1px solid rgba(246, 211, 101, 0.3); }
.stk-signal--high { background: rgba(255, 75, 114, 0.12); color: #ff4b72; border: 1px solid rgba(255, 75, 114, 0.3); box-shadow: 0 0 8px rgba(255, 75, 114, 0.2); }
.stk-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 18px;
  border: none;
  border-radius: 8px;
  font-size: 0.84rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}
.stk-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.stk-btn--outline {
  background: rgba(255, 255, 255, 0.04);
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.stk-btn--outline:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(0, 242, 254, 0.3);
}
.stk-loading { display: flex; justify-content: center; padding: 20px 0; }
.stk-spinner { width: 32px; height: 32px; border: 3px solid rgba(255, 255, 255, 0.1); border-top-color: #00f2fe; border-radius: 50%; animation: stk-spin 0.7s linear infinite; }
@keyframes stk-spin { to { transform: rotate(360deg); } }
.stk-message { text-align: center; font-size: 0.85rem; color: #94a3b8; padding: 10px 0; margin: 0; }

/* Mini Scale Marquee Styling */
.group-title--mini {
  font-size: 0.82rem !important;
  color: #94a3b8 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.market-card-wrapper--mini {
  width: 140px !important;
}
.marquee-track--mini {
  gap: 0.5rem !important;
  padding-right: 0.5rem !important;
}
.market-card--mini {
  padding: 6px 10px !important;
  border-radius: 8px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  background: rgba(18, 24, 38, 0.75) !important;
}
.market-card--mini .market-card__icon {
  width: 18px !important;
  height: 18px !important;
  font-size: 0.7rem !important;
  border-radius: 4px !important;
}
.market-card--mini .market-card__change {
  font-size: 0.55rem !important;
  padding: 0.5px 4px !important;
}
.market-card--mini .market-card__title {
  font-size: 0.65rem !important;
  margin-bottom: 1px !important;
  color: #94a3b8;
}
.market-card--mini .market-card__price {
  font-size: 0.75rem !important;
  font-weight: 800 !important;
  color: #ffffff;
}
.market-card--mini .market-card__time {
  font-size: 0.52rem !important;
  line-height: 0.8rem !important;
  height: 0.8rem !important;
  margin-top: 1px !important;
  color: #64748b !important;
}
.market-card--mini .market-card__sparkline {
  height: 12px !important;
  margin-top: 4px !important;
}

.thesis-card :deep(.ai-list-item) {
  list-style-type: none;
  position: relative;
  padding-left: 1.25rem;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
  line-height: 1.7;
}
.thesis-card :deep(.ai-list-item::before) {
  content: "•";
  color: #00f2fe;
  font-weight: bold;
  display: inline-block;
  width: 1rem;
  margin-left: -1rem;
  position: absolute;
  left: 0.25rem;
}

/* Custom Horizontal Scroll styling */
.custom-horizontal-scroll::-webkit-scrollbar {
  height: 6px;
}
.custom-horizontal-scroll::-webkit-scrollbar-track {
  background: rgba(10, 13, 20, 0.8);
  border-radius: 4px;
}
.custom-horizontal-scroll::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 4px;
  transition: background 0.2s;
}
.custom-horizontal-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 242, 254, 0.4);
}

/* Marquee Navigation Buttons */
.marquee-nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(18, 24, 38, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  opacity: 0;
  pointer-events: none;
}
.position-relative:hover .marquee-nav-btn {
  opacity: 1;
  pointer-events: auto;
}
.marquee-nav-btn:hover {
  background: #00f2fe;
  color: #0a0d14;
  border-color: #00f2fe;
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.4);
  transform: translateY(-50%) scale(1.12);
}
.marquee-nav-btn:active {
  transform: translateY(-50%) scale(0.95);
}
.marquee-nav-btn--left {
  left: 8px;
}
.marquee-nav-btn--right {
  right: 8px;
}

/* Ensure horizontal scroll hides default ugly browser scrollbars but allows our custom one */
.custom-horizontal-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.12) transparent;
}

/* Separator between loop cycles in marquee */
.marquee-separator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  flex-shrink: 0;
  height: 48px;
  align-self: center;
}
.marquee-separator-line {
  width: 2px;
  height: 100%;
  background: linear-gradient(to bottom, transparent, rgba(0, 242, 254, 0.3) 20%, rgba(0, 242, 254, 0.3) 80%, transparent);
  border-radius: 99px;
  position: relative;
}
.marquee-separator-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 6px;
  height: 6px;
  background-color: #00f2fe;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(0, 242, 254, 0.6);
}

/* Economic Calendar Actual Value Badges */
.stk-val-badge {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: 0.76rem;
  font-weight: 700;
  white-space: nowrap;
}
.stk-val-badge--up {
  background: rgba(0, 245, 160, 0.15);
  color: #00f5a0;
  border: 1px solid rgba(0, 245, 160, 0.35);
  box-shadow: 0 0 8px rgba(0, 245, 160, 0.2);
}
.stk-val-badge--down {
  background: rgba(255, 75, 114, 0.15);
  color: #ff4b72;
  border: 1px solid rgba(255, 75, 114, 0.35);
  box-shadow: 0 0 8px rgba(255, 75, 114, 0.2);
}
.stk-val-badge--neutral {
  background: rgba(0, 242, 254, 0.12);
  color: #00f2fe;
  border: 1px solid rgba(0, 242, 254, 0.3);
}

/* ── Interactive Charts Hub ─────────────────────────────── */
.chart-hub-header {
  background: rgba(10, 13, 20, 0.85);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.chart-tab-pills {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  gap: 4px;
}

.chart-tab-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 0.45rem 1rem;
  border-radius: 8px;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
}

.chart-tab-btn:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.05);
}

.chart-tab-btn.active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.2) 0%, rgba(79, 172, 254, 0.12) 100%);
  color: #00f2fe;
  box-shadow: 0 0 14px rgba(0, 242, 254, 0.2);
  border: 1px solid rgba(0, 242, 254, 0.35);
}

.chart-symbol-input {
  background: rgba(8, 12, 20, 0.85) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  color: #00f2fe !important;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-weight: 700;
  font-size: 0.88rem;
  padding: 0.5rem 0.85rem;
  border-radius: 8px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.4);
  transition: all 0.2s ease;
}

.chart-symbol-input:focus {
  border-color: #00f2fe !important;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.4), 0 0 0 3px rgba(0, 242, 254, 0.15) !important;
  outline: none;
}

.chart-symbol-input::placeholder {
  color: #64748b;
  font-weight: 400;
  font-size: 0.8rem;
}

.chart-quick-chips {
  background: rgba(10, 13, 20, 0.6);
}

.quick-chip-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.09);
  color: #94a3b8;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'JetBrains Mono', Consolas, monospace;
}

.quick-chip-btn:hover {
  background: rgba(0, 242, 254, 0.1);
  border-color: rgba(0, 242, 254, 0.35);
  color: #00f2fe;
  transform: translateY(-1px);
}

.quick-chip-btn.active {
  background: rgba(0, 242, 254, 0.18);
  border-color: #00f2fe;
  color: #00f2fe;
  box-shadow: 0 0 8px rgba(0, 242, 254, 0.3);
}

.chart-hub-body {
  background: #080c14;
  min-height: 560px;
}

.tradingview-wrapper, .vietstock-wrapper {
  width: 100%;
  height: 560px;
  position: relative;
}

/* ── Breakout Radar Section Styles ─────────────────────── */
.badge-tag-mini {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.3);
  color: #00f2fe;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.6px;
}

.live-pnl-summary {
  background: rgba(10, 13, 20, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.sym-hover-link {
  transition: color 0.2s ease;
  font-size: 0.92rem;
}

.stk-row:hover .sym-hover-link {
  color: #00f2fe !important;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.badge-mini-chart {
  font-size: 0.8rem;
  opacity: 0.6;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.stk-row:hover .badge-mini-chart {
  opacity: 1;
  transform: scale(1.2);
}

.asset-badge-mini {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  white-space: nowrap;
  line-height: 1.2;
}

.badge-crypto { background: rgba(247, 147, 26, 0.15); color: #f7931a; }
.badge-futures { background: rgba(0, 242, 254, 0.15); color: #00f2fe; }
.badge-stock_vn { background: rgba(235, 77, 75, 0.15); color: #eb4d4b; }
.badge-stock_us { background: rgba(79, 172, 254, 0.15); color: #4facfe; }
.badge-commodity { background: rgba(246, 211, 101, 0.15); color: #f6d365; }
.badge-forex { background: rgba(162, 155, 254, 0.15); color: #a29bfe; }

.badge-layer {
  font-size: 0.75rem;
  font-weight: 700;
  color: #00f2fe;
  white-space: nowrap;
}

.mini-layer-progress {
  width: 50px;
  height: 5px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.mini-layer-fill {
  height: 100%;
  background: linear-gradient(90deg, #00f2fe, #00f5a0);
}

.btn-chart-quick {
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.25);
  color: #00f2fe;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn-chart-quick:hover {
  background: rgba(0, 242, 254, 0.25);
  border-color: #00f2fe;
  transform: translateY(-1px);
}

.btn-radar-link {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
  color: #94a3b8;
}

.btn-radar-link:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.25);
}

.text-cyan { color: #00f2fe !important; }
.border-cyan { border-color: rgba(0, 242, 254, 0.3) !important; }
.text-neon-green { color: #10b981 !important; }
.text-neon-red { color: #ef4444 !important; }
.text-gold { color: #f6d365 !important; }

.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ========================================================== */
/*  RESPONSIVE STYLES (Smartphones & Tablets)                 */
/* ========================================================== */
@media (max-width: 991px) {
  .home-view {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
  }
  
  .chart-hub-header {
    flex-direction: column;
    align-items: stretch !important;
    gap: 12px !important;
    padding: 14px 16px !important;
  }

  .chart-hub-header .d-flex.justify-content-end {
    max-width: 100% !important;
    justify-content: stretch !important;
  }

  .stk-header {
    padding: 16px !important;
  }

  .stk-header__title {
    font-size: 1.2rem !important;
  }
}

@media (max-width: 768px) {
  .home-view {
    padding-left: 10px !important;
    padding-right: 10px !important;
  }

  .stk-panel {
    border-radius: 12px !important;
    margin-bottom: 1.5rem !important;
  }

  .stk-header {
    flex-direction: column;
    align-items: stretch !important;
    gap: 12px !important;
  }

  .stk-header > div:last-child {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .chart-tab-pills {
    width: 100%;
    display: flex;
  }

  .chart-tab-btn {
    flex: 1;
    text-align: center;
    font-size: 0.8rem !important;
    padding: 8px 6px !important;
  }

  .chart-quick-chips {
    padding: 8px 12px !important;
    overflow-x: auto;
    flex-wrap: nowrap !important;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .chart-quick-chips::-webkit-scrollbar {
    display: none;
  }

  .quick-chip-btn {
    flex-shrink: 0;
    font-size: 0.72rem !important;
    padding: 3px 8px !important;
  }

  .stk-table-wrap {
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch;
    border-radius: 0 0 12px 12px;
  }

  .stk-table {
    min-width: 900px;
    font-size: 0.82rem !important;
  }

  .stk-th, .stk-td {
    padding: 8px 10px !important;
  }

  .live-pnl-summary {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 576px) {
  .stk-header__title {
    font-size: 1.1rem !important;
  }
  
  .stk-header__sub {
    font-size: 0.78rem !important;
  }

  .chart-symbol-input {
    font-size: 0.8rem !important;
  }

  .stk-btn {
    font-size: 0.8rem !important;
    padding: 6px 12px !important;
  }
}
</style>
