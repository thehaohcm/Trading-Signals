<template>
  <div class="breakout-radar-wrapper">
    <NavBar />

    <div class="radar-container">
      <!-- Top Hero Header -->
      <div class="radar-header">
        <div class="radar-header-left">
          <div class="badge-tag">
            <span class="pulse-dot"></span>
            QUANT FORWARD-TESTING ENGINE
          </div>
          <h1 class="radar-title">
            <span class="gradient-text">Live Trade</span> & Pyramiding Radar
          </h1>
          <p class="radar-subtitle">
            Hệ thống tự động theo dõi phá vỡ mức giá Breakout, vào lệnh ảo $1,000, nhồi lệnh giảm dần (2/3) khi lãi & dời Stop-Loss bảo toàn vốn.
          </p>
        </div>

        <div class="radar-header-actions">
          <button @click="openAddModal" class="btn-action btn-primary-glow">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            <span>Thêm Mã Theo Dõi</span>
          </button>
          <button @click="fetchAllData" :disabled="loading" class="btn-action btn-secondary" title="Làm mới dữ liệu">
            <svg :class="{ 'spinning': loading }" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6"></path>
              <path d="M1 20v-6h6"></path>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- Live KPI Metrics Cards -->
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-icon metric-icon-cyan">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M2 12h5l3 5 4-10 3 5h5"></path>
            </svg>
          </div>
          <div class="metric-info">
            <span class="metric-label">Mã Theo Dõi Breakout</span>
            <span class="metric-value">{{ watchlist.length }}</span>
            <span class="metric-sub">{{ activeWatchlistCount }} đang quét tự động</span>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon metric-icon-green">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div class="metric-info">
            <span class="metric-label">Vị Thế Đang Mở (Live)</span>
            <span class="metric-value text-green">{{ openPositions.length }}</span>
            <span class="metric-sub">Tổng vốn: {{ formatCurrency(totalInvestedOpen) }}</span>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon" :class="totalUnrealizedPnL >= 0 ? 'metric-icon-green' : 'metric-icon-red'">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="1" x2="12" y2="23"></line>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
            </svg>
          </div>
          <div class="metric-info">
            <span class="metric-label">PnL Đang Chạy (Unrealized)</span>
            <span class="metric-value" :class="totalUnrealizedPnL >= 0 ? 'text-green' : 'text-red'">
              {{ totalUnrealizedPnL >= 0 ? '+' : '' }}{{ formatCurrency(totalUnrealizedPnL) }}
            </span>
            <span class="metric-sub" :class="avgOpenROI >= 0 ? 'text-green' : 'text-red'">
              ROI TB: {{ avgOpenROI >= 0 ? '+' : '' }}{{ avgOpenROI.toFixed(2) }}%
            </span>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon metric-icon-gold">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>
              <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>
              <path d="M4 22h16"></path>
              <path d="M10 14.66V17c0 .55-.45 1-1 1H7v2h10v-2h-2c-.55 0-1-.45-1-1v-2.34"></path>
              <path d="M18 2H6v7a6 6 0 0 0 12 0V2z"></path>
            </svg>
          </div>
          <div class="metric-info">
            <span class="metric-label">Tổng Lãi Đã Chốt (Realized)</span>
            <span class="metric-value" :class="totalRealizedPnL >= 0 ? 'text-green' : 'text-red'">
              {{ totalRealizedPnL >= 0 ? '+' : '' }}{{ formatCurrency(totalRealizedPnL) }}
            </span>
            <span class="metric-sub">Win Rate: {{ overallWinRate.toFixed(1) }}%</span>
          </div>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="radar-tabs-nav">
        <div class="tabs-group">
          <button 
            @click="activeTab = 'positions'" 
            class="tab-btn" 
            :class="{ 'tab-btn-active': activeTab === 'positions' }">
            <span class="tab-icon">⚡</span>
            <span>Live Trades</span>
            <span class="tab-badge" v-if="openPositions.length > 0">{{ openPositions.length }}</span>
          </button>

          <button 
            @click="activeTab = 'watchlist'" 
            class="tab-btn" 
            :class="{ 'tab-btn-active': activeTab === 'watchlist' }">
            <span class="tab-icon">🎯</span>
            <span>Watchlist & Giá Breakout</span>
            <span class="tab-badge-secondary">{{ watchlist.length }}</span>
          </button>

          <button 
            @click="activeTab = 'leaderboard'" 
            class="tab-btn" 
            :class="{ 'tab-btn-active': activeTab === 'leaderboard' }">
            <span class="tab-icon">🏆</span>
            <span>Bảng Xếp Hạng & Sức Mạnh RS</span>
          </button>

          <button 
            @click="activeTab = 'history'" 
            class="tab-btn" 
            :class="{ 'tab-btn-active': activeTab === 'history' }">
            <span class="tab-icon">📜</span>
            <span>Lịch Sử Giao Dịch</span>
            <span class="tab-badge-secondary">{{ closedPositions.length }}</span>
          </button>
        </div>

        <!-- Filter bar -->
        <div class="filter-group">
          <select v-model="selectedAssetFilter" class="custom-select">
            <option value="ALL">Tất cả lớp tài sản</option>
            <option value="crypto">Crypto Spot</option>
            <option value="futures">Crypto Futures</option>
            <option value="stock_vn">Cổ Phiếu VN</option>
            <option value="stock_us">Cổ Phiếu US</option>
            <option value="commodity">Hàng Hóa (Vàng, Dầu)</option>
            <option value="forex">Ngoại Hối (Forex)</option>
          </select>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading && isInitialLoad" class="loading-box">
        <div class="spinner"></div>
        <p>Đang đồng bộ dữ liệu giao dịch định lượng...</p>
      </div>

      <!-- TAB 1: LIVE POSITIONS -->
      <div v-else-if="activeTab === 'positions'" class="tab-content">
        <div v-if="filteredOpenPositions.length === 0" class="empty-card">
          <div class="empty-icon">📡</div>
          <h3>Chưa có vị thế phá đỉnh nào đang mở</h3>
          <p>Hệ thống tự động kích hoạt mua ảo $1000 ngay khi giá tài sản trong Watchlist vượt qua mức giá Breakout.</p>
          <button @click="activeTab = 'watchlist'" class="btn-action btn-primary-glow">Xem danh sách Watchlist</button>
        </div>

        <div v-else class="positions-grid">
          <div 
            v-for="pos in filteredOpenPositions" 
            :key="pos.id" 
            class="position-card"
            :class="{ 'card-profit': pos.unrealized_pnl >= 0, 'card-loss': pos.unrealized_pnl < 0 }">
            
            <!-- Card Header -->
            <div class="card-head">
              <div class="sym-block sym-clickable" @click="openChart(pos.symbol, pos.asset_type, pos.name)" title="Nhấn để xem biểu đồ TradingView / Vietstock">
                <span class="asset-badge" :class="'badge-' + pos.asset_type">
                  {{ formatAssetType(pos.asset_type) }}
                </span>
                <span class="sym-name">{{ pos.symbol }}</span>
                <span class="sym-chart-hint" title="Xem biểu đồ">📈</span>
              </div>
              <div class="pnl-pill" :class="pos.unrealized_pnl >= 0 ? 'pill-green' : 'pill-red'">
                {{ pos.unrealized_roi_pct >= 0 ? '+' : '' }}{{ pos.unrealized_roi_pct.toFixed(2) }}%
                <span class="pnl-usd">({{ pos.unrealized_pnl >= 0 ? '+' : '' }}{{ formatCurrency(pos.unrealized_pnl) }})</span>
              </div>
            </div>

            <!-- Prices Row -->
            <div class="price-stats-row">
              <div class="stat-col">
                <span class="col-lbl">Giá Hiện Tại</span>
                <span class="col-val val-highlight">{{ formatPrice(pos.current_price, pos.asset_type) }}</span>
              </div>
              <div class="stat-col">
                <span class="col-lbl">Giá Vốn TB</span>
                <span class="col-val">{{ formatPrice(pos.avg_entry_price, pos.asset_type) }}</span>
              </div>
              <div class="stat-col">
                <span class="col-lbl">Tổng Vốn Vào</span>
                <span class="col-val">{{ formatCurrency(pos.total_invested) }}</span>
              </div>
              <div class="stat-col">
                <span class="col-lbl">Đỉnh Cao Nhất</span>
                <span class="col-val text-gold">{{ formatPrice(pos.highest_price, pos.asset_type) }}</span>
              </div>
            </div>

            <!-- Pyramiding Steps Visualizer -->
            <div class="pyramid-tracker">
              <div class="tracker-header">
                <span class="tracker-title">Tiến Trình Nhồi Lệnh (Pyramiding)</span>
                <span class="tracker-layer">Tầng {{ pos.current_layer }} / 3</span>
              </div>
              <div class="tracker-steps">
                <div class="step-item" :class="{ 'step-active': pos.current_layer >= 1 }">
                  <div class="step-circle">1</div>
                  <div class="step-info">
                    <span class="step-name">Khởi tạo</span>
                    <span class="step-val">$1,000</span>
                  </div>
                </div>
                <div class="step-line" :class="{ 'line-active': pos.current_layer >= 2 }"></div>
                <div class="step-item" :class="{ 'step-active': pos.current_layer >= 2 }">
                  <div class="step-circle">2</div>
                  <div class="step-info">
                    <span class="step-name">Nhồi Đợt 1 (+5%)</span>
                    <span class="step-val">$670 (2/3)</span>
                  </div>
                </div>
                <div class="step-line" :class="{ 'line-active': pos.current_layer >= 3 }"></div>
                <div class="step-item" :class="{ 'step-active': pos.current_layer >= 3 }">
                  <div class="step-circle">3</div>
                  <div class="step-info">
                    <span class="step-name">Nhồi Đợt 2 (+10%)</span>
                    <span class="step-val">$449 (2/3)</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Risk Gauges: Stop Loss & Next Pyramid -->
            <div class="risk-bar-grid">
              <div class="risk-box sl-box">
                <div class="risk-box-header">
                  <span class="risk-lbl">🛑 Stop-Loss (Cắt Lỗ)</span>
                  <span class="risk-dist text-red">
                    {{ calculateDistancePct(pos.current_price, pos.stop_loss_price).toFixed(2) }}% cách SL
                  </span>
                </div>
                <span class="risk-price">{{ formatPrice(pos.stop_loss_price, pos.asset_type) }}</span>
              </div>

              <div class="risk-box pyramid-box" v-if="pos.current_layer < 3">
                <div class="risk-box-header">
                  <span class="risk-lbl">🚀 Điểm Nhồi Tiếp Theo</span>
                  <span class="risk-dist text-cyan">
                    +{{ calculateDistancePct(pos.next_pyramid_price, pos.current_price).toFixed(2) }}% tới đỉnh
                  </span>
                </div>
                <span class="risk-price">{{ formatPrice(pos.next_pyramid_price, pos.asset_type) }}</span>
              </div>

              <div class="risk-box pyramid-box max-layer-box" v-else>
                <div class="risk-box-header">
                  <span class="risk-lbl">🏆 Đã Đạt Max Nhồi 3 Tầng</span>
                  <span class="risk-dist text-gold">Trailing Stop Kéo Theo Đỉnh</span>
                </div>
                <span class="risk-price text-gold">LET WINNERS RUN</span>
              </div>
            </div>

            <!-- Card Actions & Orders Details -->
            <div class="card-footer">
              <button @click="openOrdersModal(pos)" class="btn-sm btn-ghost">
                🔍 Xem Lịch Sử Khớp Lệnh ({{ pos.orders ? pos.orders.length : 1 }})
              </button>
              <button @click="closePosition(pos.id)" class="btn-sm btn-danger-outline">
                Đóng Vị Thế Thủ Công
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 2: WATCHLIST & Breakout MANAGER -->
      <div v-else-if="activeTab === 'watchlist'" class="tab-content">
        <div class="table-container">
          <div class="table-header-bar">
            <div class="search-box">
              <input v-model="searchKeyword" placeholder="Tìm kiếm mã, tên tài sản..." class="custom-input" />
            </div>
            <div class="table-actions">
              <span class="watchlist-count">Tổng cộng {{ filteredWatchlist.length }} mã</span>
            </div>
          </div>

          <table class="radar-table">
            <thead>
              <tr>
                <th>Mã / Tên Tài Sản</th>
                <th>Thị Trường</th>
                <th>Giá Breakout (Kích Hoạt)</th>
                <th>Giá Hiện Tại</th>
                <th>Khoảng Cách Breakout</th>
                <th>Vốn Vào / Quy Tắc Nhồi</th>
                <th>Cắt Lỗ</th>
                <th>Trạng Thái</th>
                <th>Hành Động</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredWatchlist" :key="item.id" :class="{ 'row-active-pos': item.has_open_position }">
                <td>
                  <div class="sym-name-col sym-clickable" @click="openChart(item.symbol, item.asset_type, item.name)" title="Nhấn để xem biểu đồ TradingView / Vietstock">
                    <div class="d-flex align-items-center gap-1">
                      <span class="sym-code">{{ item.symbol }}</span>
                      <span class="sym-chart-hint">📈</span>
                    </div>
                    <span class="sym-desc" v-if="item.name">{{ item.name }}</span>
                  </div>
                </td>
                <td>
                  <span class="asset-badge" :class="'badge-' + item.asset_type">
                    {{ formatAssetType(item.asset_type) }}
                  </span>
                </td>
                <td>
                  <span class="ath-price-val">{{ formatPrice(item.ath_price, item.asset_type) }}</span>
                </td>
                <td>
                  <span class="cur-price-val" v-if="item.current_price > 0">
                    {{ formatPrice(item.current_price, item.asset_type) }}
                  </span>
                  <span class="text-muted" v-else>Đang chờ quét</span>
                </td>
                <td>
                  <span v-if="item.current_price > 0" :class="item.current_price >= item.ath_price ? 'text-green font-bold' : 'text-muted'">
                    {{ item.current_price >= item.ath_price ? '🔥 ĐÃ VƯỢT ĐỈNH' : ((item.current_price - item.ath_price) / item.ath_price * 100).toFixed(2) + '%' }}
                  </span>
                  <span class="text-muted" v-else>--</span>
                </td>
                <td>
                  <div class="rules-col">
                    <span>${{ item.initial_budget.toLocaleString() }} (Vốn đầu)</span>
                    <span class="rules-sub">Nhồi +{{ item.step_pct }}% (Tỷ lệ {{ (item.pyramid_ratio * 100).toFixed(0) }}%)</span>
                  </div>
                </td>
                <td>
                  <span class="text-red font-semibold">-{{ item.sl_pct }}%</span>
                </td>
                <td>
                  <span v-if="item.has_open_position" class="status-pill status-in-trade">🚀 Đang Có Lệnh</span>
                  <span v-else-if="item.is_active" class="status-pill status-active">🟢 Đang Quét</span>
                  <span v-else class="status-pill status-paused">⚪ Tạm Dừng</span>
                </td>
                <td>
                  <div class="action-btns-row">
                    <button @click="editWatchlistItem(item)" class="btn-icon" title="Chỉnh sửa tham số">
                      ✏️
                    </button>
                    <button @click="deleteWatchlistItem(item.id)" class="btn-icon btn-icon-delete" title="Xóa khỏi watchlist">
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- TAB 3: LEADERBOARD & RELATIVE STRENGTH -->
      <div v-else-if="activeTab === 'leaderboard'" class="tab-content">
        <div class="leaderboard-intro">
          <h3>🏆 Bảng Xếp Hạng Sức Mạnh Tương Đối (Relative Strength)</h3>
          <p>So sánh hiệu suất thực tế giữa các tài sản sau các đợt phá đỉnh và nhồi lệnh, giúp nhận diện dòng tiền đang dồn vào đâu mạnh nhất.</p>
        </div>

        <div class="table-container">
          <table class="radar-table">
            <thead>
              <tr>
                <th>Hạng</th>
                <th>Tài Sản</th>
                <th>Thị Trường</th>
                <th>Tổng Số Trade</th>
                <th>Win Rate</th>
                <th>Max ROI</th>
                <th>Tổng Lợi Nhuận ($)</th>
                <th>Trạng Thái Hiện Tại</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(lead, idx) in filteredLeaderboard" :key="lead.symbol">
                <td>
                  <span class="rank-badge" :class="'rank-' + (idx + 1)">
                    {{ idx === 0 ? '🥇 #1' : idx === 1 ? '🥈 #2' : idx === 2 ? '🥉 #3' : '#' + (idx + 1) }}
                  </span>
                </td>
                <td>
                  <div class="sym-clickable" @click="openChart(lead.symbol, lead.asset_type, lead.name)" title="Nhấn để xem biểu đồ TradingView / Vietstock">
                    <span class="sym-code font-bold">{{ lead.symbol }}</span>
                    <span class="sym-chart-hint">📈</span>
                  </div>
                </td>
                <td>
                  <span class="asset-badge" :class="'badge-' + lead.asset_type">
                    {{ formatAssetType(lead.asset_type) }}
                  </span>
                </td>
                <td>
                  <span>{{ lead.total_trades }} lệnh</span>
                </td>
                <td>
                  <span class="winrate-bar-wrapper">
                    <span class="winrate-text">{{ lead.win_rate_pct.toFixed(1) }}%</span>
                    <div class="winrate-progress">
                      <div class="winrate-fill" :style="{ width: lead.win_rate_pct + '%' }"></div>
                    </div>
                  </span>
                </td>
                <td>
                  <span class="text-gold font-bold">+{{ lead.max_roi.toFixed(2) }}%</span>
                </td>
                <td>
                  <span :class="lead.total_realized_pnl >= 0 ? 'text-green font-bold' : 'text-red font-bold'">
                    {{ lead.total_realized_pnl >= 0 ? '+' : '' }}{{ formatCurrency(lead.total_realized_pnl) }}
                  </span>
                </td>
                <td>
                  <span v-if="lead.current_status === 'OPEN'" class="status-pill status-in-trade">
                    🚀 Tầng {{ lead.current_layer }} ({{ lead.current_roi >= 0 ? '+' : '' }}{{ lead.current_roi.toFixed(2) }}%)
                  </span>
                  <span v-else class="status-pill status-paused">Đã Chốt</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- TAB 4: CLOSED TRADES HISTORY -->
      <div v-else-if="activeTab === 'history'" class="tab-content">
        <div class="table-container">
          <table class="radar-table">
            <thead>
              <tr>
                <th>Tài Sản</th>
                <th>Thị Trường</th>
                <th>Tổng Vốn Vào</th>
                <th>Tầng Đạt Được</th>
                <th>Giá Vốn TB</th>
                <th>Giá Đóng</th>
                <th>Lý Do Đóng</th>
                <th>Lợi Nhuận Thực Tế ($)</th>
                <th>ROI Thực Tế</th>
                <th>Thời Gian Đóng</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pos in closedPositions" :key="pos.id">
                <td>
                  <div class="sym-clickable" @click="openChart(pos.symbol, pos.asset_type, pos.name)" title="Nhấn để xem biểu đồ TradingView / Vietstock">
                    <span class="sym-code font-bold">{{ pos.symbol }}</span>
                    <span class="sym-chart-hint">📈</span>
                  </div>
                </td>
                <td>
                  <span class="asset-badge" :class="'badge-' + pos.asset_type">
                    {{ formatAssetType(pos.asset_type) }}
                  </span>
                </td>
                <td>{{ formatCurrency(pos.total_invested) }}</td>
                <td><span class="layer-tag">Tầng {{ pos.current_layer }}</span></td>
                <td>{{ formatPrice(pos.avg_entry_price, pos.asset_type) }}</td>
                <td>{{ formatPrice(pos.current_price, pos.asset_type) }}</td>
                <td>
                  <span :class="pos.status === 'CLOSED_SL' ? 'text-red' : 'text-cyan'">
                    {{ pos.status === 'CLOSED_SL' ? '🛑 Dính Stop-Loss 5%' : '✋ Đóng Thủ Công' }}
                  </span>
                </td>
                <td>
                  <span :class="pos.realized_pnl >= 0 ? 'text-green font-bold' : 'text-red font-bold'">
                    {{ pos.realized_pnl >= 0 ? '+' : '' }}{{ formatCurrency(pos.realized_pnl) }}
                  </span>
                </td>
                <td>
                  <span :class="pos.realized_pnl >= 0 ? 'text-green font-bold' : 'text-red font-bold'">
                    {{ ((pos.realized_pnl / (pos.total_invested || 1)) * 100).toFixed(2) }}%
                  </span>
                </td>
                <td><span class="text-muted">{{ formatDate(pos.closed_at) }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

    <!-- MODAL: ADD / EDIT WATCHLIST ITEM -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal-card">
        <div class="modal-head">
          <h3>{{ editingItem.id ? 'Chỉnh Sửa Tham Số Mã' : 'Thêm Mã Mới Vào Live Trade' }}</h3>
          <button @click="showModal = false" class="modal-close-btn">&times;</button>
        </div>

        <form @submit.prevent="saveWatchlistItem" class="modal-body">
          <div class="form-row">
            <div class="form-group flex-1">
              <label>Mã Giao Dịch (Symbol) <span class="text-red">*</span></label>
              <input v-model="editingItem.symbol" placeholder="VD: BTCUSDT, NVDA, FPT, GC=F..." required class="custom-input" />
            </div>
            <div class="form-group flex-1">
              <label>Thị Trường (Asset Class) <span class="text-red">*</span></label>
              <select v-model="editingItem.asset_type" required class="custom-select">
                <option value="crypto">Crypto Spot (Binance)</option>
                <option value="futures">Crypto Futures (Binance)</option>
                <option value="stock_vn">Cổ Phiếu VN (VND)</option>
                <option value="stock_us">Cổ Phiếu US (USD)</option>
                <option value="commodity">Hàng Hóa (Vàng, Dầu)</option>
                <option value="forex">Ngoại Hối (Forex)</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label>Tên Gợi Nhớ (Optional)</label>
              <input v-model="editingItem.name" placeholder="VD: Bitcoin, NVIDIA, FPT Corp..." class="custom-input" />
            </div>
            <div class="form-group flex-1">
              <label>Giá Breakout <span class="text-red">*</span></label>
              <input v-model.number="editingItem.ath_price" type="number" step="any" placeholder="Giá Breakout kích hoạt..." required class="custom-input font-bold text-gold" />
            </div>
          </div>

          <div class="modal-divider">QUY TẮC QUẢN LÝ VỐN & PYRAMIDING</div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label>Vốn Mở Lệnh Đợt 1 ($)</label>
              <input v-model.number="editingItem.initial_budget" type="number" step="any" class="custom-input" />
            </div>
            <div class="form-group flex-1">
              <label>Bước Giá Nhồi Lệnh (%)</label>
              <input v-model.number="editingItem.step_pct" type="number" step="0.1" class="custom-input" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label>Tỷ Lệ Nhồi (2/3 = 0.67)</label>
              <input v-model.number="editingItem.pyramid_ratio" type="number" step="0.01" class="custom-input" />
            </div>
            <div class="form-group flex-1">
              <label>Cắt Lỗ Stop-Loss (%)</label>
              <input v-model.number="editingItem.sl_pct" type="number" step="0.1" class="custom-input text-red font-bold" />
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" @click="showModal = false" class="btn-action btn-secondary">Hủy</button>
            <button type="submit" class="btn-action btn-primary-glow">Lưu & Bắt Đầu Quét</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: POSITION ORDERS TIMELINE -->
    <div v-if="selectedPositionForOrders" class="modal-backdrop" @click.self="selectedPositionForOrders = null">
      <div class="modal-card modal-lg">
        <div class="modal-head">
          <div>
            <h3>Chi Tiết Các Lệnh Nhồi & Quản Lý Vốn: {{ selectedPositionForOrders.symbol }}</h3>
            <span class="modal-sub">Trạng thái: {{ selectedPositionForOrders.status }} | Vốn: {{ formatCurrency(selectedPositionForOrders.total_invested) }}</span>
          </div>
          <button @click="selectedPositionForOrders = null" class="modal-close-btn">&times;</button>
        </div>

        <div class="modal-body">
          <div class="orders-timeline">
            <div v-for="order in selectedPositionForOrders.orders" :key="order.id" class="order-timeline-item">
              <div class="order-badge" :class="'order-' + order.order_type.toLowerCase()">
                {{ order.order_type === 'INITIAL_BUY' ? 'MUA ĐỢT 1' : order.order_type === 'PYRAMID_BUY' ? `NHỒI TẦNG ${order.layer}` : 'CẮT LỖ' }}
              </div>
              <div class="order-details">
                <div class="order-main-line">
                  <span class="order-price">Giá khớp: {{ formatPrice(order.price, selectedPositionForOrders.asset_type) }}</span>
                  <span class="order-amount">Số tiền: {{ formatCurrency(order.amount_usd) }}</span>
                  <span class="order-units">Khối lượng: {{ order.units.toFixed(4) }}</span>
                </div>
                <div class="order-reason-line">
                  <span class="order-reason">{{ order.reason }}</span>
                  <span class="order-time">{{ formatDate(order.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL: CHART MODAL (TRADINGVIEW & VIETSTOCK) -->
    <div v-if="showChartModal" class="modal-backdrop" @click.self="closeChartModal">
      <div class="modal-card modal-chart">
        <div class="modal-head chart-modal-head">
          <div class="chart-modal-title-wrap">
            <span class="asset-badge" :class="'badge-' + (selectedChartAsset.asset_type || 'crypto')">
              {{ formatAssetType(selectedChartAsset.asset_type) }}
            </span>
            <div class="chart-title-text">
              <h3>{{ selectedChartAsset.symbol }}</h3>
              <span class="modal-sub" v-if="selectedChartAsset.name">{{ selectedChartAsset.name }}</span>
            </div>
          </div>

          <div class="chart-modal-header-actions">
            <!-- Chart Mode Switcher: TradingView vs Vietstock -->
            <div class="chart-tab-switcher">
              <button 
                type="button"
                class="chart-switch-btn" 
                :class="{ active: chartTab === 'tradingview' }"
                @click="chartTab = 'tradingview'"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>
                </svg>
                TradingView
              </button>
              <button 
                type="button"
                class="chart-switch-btn" 
                :class="{ active: chartTab === 'vietstock' }"
                @click="chartTab = 'vietstock'"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>
                </svg>
                Vietstock
              </button>
            </div>
            
            <button @click="closeChartModal" class="modal-close-btn" aria-label="Đóng">&times;</button>
          </div>
        </div>

        <!-- Symbol Quick Switcher Bar -->
        <div class="chart-modal-search-bar">
          <div class="chart-search-box">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input 
              v-model="chartSearchInput" 
              @keydown.enter="applyChartSearch" 
              placeholder="Nhập mã khác (VD: FPT, BTCUSDT, NVDA, EURUSD, GC=F...)"
              class="chart-search-input" 
            />
            <button class="btn-search-apply" @click="applyChartSearch">Xem</button>
          </div>
          <div class="chart-quick-chips" v-if="quickChartChips.length > 0">
            <span class="quick-chips-lbl">Gợi ý:</span>
            <button 
              v-for="chip in quickChartChips" 
              :key="chip.symbol" 
              class="quick-chip"
              :class="{ 'quick-chip-active': selectedChartAsset.symbol.toUpperCase() === chip.symbol.toUpperCase() }"
              @click="openChart(chip.symbol, chip.asset_type, chip.name)"
            >
              {{ chip.symbol }}
            </button>
          </div>
        </div>

        <!-- Chart Body Display -->
        <div class="modal-chart-body">
          <div v-show="chartTab === 'tradingview'" class="tradingview-container-wrap">
            <TradingViewChart 
              v-if="showChartModal && chartTab === 'tradingview' && resolvedTvSymbol" 
              :key="resolvedTvSymbol" 
              :coin="resolvedTvSymbol" 
              :height="520" 
            />
          </div>
          <div v-show="chartTab === 'vietstock'" class="vietstock-container-wrap">
            <iframe 
              v-if="showChartModal && chartTab === 'vietstock' && resolvedVnCode"
              :key="resolvedVnCode"
              :src="`https://stockchart.vietstock.vn/?stockcode=${resolvedVnCode}`" 
              width="100%" 
              height="520" 
              frameborder="0" 
              allowfullscreen 
              class="vietstock-iframe"
            ></iframe>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import NavBar from '@/components/NavBar.vue';
import TradingViewChart from '@/components/TradingViewChart.vue';

export default {
  name: 'BreakoutRadar',
  components: {
    NavBar,
    TradingViewChart
  },
  data() {
    return {
      activeTab: 'positions', // 'positions', 'watchlist', 'leaderboard', 'history'
      selectedAssetFilter: 'ALL',
      searchKeyword: '',
      loading: false,
      isInitialLoad: true,
      
      watchlist: [],
      positions: [],
      leaderboard: [],
      
      // Modals
      showModal: false,
      editingItem: {
        id: null,
        symbol: '',
        asset_type: 'crypto',
        name: '',
        ath_price: null,
        initial_budget: 1000,
        step_pct: 5.0,
        pyramid_ratio: 0.67,
        sl_pct: 5.0,
        max_pyramids: 3,
        is_active: true,
        notes: ''
      },
      selectedPositionForOrders: null,
      pollingInterval: null,

      // Chart Modal State
      showChartModal: false,
      chartTab: 'tradingview', // 'tradingview' | 'vietstock'
      selectedChartAsset: {
        symbol: '',
        asset_type: 'crypto',
        name: ''
      },
      chartSearchInput: ''
    };
  },
  computed: {
    activeWatchlistCount() {
      return this.watchlist.filter(w => w.is_active).length;
    },
    openPositions() {
      return this.positions.filter(p => p.status === 'OPEN');
    },
    closedPositions() {
      return this.positions.filter(p => p.status !== 'OPEN');
    },
    filteredOpenPositions() {
      let list = this.openPositions;
      if (this.selectedAssetFilter !== 'ALL') {
        list = list.filter(p => p.asset_type === this.selectedAssetFilter);
      }
      return list;
    },
    filteredWatchlist() {
      let list = this.watchlist;
      if (this.selectedAssetFilter !== 'ALL') {
        list = list.filter(w => w.asset_type === this.selectedAssetFilter);
      }
      if (this.searchKeyword.trim()) {
        const q = this.searchKeyword.toLowerCase();
        list = list.filter(w => w.symbol.toLowerCase().includes(q) || (w.name && w.name.toLowerCase().includes(q)));
      }
      return list;
    },
    filteredLeaderboard() {
      let list = this.leaderboard;
      if (this.selectedAssetFilter !== 'ALL') {
        list = list.filter(l => l.asset_type === this.selectedAssetFilter);
      }
      return list;
    },
    totalInvestedOpen() {
      return this.openPositions.reduce((sum, p) => sum + (p.total_invested || 0), 0);
    },
    totalUnrealizedPnL() {
      return this.openPositions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0);
    },
    totalRealizedPnL() {
      return this.closedPositions.reduce((sum, p) => sum + (p.realized_pnl || 0), 0);
    },
    avgOpenROI() {
      if (this.openPositions.length === 0) return 0;
      const sum = this.openPositions.reduce((s, p) => s + (p.unrealized_roi_pct || 0), 0);
      return sum / this.openPositions.length;
    },
    overallWinRate() {
      if (this.closedPositions.length === 0) return 0;
      const wins = this.closedPositions.filter(p => p.realized_pnl > 0).length;
      return (wins / this.closedPositions.length) * 100;
    },
    resolvedTvSymbol() {
      const asset = this.selectedChartAsset;
      if (!asset || !asset.symbol) return '';
      const sym = asset.symbol.trim();
      const type = asset.asset_type;

      if (sym.includes(':')) return sym;

      if (type === 'futures') {
        if (sym.toUpperCase().endsWith('USDT')) return `BINANCE:${sym}.P`;
        return `BINANCE:${sym}`;
      }
      if (type === 'crypto') {
        if (sym.toUpperCase().endsWith('USDT')) return `BINANCE:${sym}`;
        if (!sym.toUpperCase().endsWith('USDT') && !sym.toUpperCase().endsWith('BTC') && !sym.toUpperCase().endsWith('USD')) {
          return `BINANCE:${sym}USDT`;
        }
        return `BINANCE:${sym}`;
      }
      if (type === 'stock_vn') {
        if (sym.toUpperCase() === 'VNINDEX') return 'HOSE:VNINDEX';
        if (sym.toUpperCase() === 'VN30') return 'HOSE:VN30';
        if (sym.toUpperCase() === 'VN30F1M') return 'HNX:VN30F1M';
        if (sym.toUpperCase() === 'HNXINDEX') return 'HNX:HNXINDEX';
        return `HOSE:${sym}`;
      }
      if (type === 'stock_us') {
        if (sym.toUpperCase() === 'SPX') return 'SP:SPX';
        return sym;
      }
      if (type === 'commodity') {
        const comMap = {
          'GC=F': 'OANDA:XAUUSD',
          'XAUUSD': 'OANDA:XAUUSD',
          'GOLD': 'OANDA:XAUUSD',
          'SI=F': 'OANDA:XAGUSD',
          'XAGUSD': 'OANDA:XAGUSD',
          'SILVER': 'OANDA:XAGUSD',
          'CL=F': 'TVC:USOIL',
          'USOIL': 'TVC:USOIL',
          'WTI': 'TVC:USOIL',
          'BZ=F': 'TVC:UKOIL',
          'UKOIL': 'TVC:UKOIL',
          'BRENT': 'TVC:UKOIL'
        };
        return comMap[sym.toUpperCase()] || sym;
      }
      if (type === 'forex') {
        const fxMap = {
          'DXY': 'CAPITALCOM:DXY',
          'XAUUSD': 'OANDA:XAUUSD',
          'XAGUSD': 'OANDA:XAGUSD'
        };
        return fxMap[sym.toUpperCase()] || `FX:${sym}`;
      }

      if (sym.toUpperCase() === 'VNINDEX') return 'HOSE:VNINDEX';
      if (sym.toUpperCase() === 'VN30') return 'HOSE:VN30';
      if (sym.toUpperCase().endsWith('USDT')) return `BINANCE:${sym}`;
      return sym;
    },
    resolvedVnCode() {
      const asset = this.selectedChartAsset;
      if (!asset || !asset.symbol) return '';
      let sym = asset.symbol.trim().toUpperCase();
      if (sym.includes(':')) {
        sym = sym.split(':').pop();
      }
      return sym;
    },
    quickChartChips() {
      const chips = [];
      const seen = new Set();

      for (const pos of this.openPositions) {
        if (!seen.has(pos.symbol.toUpperCase())) {
          seen.add(pos.symbol.toUpperCase());
          chips.push({ symbol: pos.symbol, asset_type: pos.asset_type, name: pos.name || '' });
        }
      }
      for (const item of this.watchlist) {
        if (!seen.has(item.symbol.toUpperCase())) {
          seen.add(item.symbol.toUpperCase());
          chips.push({ symbol: item.symbol, asset_type: item.asset_type, name: item.name || '' });
        }
      }
      return chips.slice(0, 8);
    }
  },
  mounted() {
    this.fetchAllData();
    // Auto refresh every 10 seconds for real-time paper trades
    this.pollingInterval = setInterval(() => {
      this.fetchAllData(false);
    }, 10000);
  },
  beforeUnmount() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
  },
  methods: {
    openChart(symbol, assetType, name) {
      if (!symbol) return;
      const cleanSym = symbol.trim();
      let detectedType = assetType;
      let detectedName = name;
      
      if (!detectedType || !detectedName) {
        const match = this.watchlist.find(w => w.symbol.toUpperCase() === cleanSym.toUpperCase());
        if (match) {
          detectedType = detectedType || match.asset_type;
          detectedName = detectedName || match.name;
        } else {
          const pMatch = this.positions.find(p => p.symbol.toUpperCase() === cleanSym.toUpperCase());
          if (pMatch) {
            detectedType = detectedType || pMatch.asset_type;
            detectedName = detectedName || pMatch.name;
          }
        }
      }

      const isVn = (detectedType === 'stock_vn') || 
                   cleanSym.toUpperCase().startsWith('VN') || 
                   (cleanSym.length === 3 && /^[A-Z]+$/.test(cleanSym) && !['BTC','ETH','SOL','BNB','XRP','ADA','DOT','DOGE','AVAX','LINK','UNI','LTC','BCH'].includes(cleanSym.toUpperCase()) && detectedType !== 'crypto' && detectedType !== 'stock_us' && detectedType !== 'forex');

      this.chartTab = isVn ? 'vietstock' : 'tradingview';
      this.selectedChartAsset = {
        symbol: cleanSym,
        asset_type: detectedType || (isVn ? 'stock_vn' : 'crypto'),
        name: detectedName || ''
      };
      this.chartSearchInput = cleanSym;
      this.showChartModal = true;
    },
    closeChartModal() {
      this.showChartModal = false;
    },
    applyChartSearch() {
      const input = (this.chartSearchInput || '').trim().toUpperCase();
      if (!input) return;
      this.openChart(input);
    },
    getAuthHeaders() {
      const token = localStorage.getItem('token');
      return token ? { 'Authorization': `Bearer ${token}` } : {};
    },
    async fetchAllData(showSpinner = true) {
      if (showSpinner) this.loading = true;
      try {
        await Promise.all([
          this.fetchWatchlist(),
          this.fetchPositions(),
          this.fetchLeaderboard()
        ]);
      } catch (err) {
        console.error("Error loading breakout data:", err);
      } finally {
        this.loading = false;
        this.isInitialLoad = false;
      }
    },
    async fetchWatchlist() {
      try {
        const res = await fetch('/breakout/watchlist', { headers: this.getAuthHeaders() });
        if (res.status === 401) {
          this.$router.push({ name: 'Login' });
          return;
        }
        if (res.ok) {
          const data = await res.json();
          this.watchlist = data || [];
        }
      } catch (e) {
        console.error("Error fetching watchlist:", e);
      }
    },
    async fetchPositions() {
      try {
        const res = await fetch('/breakout/positions', { headers: this.getAuthHeaders() });
        if (res.status === 401) {
          this.$router.push({ name: 'Login' });
          return;
        }
        if (res.ok) {
          const data = await res.json();
          this.positions = data || [];
        }
      } catch (e) {
        console.error("Error fetching positions:", e);
      }
    },
    async fetchLeaderboard() {
      try {
        const res = await fetch('/breakout/leaderboard', { headers: this.getAuthHeaders() });
        if (res.status === 401) {
          this.$router.push({ name: 'Login' });
          return;
        }
        if (res.ok) {
          const data = await res.json();
          this.leaderboard = data || [];
        }
      } catch (e) {
        console.error("Error fetching leaderboard:", e);
      }
    },
    openAddModal() {
      this.editingItem = {
        id: null,
        symbol: '',
        asset_type: 'crypto',
        name: '',
        ath_price: null,
        initial_budget: 1000,
        step_pct: 5.0,
        pyramid_ratio: 0.67,
        sl_pct: 5.0,
        max_pyramids: 3,
        is_active: true,
        notes: ''
      };
      this.showModal = true;
    },
    editWatchlistItem(item) {
      this.editingItem = { ...item };
      this.showModal = true;
    },
    async saveWatchlistItem() {
      try {
        const method = this.editingItem.id ? 'PUT' : 'POST';
        const res = await fetch('/breakout/watchlist', {
          method,
          headers: { 
            'Content-Type': 'application/json',
            ...this.getAuthHeaders()
          },
          body: JSON.stringify(this.editingItem)
        });
        if (res.status === 401) {
          this.$router.push({ name: 'Login' });
          return;
        }
        if (res.ok) {
          this.showModal = false;
          this.fetchWatchlist();
        } else {
          alert('Lỗi lưu watchlist item');
        }
      } catch (e) {
        console.error("Save error:", e);
      }
    },
    async deleteWatchlistItem(id) {
      if (!confirm('Bạn có chắc muốn xóa mã này khỏi danh sách Live Trade?')) return;
      try {
        const res = await fetch(`/breakout/watchlist?id=${id}`, { 
          method: 'DELETE',
          headers: this.getAuthHeaders()
        });
        if (res.status === 401) {
          this.$router.push({ name: 'Login' });
          return;
        }
        if (res.ok) {
          this.fetchWatchlist();
        }
      } catch (e) {
        console.error("Delete error:", e);
      }
    },
    async closePosition(positionId) {
      if (!confirm('Bạn có chắc muốn đóng vị thế này ngay lập tức?')) return;
      try {
        const res = await fetch('/breakout/positions/close', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            ...this.getAuthHeaders()
          },
          body: JSON.stringify({ position_id: positionId, reason: 'MANUAL_CLOSE' })
        });
        if (res.status === 401) {
          this.$router.push({ name: 'Login' });
          return;
        }
        if (res.ok) {
          this.fetchPositions();
          this.fetchLeaderboard();
        }
      } catch (e) {
        console.error("Close position error:", e);
      }
    },
    openOrdersModal(pos) {
      this.selectedPositionForOrders = pos;
    },
    formatPrice(price, assetType) {
      if (!price && price !== 0) return '--';
      if (assetType === 'stock_vn') {
        return price.toLocaleString('vi-VN') + 'đ';
      }
      return '$' + Number(price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
    },
    formatCurrency(val) {
      if (!val && val !== 0) return '$0.00';
      return '$' + Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
    formatAssetType(type) {
      const map = {
        'crypto': 'Crypto Spot',
        'futures': 'Futures',
        'stock_vn': 'Stock VN',
        'stock_us': 'Stock US',
        'commodity': 'Commodity',
        'forex': 'Forex'
      };
      return map[type] || type;
    },
    formatDate(dateStr) {
      if (!dateStr) return '--';
      const d = new Date(dateStr);
      return d.toLocaleDateString('vi-VN') + ' ' + d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    },
    calculateDistancePct(target, current) {
      if (!current || current === 0) return 0;
      return Math.abs((target - current) / current) * 100;
    }
  }
};
</script>

<style scoped>
.breakout-radar-wrapper {
  min-height: 100vh;
  background-color: #0a0d14;
  color: #e2e8f0;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  padding-bottom: 80px;
}

.radar-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 20px;
}

/* Header */
.radar-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
  gap: 20px;
}

.badge-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.3);
  color: #00f2fe;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.8px;
  margin-bottom: 10px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00f2fe;
  box-shadow: 0 0 10px #00f2fe;
  animation: pulse 1.8s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.radar-title {
  font-size: 28px;
  font-weight: 800;
  margin: 0 0 8px 0;
  color: #ffffff;
}

.gradient-text {
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 50%, #00f5a0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.radar-subtitle {
  color: #94a3b8;
  font-size: 14px;
  margin: 0;
  max-width: 720px;
  line-height: 1.5;
}

.radar-header-actions {
  display: flex;
  gap: 12px;
}

/* Metrics Cards */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.metric-card {
  background: rgba(18, 24, 38, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s, border-color 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
  border-color: rgba(0, 242, 254, 0.3);
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-icon-cyan { background: rgba(0, 242, 254, 0.12); color: #00f2fe; }
.metric-icon-green { background: rgba(0, 245, 160, 0.12); color: #00f5a0; }
.metric-icon-gold { background: rgba(246, 211, 101, 0.12); color: #f6d365; }
.metric-icon-red { background: rgba(255, 75, 114, 0.12); color: #ff4b72; }

.metric-info {
  display: flex;
  flex-direction: column;
}

.metric-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 22px;
  font-weight: 800;
  color: #ffffff;
}

.metric-sub {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

/* Tabs */
.radar-tabs-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 24px;
  padding-bottom: 12px;
  flex-wrap: wrap;
  gap: 16px;
}

.tabs-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tab-btn {
  background: transparent;
  border: 1px solid transparent;
  color: #94a3b8;
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.04);
}

.tab-btn-active {
  background: rgba(0, 242, 254, 0.12) !important;
  border-color: rgba(0, 242, 254, 0.3) !important;
  color: #00f2fe !important;
}

.tab-badge {
  background: #00f5a0;
  color: #0a0d14;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 800;
}

.tab-badge-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 10px;
}

/* Position Cards */
.positions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 20px;
}

.position-card {
  background: rgba(18, 24, 38, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  transition: all 0.25s;
}

.card-profit {
  border-left: 4px solid #00f5a0;
}

.card-loss {
  border-left: 4px solid #ff4b72;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.sym-block {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sym-name {
  font-size: 18px;
  font-weight: 800;
  color: #ffffff;
}

.pnl-pill {
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 800;
  font-size: 14px;
}

.pill-green {
  background: rgba(0, 245, 160, 0.15);
  border: 1px solid rgba(0, 245, 160, 0.3);
  color: #00f5a0;
}

.pill-red {
  background: rgba(255, 75, 114, 0.15);
  border: 1px solid rgba(255, 75, 114, 0.3);
  color: #ff4b72;
}

.pnl-usd {
  font-size: 12px;
  font-weight: 600;
  margin-left: 4px;
}

.price-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  background: rgba(10, 13, 20, 0.5);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 16px;
}

.stat-col {
  display: flex;
  flex-direction: column;
}

.col-lbl {
  font-size: 10px;
  color: #64748b;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.col-val {
  font-size: 13px;
  font-weight: 700;
  color: #e2e8f0;
}

.val-highlight {
  color: #00f2fe;
}

/* Pyramid Tracker */
.pyramid-tracker {
  background: rgba(10, 13, 20, 0.35);
  border: 1px dashed rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 16px;
}

.tracker-header {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  margin-bottom: 12px;
}

.tracker-layer {
  color: #00f2fe;
}

.tracker-steps {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0.4;
  transition: opacity 0.2s;
}

.step-active {
  opacity: 1;
}

.step-circle {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
}

.step-active .step-circle {
  background: #00f2fe;
  border-color: #00f2fe;
  color: #0a0d14;
  box-shadow: 0 0 10px rgba(0, 242, 254, 0.5);
}

.step-info {
  display: flex;
  flex-direction: column;
}

.step-name {
  font-size: 10px;
  color: #94a3b8;
}

.step-val {
  font-size: 11px;
  font-weight: 700;
  color: #ffffff;
}

.step-line {
  flex: 1;
  height: 2px;
  background: rgba(255, 255, 255, 0.1);
  margin: 0 8px;
}

.line-active {
  background: #00f2fe;
  box-shadow: 0 0 6px #00f2fe;
}

/* Risk Bar Grid */
.risk-bar-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.risk-box {
  background: rgba(10, 13, 20, 0.6);
  border-radius: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.sl-box { border-left: 3px solid #ff4b72; }
.pyramid-box { border-left: 3px solid #00f2fe; }
.max-layer-box { border-left: 3px solid #f6d365; }

.risk-box-header {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  margin-bottom: 4px;
}

.risk-lbl { color: #94a3b8; font-weight: 600; }
.risk-dist { font-weight: 700; font-size: 10px; }
.risk-price { font-size: 13px; font-weight: 800; color: #ffffff; }

/* Card Footer */
.card-footer {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 14px;
}

/* Table Styles */
.table-container {
  background: rgba(18, 24, 38, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  overflow-x: auto;
}

.table-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.radar-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;
}

.radar-table th {
  padding: 12px 18px;
  color: #64748b;
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 700;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.radar-table td {
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: #e2e8f0;
}

.radar-table tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.row-active-pos {
  background: rgba(0, 245, 160, 0.03);
}

.sym-name-col {
  display: flex;
  flex-direction: column;
}

.sym-code {
  font-size: 14px;
  font-weight: 800;
  color: #ffffff;
}

.sym-desc {
  font-size: 11px;
  color: #64748b;
}

.ath-price-val {
  font-weight: 800;
  color: #f6d365;
}

.cur-price-val {
  font-weight: 800;
  color: #00f2fe;
}

/* Badges */
.asset-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}

.badge-crypto { background: rgba(247, 147, 26, 0.15); color: #f7931a; }
.badge-futures { background: rgba(0, 242, 254, 0.15); color: #00f2fe; }
.badge-stock_vn { background: rgba(235, 77, 75, 0.15); color: #eb4d4b; }
.badge-stock_us { background: rgba(79, 172, 254, 0.15); color: #4facfe; }
.badge-commodity { background: rgba(246, 211, 101, 0.15); color: #f6d365; }
.badge-forex { background: rgba(162, 155, 254, 0.15); color: #a29bfe; }

.status-pill {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
}

.status-active { background: rgba(0, 245, 160, 0.12); color: #00f5a0; }
.status-in-trade { background: rgba(0, 242, 254, 0.15); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.3); }
.status-paused { background: rgba(255, 255, 255, 0.08); color: #94a3b8; }

/* Buttons & Inputs */
.btn-action {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary-glow {
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  color: #0a0d14;
  box-shadow: 0 4px 14px rgba(0, 242, 254, 0.35);
}

.btn-primary-glow:hover {
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.5);
  transform: translateY(-1px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 8px;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-ghost {
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
}

.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.btn-danger-outline {
  background: transparent;
  border: 1px solid rgba(255, 75, 114, 0.3);
  color: #ff4b72;
}

.btn-danger-outline:hover {
  background: rgba(255, 75, 114, 0.15);
}

.btn-icon {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
  border-radius: 6px;
}

.btn-icon:hover { background: rgba(255, 255, 255, 0.1); }

.custom-input, .custom-select {
  background: rgba(10, 13, 20, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #ffffff;
  padding: 9px 14px;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  width: 100%;
  box-sizing: border-box;
}

.custom-input:focus, .custom-select:focus {
  border-color: #00f2fe;
}

/* Modals */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.modal-card {
  background: #111726;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  width: 100%;
  max-width: 560px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.modal-lg {
  max-width: 680px;
}

.modal-head {
  padding: 18px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-head h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  color: #ffffff;
}

.modal-sub {
  font-size: 12px;
  color: #94a3b8;
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 24px;
  cursor: pointer;
}

.modal-body {
  padding: 20px 24px;
}

.form-row {
  display: flex;
  gap: 14px;
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 6px;
}

.modal-divider {
  font-size: 10px;
  font-weight: 800;
  color: #00f2fe;
  letter-spacing: 0.8px;
  margin: 18px 0 14px 0;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
  padding-bottom: 6px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

/* Orders Timeline */
.orders-timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.order-timeline-item {
  display: flex;
  gap: 14px;
  background: rgba(10, 13, 20, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 12px 16px;
}

.order-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 800;
  align-self: flex-start;
  white-space: nowrap;
}

.order-initial_buy { background: rgba(0, 245, 160, 0.15); color: #00f5a0; }
.order-pyramid_buy { background: rgba(0, 242, 254, 0.15); color: #00f2fe; }
.order-stop_loss { background: rgba(255, 75, 114, 0.15); color: #ff4b72; }
.order-manual_close { background: rgba(246, 211, 101, 0.15); color: #f6d365; }

.order-details {
  flex: 1;
}

.order-main-line {
  display: flex;
  gap: 16px;
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 4px;
}

.order-reason-line {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #64748b;
}

/* Empty & Loading */
.empty-card {
  text-align: center;
  padding: 60px 20px;
  background: rgba(18, 24, 38, 0.5);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-card h3 { color: #ffffff; margin-bottom: 8px; }
.empty-card p { color: #94a3b8; max-width: 500px; margin: 0 auto 20px auto; font-size: 13px; }

.loading-box {
  text-align: center;
  padding: 60px;
  color: #94a3b8;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(0, 242, 254, 0.2);
  border-top-color: #00f2fe;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px auto;
}

.spinning { animation: spin 0.8s linear infinite; }

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Utilities */
.text-green { color: #00f5a0; }
.text-red { color: #ff4b72; }
.text-cyan { color: #00f2fe; }
.text-gold { color: #f6d365; }
.text-muted { color: #64748b; }
.font-bold { font-weight: 700; }
.font-semibold { font-weight: 600; }
.flex-1 { flex: 1; }

.winrate-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.winrate-progress {
  width: 60px;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.winrate-fill {
  height: 100%;
  background: #00f5a0;
}

/* Clickable Symbol Enhancements */
.sym-clickable {
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  user-select: none;
}

.sym-clickable:hover .sym-name,
.sym-clickable:hover .sym-code {
  color: #00f2fe;
  text-decoration: underline;
  text-decoration-color: rgba(0, 242, 254, 0.4);
  text-underline-offset: 3px;
}

.sym-chart-hint {
  font-size: 12px;
  opacity: 0.5;
  transition: all 0.2s ease;
  transform: scale(0.9);
}

.sym-clickable:hover .sym-chart-hint {
  opacity: 1;
  transform: scale(1.15);
}

/* Modal Chart Styles */
.modal-chart {
  max-width: 1040px;
  width: 95vw;
  background: #0f1523;
  border: 1px solid rgba(0, 242, 254, 0.25);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.7), 0 0 30px rgba(0, 242, 254, 0.1);
}

.chart-modal-head {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.chart-modal-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-title-text {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.chart-title-text h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.chart-modal-header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.chart-tab-switcher {
  display: flex;
  background: rgba(10, 13, 20, 0.8);
  padding: 3px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.chart-switch-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.chart-switch-btn:hover {
  color: #ffffff;
}

.chart-switch-btn.active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.2) 0%, rgba(79, 172, 254, 0.2) 100%);
  color: #00f2fe;
  border: 1px solid rgba(0, 242, 254, 0.4);
  box-shadow: 0 0 10px rgba(0, 242, 254, 0.2);
}

.chart-modal-search-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: rgba(10, 13, 20, 0.6);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-wrap: wrap;
  gap: 12px;
}

.chart-search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(18, 24, 38, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 4px 10px;
  flex: 1;
  max-width: 440px;
  color: #94a3b8;
}

.chart-search-input {
  background: transparent;
  border: none;
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  outline: none;
  width: 100%;
}

.btn-search-apply {
  background: rgba(0, 242, 254, 0.15);
  border: 1px solid rgba(0, 242, 254, 0.3);
  color: #00f2fe;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-search-apply:hover {
  background: rgba(0, 242, 254, 0.3);
}

.chart-quick-chips {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.quick-chips-lbl {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
}

.quick-chip {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-chip:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.quick-chip-active {
  background: rgba(0, 242, 254, 0.15);
  border-color: rgba(0, 242, 254, 0.4);
  color: #00f2fe;
}

.modal-chart-body {
  background: #0a0d14;
  min-height: 520px;
}

.tradingview-container-wrap {
  width: 100%;
  min-height: 520px;
}

.vietstock-container-wrap {
  width: 100%;
  background: #ffffff;
}

.vietstock-iframe {
  display: block;
  border: none;
  background: #ffffff;
  width: 100%;
  height: 520px;
}
</style>
