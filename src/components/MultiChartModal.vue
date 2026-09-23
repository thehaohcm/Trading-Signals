<template>
  <Teleport to="body">
    <div v-if="visible" class="multi-chart-backdrop" :class="{ 'is-minimized-backdrop': isMinimized }" @click.self="handleBackdropClick">
      <!-- Floating Minimized Pill when minimized -->
      <div v-if="isMinimized" class="minimized-pill" @click="toggleMinimize">
        <div class="d-flex align-items-center gap-2">
          <i class="fa-solid fa-chart-line text-cyan"></i>
          <span class="fw-bold">{{ activeSymbolDisplay }}</span>
          <span class="badge bg-secondary">{{ splitCount }} Chart{{ splitCount > 1 ? 's' : '' }}</span>
        </div>
        <div class="d-flex align-items-center gap-1 ms-3">
          <button class="pill-btn" @click.stop="toggleMinimize" title="Phục hồi cửa sổ">
            <i class="fa-solid fa-window-restore"></i>
          </button>
          <button class="pill-btn pill-btn--close" @click.stop="closeModal" title="Đóng">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>

      <!-- Main Modal Window -->
      <div 
        v-else 
        class="multi-chart-modal" 
        :class="{ 
          'is-maximized': isMaximized,
          'split-layout-1': splitCount === 1,
          'split-layout-2': splitCount === 2,
          'split-layout-4': splitCount === 4,
          'split-layout-8': splitCount === 8
        }" 
        @click.stop
      >
        <!-- Modal Header -->
        <div class="modal-header-bar">
          <div class="header-left d-flex align-items-center gap-2">
            <div class="chart-header-icon">
              <i class="fa-solid fa-chart-candlestick"></i>
            </div>
            <div>
              <h5 class="modal-title m-0">{{ modalTitle }}</h5>
              <span class="modal-subtitle">{{ activeSubtitle }}</span>
            </div>
          </div>

          <!-- Split Window Selector & Auto Live Trade Toggle -->
          <div class="header-center d-flex align-items-center gap-2">
            <!-- Auto Live Trade Toggle Button -->
            <button 
              type="button" 
              class="quick-trade-toggle-btn"
              :class="{ 'is-active': isRealTradeOpen, 'has-open-position': !!currentOpenPosition, 'has-auto-trade': isSymbolAutoTradeActive && !currentOpenPosition }"
              @click="toggleRealTrade"
              title="Bật/Tắt cấu hình Tự Động Live Trade theo Tín Hiệu"
            >
              <span class="live-dot" :class="{ 'live-dot--active': isRealTradeOpen || !!currentOpenPosition }"></span>
              <span class="btn-text">
                <template v-if="currentOpenPosition">
                  🟢 VỊ THẾ ĐANG MỞ ({{ currentOpenPosition.unrealized_pnl >= 0 ? '+' : '' }}{{ formatNumber(currentOpenPosition.unrealized_pnl) }}$)
                </template>
                <template v-else-if="isSymbolAutoTradeActive">
                  ⚡ AUTO TRADE ĐANG BẬT
                </template>
                <template v-else>
                  🔴 Auto Live Trade
                </template>
              </span>
              <i class="fa-solid ms-1" :class="isRealTradeOpen ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
            </button>

            <!-- Split Controls Group -->
            <div class="split-controls-group" title="Chia cửa sổ biểu đồ (Split Chart Windows)">
              <span class="split-label d-none d-lg-inline">Split:</span>
              <button 
                type="button"
                class="split-btn" 
                :class="{ 'is-active': splitCount === 1 }" 
                @click="setSplitCount(1)"
                title="1 Cửa sổ (Single View)"
              >
                <span class="split-icon">▢</span>
                <span class="split-text">1</span>
              </button>
              <button 
                type="button"
                class="split-btn" 
                :class="{ 'is-active': splitCount === 2 }" 
                @click="setSplitCount(2)"
                title="2 Cửa sổ song song (Split 1x2)"
              >
                <span class="split-icon">◫</span>
                <span class="split-text">2</span>
              </button>
              <button 
                type="button"
                class="split-btn" 
                :class="{ 'is-active': splitCount === 4 }" 
                @click="setSplitCount(4)"
                title="4 Cửa sổ lưới (Grid 2x2)"
              >
                <span class="split-icon">⊞</span>
                <span class="split-text">4</span>
              </button>
              <button 
                type="button"
                class="split-btn" 
                :class="{ 'is-active': splitCount === 8 }" 
                @click="setSplitCount(8)"
                title="8 Cửa sổ nâng cao (Grid 4x2)"
              >
                <span class="split-icon">▦</span>
                <span class="split-text">8</span>
              </button>
            </div>
          </div>

          <!-- Header Window Action Buttons -->
          <div class="header-right d-flex align-items-center gap-1">
            <!-- Minimize Button -->
            <button 
              type="button" 
              class="window-ctrl-btn" 
              @click="toggleMinimize" 
              title="Thu nhỏ thành thanh nổi"
            >
              <i class="fa-solid fa-minus"></i>
            </button>

            <!-- Maximize / Restore Button -->
            <button 
              type="button" 
              class="window-ctrl-btn" 
              @click="toggleMaximize" 
              :title="isMaximized ? 'Thu nhỏ về kích thước chuẩn' : 'Phóng to toàn màn hình (Full Screen)'"
            >
              <i class="fa-solid" :class="isMaximized ? 'fa-compress' : 'fa-expand'"></i>
            </button>

            <!-- Close Button -->
            <button 
              type="button" 
              class="window-ctrl-btn window-ctrl-btn--close" 
              @click="closeModal" 
              title="Đóng cửa sổ"
            >
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
        </div>

        <!-- REAL-TIME AUTO TRADE ACTION BAR (COLLAPSIBLE) -->
        <div class="real-trade-bar" v-if="isRealTradeOpen">
          <div class="real-trade-content d-flex align-items-center justify-content-between flex-wrap gap-2">
            <!-- Left: Current Symbol & Exchange Selector -->
            <div class="d-flex align-items-center gap-2 flex-wrap">
              <span class="trade-symbol-badge">
                <i class="fa-solid fa-bolt text-yellow me-1"></i>{{ currentActiveSymbol }}
              </span>
              
              <!-- Exchange Selector Pills -->
              <div class="exchange-pills">
                <button 
                  v-for="ex in ['binance', 'okx', 'bybit']" 
                  :key="ex"
                  type="button"
                  class="exchange-pill"
                  :class="{ 'is-active': activeExchange === ex }"
                  @click="selectExchange(ex)"
                >
                  {{ ex.toUpperCase() }}
                </button>
              </div>

              <!-- Config API Key Button -->
              <button 
                type="button" 
                class="btn-config-key"
                @click="showApiKeyModal = true"
                :title="apiKeyConfigured ? 'Cập nhật API Key sàn' : 'Chưa cấu hình API Key sàn'"
              >
                <i class="fa-solid fa-key me-1 text-cyan"></i>
                <span>{{ apiKeyConfigured ? 'Đổi Key' : '🔑 Nhập API Key' }}</span>
              </button>
            </div>

            <!-- Case 1: IF POSITION ALREADY OPEN -> SHOW LIVE STATS & CLOSE POSITION BUTTON -->
            <template v-if="currentOpenPosition">
              <div class="trade-position-status d-flex align-items-center gap-2 flex-wrap">
                <span class="pos-badge-live">🟢 Đang Giữ Vị Thế: {{ currentOpenPosition.total_units }} {{ currentOpenPosition.symbol }}</span>
                <span class="pos-stat">Entry: <strong>${{ formatNumber(currentOpenPosition.avg_entry_price) }}</strong></span>
                <span class="pos-stat" :class="currentOpenPosition.unrealized_pnl >= 0 ? 'text-green' : 'text-red'">
                  PnL: <strong>{{ currentOpenPosition.unrealized_pnl >= 0 ? '+' : '' }}{{ formatNumber(currentOpenPosition.unrealized_pnl) }}$ ({{ (currentOpenPosition.unrealized_roi_pct || 0).toFixed(2) }}%)</strong>
                </span>
                <span class="pos-stat text-gold">SL (-2%): <strong>${{ formatNumber(currentOpenPosition.stop_loss_price) }}</strong></span>
                <span class="badge bg-primary bg-opacity-25 text-cyan py-1 px-2 font-mono" style="font-size: 0.72rem;">🤖 alert.py đang tự động dời SL & cắt lỗ</span>
              </div>

              <div class="d-flex align-items-center gap-2">
                <button 
                  type="button" 
                  class="btn-close-position-instant"
                  :disabled="isClosingOrder"
                  @click="closeActivePosition(currentOpenPosition.id)"
                  title="Thoát và bán toàn bộ vị thế ngay lập tức theo giá thị trường"
                >
                  <i class="fa-solid fa-arrow-right-from-bracket me-1"></i>
                  <span>{{ isClosingOrder ? 'Đang thoát...' : '🚨 THOÁT LỆNH NGAY LẬP TỨC' }}</span>
                </button>
              </div>
            </template>

            <!-- Case 2: IF NO ACTIVE POSITION -> CONFIGURE TRADE OPTIONS -->
            <template v-else>
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <!-- Trade Mode Selector (Signal, Trigger Price, Market Now) -->
                <div class="trade-mode-pills d-flex align-items-center" v-if="apiKeyConfigured">
                  <button 
                    type="button" 
                    class="mode-pill" 
                    :class="{ 'is-active': tradeMode === 'signal' }" 
                    @click="tradeMode = 'signal'"
                    title="alert.py tự động quét và mua khi vượt đỉnh ATH"
                  >
                    <i class="fa-solid fa-bolt me-1 text-yellow"></i>Tín Hiệu ATH
                  </button>
                  <button 
                    type="button" 
                    class="mode-pill" 
                    :class="{ 'is-active': tradeMode === 'custom_price' }" 
                    @click="selectCustomPriceMode"
                    title="Đặt lệnh chờ mua khi giá thị trường chạm mức chỉ định"
                  >
                    <i class="fa-solid fa-crosshairs me-1 text-cyan"></i>Giá Chỉ Định
                  </button>
                  <button 
                    type="button" 
                    class="mode-pill mode-pill--market" 
                    :class="{ 'is-active': tradeMode === 'market_now' }" 
                    @click="tradeMode = 'market_now'"
                    title="Khớp lệnh Market Buy ngay lập tức trên sàn"
                  >
                    <i class="fa-solid fa-bolt-lightning me-1 text-green"></i>Vào Lệnh Ngay
                  </button>
                </div>

                <!-- Available Balance -->
                <div class="balance-display d-flex align-items-center gap-1.5" v-if="apiKeyConfigured">
                  <span class="text-muted small">Khả dụng:</span>
                  <span class="balance-amount font-bold text-cyan">{{ formatNumber(exchangeBalance.free_usdt) }} USDT</span>
                  <button type="button" class="btn-refresh-balance" @click="fetchExchangeBalance" :disabled="loadingBalance" title="Làm mới số dư">
                    <i class="fa-solid fa-rotate" :class="{ 'fa-spin': loadingBalance }"></i>
                  </button>
                </div>

                <!-- Budget Input & Quick % Buttons -->
                <div class="budget-input-wrap d-flex align-items-center gap-1" v-if="apiKeyConfigured">
                  <div class="input-with-suffix">
                    <input 
                      type="number" 
                      v-model.number="orderBudget" 
                      class="budget-input"
                      :class="{ 'is-invalid': isBudgetExceeded }"
                      placeholder="Vốn vào lệnh" 
                      min="5" 
                      :max="exchangeBalance.free_usdt"
                      step="1"
                    />
                    <span class="input-suffix">USDT</span>
                  </div>

                  <div class="quick-pct-btns">
                    <button type="button" class="quick-pct-btn" @click="setBudgetPct(25)">25%</button>
                    <button type="button" class="quick-pct-btn" @click="setBudgetPct(50)">50%</button>
                    <button type="button" class="quick-pct-btn" @click="setBudgetPct(100)">MAX</button>
                  </div>
                </div>

                <!-- Trigger Price Input (When mode is custom_price) -->
                <div class="trigger-price-wrap d-flex align-items-center gap-1" v-if="apiKeyConfigured && tradeMode === 'custom_price'">
                  <div class="input-with-suffix">
                    <input 
                      type="number" 
                      v-model.number="customTriggerPrice" 
                      class="budget-input trigger-input"
                      placeholder="Giá kích hoạt mua" 
                      step="any"
                      min="0"
                    />
                    <span class="input-suffix">$</span>
                  </div>
                </div>

                <!-- Action Buttons depending on mode -->
                <template v-if="apiKeyConfigured">
                  <!-- Mode 1: Signal ATH Auto Trade -->
                  <template v-if="tradeMode === 'signal'">
                    <button 
                      v-if="!isSymbolAutoTradeActive"
                      type="button" 
                      class="btn-place-order"
                      :disabled="isConfiguringAutoTrade || orderBudget <= 0 || isBudgetExceeded || !isTradableOnExchange"
                      @click="enableAutoTradeForSymbol"
                      :title="!isTradableOnExchange ? 'Mã này không được hỗ trợ giao dịch trên sàn' : (isBudgetExceeded ? 'Số tiền vượt quá số dư khả dụng' : 'alert.py sẽ tự động vào lệnh Mua khi giá phá đỉnh ATH và tự động quản lý cắt lỗ -2%')"
                    >
                      <i class="fa-solid fa-robot me-1"></i>
                      <span>{{ isConfiguringAutoTrade ? 'Đang kích hoạt...' : `⚡ BẬT AUTO TRADE ($${orderBudget || 0} | SL: -2%)` }}</span>
                    </button>

                    <div v-else class="d-flex align-items-center gap-1.5">
                      <span class="badge bg-success bg-opacity-25 text-success border border-success border-opacity-25 py-1 px-2.5 font-bold" style="font-size: 0.78rem;">
                        <i class="fa-solid fa-radar me-1 fa-spin"></i> Đang Chờ Tín Hiệu (Vốn: ${{ orderBudget }} | SL: -2%)
                      </span>
                      <button 
                        type="button" 
                        class="btn-cancel-auto-trade"
                        :disabled="isConfiguringAutoTrade"
                        @click="disableAutoTradeForSymbol"
                        title="Tắt chế độ tự động vào lệnh cho mã này"
                      >
                        Tắt
                      </button>
                    </div>
                  </template>

                  <!-- Mode 2: Trigger Price Order -->
                  <template v-else-if="tradeMode === 'custom_price'">
                    <button 
                      type="button" 
                      class="btn-place-order btn-trigger-order"
                      :disabled="isConfiguringAutoTrade || orderBudget <= 0 || isBudgetExceeded || customTriggerPrice <= 0 || !isTradableOnExchange"
                      @click="placeCustomPriceOrder"
                      :title="!isTradableOnExchange ? 'Mã này không được hỗ trợ giao dịch trên sàn' : `alert.py sẽ tự động mua khi giá >= $${customTriggerPrice} và quản lý SL -2%`"
                    >
                      <i class="fa-solid fa-crosshairs me-1"></i>
                      <span>{{ isConfiguringAutoTrade ? 'Đang lưu...' : `🎯 ĐẶT LỆNH THEO GIÁ ($${orderBudget || 0} | Trigger: $${formatNumber(customTriggerPrice)})` }}</span>
                    </button>
                  </template>

                  <!-- Mode 3: Market Buy Now -->
                  <template v-else-if="tradeMode === 'market_now'">
                    <button 
                      type="button" 
                      class="btn-place-order btn-market-buy-now"
                      :disabled="isPlacingMarketOrder || orderBudget <= 0 || isBudgetExceeded || !isTradableOnExchange"
                      @click="placeDirectMarketBuy"
                      :title="!isTradableOnExchange ? 'Mã này không được hỗ trợ giao dịch trên sàn' : 'Gửi lệnh Market Buy trực tiếp lên sàn Binance ngay bây giờ với SL -2%'"
                    >
                      <i class="fa-solid fa-bolt-lightning me-1"></i>
                      <span>{{ isPlacingMarketOrder ? 'Đang mua...' : `🚀 MUA NGAY LẬP TỨC ($${orderBudget || 0} | SL: -2%)` }}</span>
                    </button>
                  </template>
                </template>

                <!-- Prompt when Key not configured -->
                <div v-else class="text-warning small d-flex align-items-center gap-1">
                  <i class="fa-solid fa-triangle-exclamation"></i>
                  <span>Chưa có API Key. Bấm "🔑 Nhập API Key" để kích hoạt Live Trade.</span>
                </div>
              </div>
            </template>
          </div>

          <!-- Symbol Tradable Validation Warning -->
          <div v-if="!currentOpenPosition && !isTradableOnExchange" class="unsupported-symbol-banner">
            <i class="fa-solid fa-triangle-exclamation me-1.5 text-yellow"></i>
            <span>Mã <strong>{{ currentActiveSymbol }}</strong> ({{ activeSlot?.assetType?.toUpperCase() || 'CHỨNG KHOÁN / NGOẠI HỐI' }}) không hỗ trợ Live Trade trên sàn {{ activeExchange.toUpperCase() }} Spot. Chỉ hỗ trợ các cặp Crypto USDT.</span>
          </div>

          <!-- Real-Time Validation Warning -->
          <div v-if="!currentOpenPosition && apiKeyConfigured && isTradableOnExchange && isBudgetExceeded" class="budget-error-banner">
            ⚠️ Số tiền vào lệnh ({{ orderBudget }} USDT) vượt quá số dư khả dụng ({{ formatNumber(exchangeBalance.free_usdt) }} USDT)!
          </div>
        </div>

        <!-- Toast Feedback Notification -->
        <div v-if="toastMessage" class="modal-toast" :class="`toast-${toastType}`">
          {{ toastMessage }}
        </div>

        <!-- Multi-Chart Grid Container -->
        <div class="modal-charts-grid-wrapper custom-scrollbar">
          <div 
            class="charts-grid" 
            :class="`grid-count-${splitCount}`"
          >
            <div 
              v-for="(slot, index) in activeSlots" 
              :key="`chart-slot-${index}`"
              class="chart-cell"
              :class="{ 'is-active-cell': activeSlotIndex === index }"
              @click="activeSlotIndex = index"
            >
              <!-- Cell Header with Dedicated Symbol Input Bar & Engine Toggle -->
              <div class="cell-header">
                <div class="cell-info d-flex align-items-center gap-1">
                  <span class="cell-num-badge">#{{ index + 1 }}</span>

                  <!-- Engine Toggle on the left (TV | VS) -->
                  <div class="cell-engine-toggle" title="Chuyển đổi giữa TradingView và Vietstock">
                    <button 
                      type="button" 
                      class="engine-btn" 
                      :class="{ 'is-active': slot.chartEngine === 'tradingview' }" 
                      @click.stop="setSlotEngine(index, 'tradingview')"
                      title="Dùng biểu đồ TradingView"
                    >
                      TV
                    </button>
                    <button 
                      type="button" 
                      class="engine-btn" 
                      :class="{ 'is-active': slot.chartEngine === 'vietstock' }" 
                      @click.stop="setSlotEngine(index, 'vietstock')"
                      title="Dùng biểu đồ Vietstock"
                    >
                      VS
                    </button>
                  </div>

                  <span class="cell-symbol-title" :title="slot.symbol">{{ slot.symbol }}</span>
                  <span class="cell-type-badge" v-if="slot.assetType">{{ slot.assetType }}</span>
                </div>

                <!-- Dedicated Symbol Textbox & Button for this chart -->
                <div class="cell-search-bar" @click.stop>
                  <div class="cell-input-group position-relative">
                    <svg class="cell-search-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="11" cy="11" r="8"></circle>
                      <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                    <input 
                      type="text" 
                      class="cell-symbol-input"
                      v-model="slot.tempInput"
                      @focus="$event.target.select()"
                      @click="$event.target.select()"
                      @mouseup.prevent="$event.target.select()"
                      @keydown.enter.stop.prevent="updateCellSymbol(index, $event)"
                      @keyup.enter.stop.prevent="focusAndSelectInput($event.target)"
                      @input="slot.tempInput = $event.target.value.toUpperCase()"
                      :placeholder="`Mã Chart #${index + 1}...`"
                      title="Nhập mã symbol cho chart này và nhấn Xem hoặc Enter"
                    />
                    <button 
                      v-if="slot.tempInput"
                      type="button"
                      class="cell-input-clear-btn"
                      @click.stop="slot.tempInput = ''"
                      title="Xóa"
                    >
                      <i class="fa-solid fa-xmark"></i>
                    </button>
                  </div>
                  <button 
                    type="button"
                    class="cell-view-btn" 
                    @click.stop="updateCellSymbol(index)" 
                    title="Cập nhật chart này"
                  >
                    <i class="fa-solid fa-arrow-right d-sm-none"></i>
                    <span class="d-none d-sm-inline">Xem</span>
                  </button>
                </div>
              </div>

              <!-- Chart Body -->
              <div class="cell-body">
                <template v-if="slot.chartEngine === 'vietstock'">
                  <iframe
                    :key="`vs-${slot.resolvedSymbol}`"
                    :src="`https://stockchart.vietstock.vn/?stockcode=${slot.resolvedSymbol}`"
                    width="100%"
                    height="100%"
                    frameborder="0"
                    allowfullscreen
                    class="vnstock-iframe"
                  ></iframe>
                </template>
                <template v-else>
                  <TradingViewChart 
                    :key="`tv-${slot.resolvedSymbol}`" 
                    :coin="slot.resolvedSymbol" 
                    height="100%" 
                  />
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- API KEY CONFIG MODAL POPUP -->
    <div v-if="showApiKeyModal" class="modal-backdrop-custom" @click.self="showApiKeyModal = false">
      <div class="stk-modal api-key-modal p-4" @click.stop>
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2 border-secondary border-opacity-25">
          <h5 class="m-0 text-white font-bold d-flex align-items-center gap-2">
            <i class="fa-solid fa-key text-cyan"></i> Cấu Hình API Key Sàn Giao Dịch
          </h5>
          <button type="button" class="btn-modal-close-custom" @click="showApiKeyModal = false">✕</button>
        </div>

        <!-- Exchange Tabs in Modal -->
        <div class="exchange-modal-tabs mb-3 d-flex gap-2">
          <button 
            type="button" 
            class="btn-ex-tab"
            :class="{ active: activeExchange === 'binance' }"
            @click="activeExchange = 'binance'"
          >
            🟡 Binance
          </button>
          <button 
            type="button" 
            class="btn-ex-tab"
            :class="{ active: activeExchange === 'okx' }"
            @click="activeExchange = 'okx'"
          >
            ⚪ OKX
          </button>
          <button 
            type="button" 
            class="btn-ex-tab"
            :class="{ active: activeExchange === 'bybit' }"
            @click="activeExchange = 'bybit'"
          >
            🟠 Bybit
          </button>
        </div>

        <form @submit.prevent="saveApiKey">
          <div v-if="activeExchange === 'binance'" class="form-group mb-3">
            <label class="stk-label">Binance API Key</label>
            <input type="text" v-model="apiKeyForm.binance_api_key" class="stk-input" placeholder="Nhập Binance API Key..." required />
            <label class="stk-label mt-2">Binance API Secret</label>
            <input type="password" v-model="apiKeyForm.binance_api_secret" class="stk-input" placeholder="Nhập Binance Secret Key..." required />
          </div>

          <div v-else-if="activeExchange === 'okx'" class="form-group mb-3">
            <label class="stk-label">OKX API Key</label>
            <input type="text" v-model="apiKeyForm.okx_api_key" class="stk-input" placeholder="Nhập OKX API Key..." required />
            <label class="stk-label mt-2">OKX API Secret</label>
            <input type="password" v-model="apiKeyForm.okx_api_secret" class="stk-input" placeholder="Nhập OKX Secret Key..." required />
            <label class="stk-label mt-2">OKX Passphrase</label>
            <input type="password" v-model="apiKeyForm.okx_passphrase" class="stk-input" placeholder="Nhập OKX Passphrase..." />
          </div>

          <div v-else-if="activeExchange === 'bybit'" class="form-group mb-3">
            <label class="stk-label">Bybit API Key</label>
            <input type="text" v-model="apiKeyForm.bybit_api_key" class="stk-input" placeholder="Nhập Bybit API Key..." required />
            <label class="stk-label mt-2">Bybit API Secret</label>
            <input type="password" v-model="apiKeyForm.bybit_api_secret" class="stk-input" placeholder="Nhập Bybit Secret Key..." required />
          </div>

          <p class="text-muted small mb-3" style="font-size: 0.76rem;">
            🔒 Thông tin API Key được mã hóa an toàn trên Server để phục vụ việc truy vấn số dư và tự động vào/thoát lệnh theo tín hiệu của <strong>alert.py</strong>. Vui lòng <strong>tắt quyền rút tiền (Withdrawal)</strong> khi tạo API Key trên sàn.
          </p>

          <div class="d-flex justify-content-end gap-2">
            <button type="button" class="stk-btn stk-btn--outline" @click="showApiKeyModal = false">Hủy</button>
            <button type="submit" class="stk-btn stk-btn--primary" :disabled="isSavingKey">
              <span>{{ isSavingKey ? 'Đang lưu...' : '💾 Lưu API Key' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import TradingViewChart from './TradingViewChart.vue';

export default {
  name: 'MultiChartModal',
  components: {
    TradingViewChart
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    initialSymbol: {
      type: String,
      default: 'BTCUSDT'
    },
    initialAsset: {
      type: Object,
      default: () => null
    }
  },
  emits: ['close', 'update:visible'],
  setup(props, { emit }) {
    const splitCount = ref(1);
    const isMaximized = ref(false);
    const isMinimized = ref(false);
    const activeSlotIndex = ref(0);

    // Auto Live Trade State
    const isRealTradeOpen = ref(false);
    const activeExchange = ref('binance');
    const apiKeyConfigured = ref(false);
    const loadingBalance = ref(false);
    const exchangeBalance = ref({ free_usdt: 0, total_units: 0, current_price: 0, configured: false });
    const orderBudget = ref(100);
    const tradeMode = ref('signal'); // 'signal' | 'custom_price' | 'market_now'
    const customTriggerPrice = ref(0);
    const isPlacingMarketOrder = ref(false);
    const activePositions = ref([]);
    const watchlistItems = ref([]);
    const showApiKeyModal = ref(false);
    const isSavingKey = ref(false);
    const isConfiguringAutoTrade = ref(false);
    const isClosingOrder = ref(false);
    const toastMessage = ref('');
    const toastType = ref('success');
    let toastTimeout = null;

    const apiKeyForm = ref({
      binance_api_key: '',
      binance_api_secret: '',
      okx_api_key: '',
      okx_api_secret: '',
      okx_passphrase: '',
      bybit_api_key: '',
      bybit_api_secret: ''
    });

    const defaultSymbols = [
      { symbol: 'BTCUSDT', type: 'crypto', resolved: 'BINANCE:BTCUSDT' },
      { symbol: 'ETHUSDT', type: 'crypto', resolved: 'BINANCE:ETHUSDT' },
      { symbol: 'SOLUSDT', type: 'crypto', resolved: 'BINANCE:SOLUSDT' },
      { symbol: 'BNBUSDT', type: 'crypto', resolved: 'BINANCE:BNBUSDT' },
      { symbol: 'XRPUSDT', type: 'crypto', resolved: 'BINANCE:XRPUSDT' },
      { symbol: 'DOGEUSDT', type: 'crypto', resolved: 'BINANCE:DOGEUSDT' },
      { symbol: 'XAUUSD', type: 'commodities', resolved: 'OANDA:XAUUSD' },
      { symbol: 'SPX', type: 'stock', resolved: 'FOREXCOM:SPXUSD' }
    ];

    // Array of 8 slots
    const slots = ref(
      Array.from({ length: 8 }, (_, i) => {
        const item = defaultSymbols[i];
        const sym = item?.symbol || 'BTCUSDT';
        const type = item?.type || 'crypto';
        return {
          symbol: sym,
          tempInput: sym,
          assetType: type,
          isVnStock: false,
          chartEngine: 'tradingview',
          resolvedSymbol: item?.resolved || 'BINANCE:BTCUSDT'
        };
      })
    );

    const getAuthHeaders = () => {
      const token = localStorage.getItem('token');
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      return headers;
    };

    const formatNumber = (num) => {
      if (num === null || num === undefined || isNaN(num)) return '0';
      return Number(num).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    };

    const showToast = (msg, type = 'success') => {
      toastMessage.value = msg;
      toastType.value = type;
      if (toastTimeout) clearTimeout(toastTimeout);
      toastTimeout = setTimeout(() => {
        toastMessage.value = '';
      }, 4500);
    };

    const currentActiveSymbol = computed(() => {
      const current = slots.value[activeSlotIndex.value]?.symbol || props.initialSymbol || 'BTCUSDT';
      return String(current).toUpperCase().trim();
    });

    const currentWatchlistItem = computed(() => {
      const raw = currentActiveSymbol.value;
      const clean = raw.replace('/', '').replace('USDT', '');
      return watchlistItems.value.find(w => 
        w.symbol.toUpperCase() === raw || 
        w.symbol.toUpperCase() === clean || 
        w.symbol.toUpperCase() === `${clean}USDT`
      );
    });

    const isSymbolAutoTradeActive = computed(() => {
      return !!(currentWatchlistItem.value && currentWatchlistItem.value.is_real_trading && currentWatchlistItem.value.is_active);
    });

    const currentOpenPosition = computed(() => {
      const raw = currentActiveSymbol.value;
      const clean = raw.replace('/', '').replace('USDT', '');
      return activePositions.value.find(p => 
        p.status === 'OPEN' && (
          p.symbol.toUpperCase() === raw || 
          p.symbol.toUpperCase() === clean || 
          p.symbol.toUpperCase() === `${clean}USDT`
        )
      );
    });

    const isTradableOnExchange = computed(() => {
      const slot = slots.value[activeSlotIndex.value];
      if (slot) {
        if (slot.isVnStock || slot.assetType === 'stock_vn') return false;
        if (['forex', 'commodities', 'stock', 'stock_us'].includes(slot.assetType)) return false;
      }
      if (exchangeBalance.value) {
        if (exchangeBalance.value.is_tradable === false) return false;
        if (exchangeBalance.value.current_price <= 0 && !loadingBalance.value) return false;
      }
      return true;
    });

    const isBudgetExceeded = computed(() => {
      return apiKeyConfigured.value && orderBudget.value > (exchangeBalance.value.free_usdt || 0);
    });

    const setBudgetPct = (pct) => {
      const available = exchangeBalance.value.free_usdt || 0;
      if (available <= 0) {
        orderBudget.value = 0;
        return;
      }
      const amt = Math.floor(available * (pct / 100));
      orderBudget.value = amt > 0 ? amt : Number((available * (pct / 100)).toFixed(2));
    };

    const fetchTradingSettings = async () => {
      try {
        const res = await fetch('/api/trading-settings', { headers: getAuthHeaders() });
        if (res.ok) {
          const data = await res.json();
          if (data && data.settings) {
            const s = data.settings;
            apiKeyForm.value.binance_api_key = s.binance_api_key || '';
            apiKeyForm.value.binance_api_secret = s.binance_api_secret || '';
            apiKeyForm.value.okx_api_key = s.okx_api_key || '';
            apiKeyForm.value.okx_api_secret = s.okx_api_secret || '';
            apiKeyForm.value.okx_passphrase = s.okx_passphrase || '';
            apiKeyForm.value.bybit_api_key = s.bybit_api_key || '';
            apiKeyForm.value.bybit_api_secret = s.bybit_api_secret || '';

            if (activeExchange.value === 'binance') {
              apiKeyConfigured.value = !!(s.binance_api_key && s.binance_api_secret);
            } else if (activeExchange.value === 'okx') {
              apiKeyConfigured.value = !!(s.okx_api_key && s.okx_api_secret);
            } else if (activeExchange.value === 'bybit') {
              apiKeyConfigured.value = !!(s.bybit_api_key && s.bybit_api_secret);
            }
          }
        }
      } catch (err) {
        console.warn('Error fetching trading settings:', err);
      }
    };

    const fetchExchangeBalance = async () => {
      loadingBalance.value = true;
      try {
        const sym = currentActiveSymbol.value;
        const res = await fetch(`/breakout/exchange-balance?symbol=${encodeURIComponent(sym)}&asset_type=crypto`, {
          headers: getAuthHeaders()
        });
        if (res.ok) {
          const data = await res.json();
          exchangeBalance.value = data;
          if (data.configured !== undefined) {
            apiKeyConfigured.value = data.configured;
          }
          if (currentWatchlistItem.value && currentWatchlistItem.value.initial_budget > 0) {
            orderBudget.value = currentWatchlistItem.value.initial_budget;
          } else if (data.free_usdt > 0 && orderBudget.value <= 0) {
            orderBudget.value = Math.min(100, Math.floor(data.free_usdt));
          }
        }
      } catch (err) {
        console.warn('Error fetching exchange balance:', err);
      } finally {
        loadingBalance.value = false;
      }
    };

    const fetchPositions = async () => {
      try {
        const res = await fetch('/breakout/positions', { headers: getAuthHeaders() });
        if (res.ok) {
          const data = await res.json();
          activePositions.value = Array.isArray(data) ? data : (data?.data || []);
        }
      } catch (err) {
        console.warn('Error fetching breakout positions:', err);
      }
    };

    const fetchWatchlist = async () => {
      try {
        const res = await fetch('/breakout/watchlist', { headers: getAuthHeaders() });
        if (res.ok) {
          const data = await res.json();
          watchlistItems.value = Array.isArray(data) ? data : (data?.data || []);
          if (currentWatchlistItem.value && currentWatchlistItem.value.initial_budget > 0) {
            orderBudget.value = currentWatchlistItem.value.initial_budget;
          }
        }
      } catch (err) {
        console.warn('Error fetching watchlist items:', err);
      }
    };

    const toggleRealTrade = () => {
      isRealTradeOpen.value = !isRealTradeOpen.value;
      if (isRealTradeOpen.value) {
        fetchTradingSettings();
        fetchExchangeBalance();
        fetchPositions();
        fetchWatchlist();
      }
    };

    const selectExchange = (ex) => {
      activeExchange.value = ex;
      fetchTradingSettings();
      fetchExchangeBalance();
    };

    const saveApiKey = async () => {
      isSavingKey.value = true;
      try {
        const res = await fetch('/api/trading-settings/update', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify(apiKeyForm.value)
        });
        if (res.ok) {
          showToast(`💾 Đã lưu cấu hình API Key ${activeExchange.value.toUpperCase()} thành công!`, 'success');
          showApiKeyModal.value = false;
          apiKeyConfigured.value = true;
          await fetchExchangeBalance();
        } else {
          const errData = await res.json();
          showToast(`⚠️ Không thể lưu: ${errData.message || 'Lỗi server'}`, 'danger');
        }
      } catch (err) {
        console.error('Error saving API Key:', err);
        showToast('Lỗi kết nối khi lưu API Key!', 'danger');
      } finally {
        isSavingKey.value = false;
      }
    };

    const enableAutoTradeForSymbol = async () => {
      if (!isTradableOnExchange.value) {
        showToast(`⚠️ Mã ${currentActiveSymbol.value} không được hỗ trợ giao dịch trên ${activeExchange.value.toUpperCase()} Spot (chỉ hỗ trợ Crypto USDT)!`, 'danger');
        return;
      }
      if (orderBudget.value <= 0) return;
      if (isBudgetExceeded.value) {
        showToast('Số tiền vào lệnh vượt quá số dư khả dụng!', 'danger');
        return;
      }
      isConfiguringAutoTrade.value = true;
      try {
        const sym = currentActiveSymbol.value;
        const cleanSym = sym.replace('/', '').replace('USDT', '').trim() + 'USDT';
        
        const payload = {
          id: currentWatchlistItem.value?.id || null,
          symbol: cleanSym,
          asset_type: 'crypto',
          name: cleanSym,
          initial_budget: orderBudget.value,
          step_pct: 1.0,
          pyramid_ratio: 0.67,
          sl_pct: 2.0,
          sl_mode: 'TRAILING_PEAK',
          is_active: true,
          is_real_trading: true,
          notes: 'Kích hoạt Auto Trade theo tín hiệu từ Popup Chart'
        };

        const res = await fetch('/breakout/watchlist', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          showToast(`🟢 ĐÃ KÍCH HOẠT AUTO TRADE: alert.py sẽ tự động vào lệnh Mua cho ${cleanSym} khi có tín hiệu phá đỉnh (Vốn $${orderBudget.value}, SL -2%)!`, 'success');
          await Promise.all([fetchWatchlist(), fetchPositions(), fetchExchangeBalance()]);
        } else {
          const errData = await res.json();
          showToast(`⚠️ Không thể kích hoạt: ${errData.message || 'Lỗi lưu watchlist'}`, 'danger');
        }
      } catch (err) {
        console.error('Error enabling auto trade:', err);
        showToast('Lỗi kết nối khi bật Auto Trade!', 'danger');
      } finally {
        isConfiguringAutoTrade.value = false;
      }
    };

    const disableAutoTradeForSymbol = async () => {
      if (!currentWatchlistItem.value) return;
      isConfiguringAutoTrade.value = true;
      try {
        const sym = currentActiveSymbol.value;
        const cleanSym = sym.replace('/', '').replace('USDT', '').trim() + 'USDT';
        
        const payload = {
          ...currentWatchlistItem.value,
          symbol: cleanSym,
          is_real_trading: false
        };

        const res = await fetch('/breakout/watchlist', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          showToast(`⏸️ Đã tắt Auto Trade cho ${cleanSym}.`, 'success');
          await fetchWatchlist();
        }
      } catch (err) {
        console.error('Error disabling auto trade:', err);
      } finally {
        isConfiguringAutoTrade.value = false;
      }
    };

    const closeActivePosition = async (posId) => {
      if (!confirm('⚠️ Bạn có chắc muốn THOÁT VỊ THẾ NGAY LẬP TỨC theo giá thị trường không?')) return;
      isClosingOrder.value = true;
      try {
        const res = await fetch('/breakout/positions/close', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify({ position_id: posId, reason: 'MANUAL_CLOSE' })
        });
        if (res.ok) {
          showToast('🎉 Đã thoát vị thế thành công!', 'success');
          await Promise.all([fetchPositions(), fetchExchangeBalance(), fetchWatchlist()]);
        } else {
          const errData = await res.json();
          showToast(`⚠️ Không thể đóng lệnh: ${errData.message || 'Lỗi server'}`, 'danger');
        }
      } catch (err) {
        console.error('Error closing position:', err);
        showToast('Lỗi kết nối khi đóng lệnh!', 'danger');
      } finally {
        isClosingOrder.value = false;
      }
    };

    const selectCustomPriceMode = () => {
      tradeMode.value = 'custom_price';
      if (!customTriggerPrice.value || customTriggerPrice.value <= 0) {
        if (exchangeBalance.value?.current_price > 0) {
          customTriggerPrice.value = exchangeBalance.value.current_price;
        } else if (currentWatchlistItem.value?.ath_price > 0) {
          customTriggerPrice.value = currentWatchlistItem.value.ath_price;
        }
      }
    };

    const placeCustomPriceOrder = async () => {
      if (!isTradableOnExchange.value) {
        showToast(`⚠️ Mã ${currentActiveSymbol.value} không được hỗ trợ giao dịch trên ${activeExchange.value.toUpperCase()} Spot (chỉ hỗ trợ Crypto USDT)!`, 'danger');
        return;
      }
      if (orderBudget.value <= 0) return;
      if (isBudgetExceeded.value) {
        showToast('Số tiền vào lệnh vượt quá số dư khả dụng!', 'danger');
        return;
      }
      if (!customTriggerPrice.value || customTriggerPrice.value <= 0) {
        showToast('Vui lòng nhập mức giá kích hoạt hợp lệ!', 'danger');
        return;
      }

      isConfiguringAutoTrade.value = true;
      try {
        const sym = currentActiveSymbol.value;
        const cleanSym = sym.replace('/', '').replace('USDT', '').trim() + 'USDT';

        const payload = {
          id: currentWatchlistItem.value?.id || null,
          symbol: cleanSym,
          asset_type: 'crypto',
          name: cleanSym,
          initial_budget: orderBudget.value,
          ath_price: customTriggerPrice.value,
          step_pct: 1.0,
          pyramid_ratio: 0.67,
          sl_pct: 2.0,
          sl_mode: 'TRAILING_PEAK',
          is_active: true,
          is_real_trading: true,
          notes: `Lệnh chờ kích hoạt khi giá >= $${customTriggerPrice.value} từ Popup Chart`
        };

        const res = await fetch('/breakout/watchlist', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          showToast(`🎯 ĐÃ ĐẶT LỆNH CHỜ: alert.py sẽ tự động Mua ${cleanSym} khi giá chạm $${formatNumber(customTriggerPrice.value)} (Vốn $${orderBudget.value}, SL -2%)!`, 'success');
          await Promise.all([fetchWatchlist(), fetchPositions(), fetchExchangeBalance()]);
        } else {
          const errData = await res.json();
          showToast(`⚠️ Không thể đặt lệnh: ${errData.message || 'Lỗi lưu lệnh chờ'}`, 'danger');
        }
      } catch (err) {
        console.error('Error placing custom price order:', err);
        showToast('Lỗi kết nối khi đặt lệnh theo giá!', 'danger');
      } finally {
        isConfiguringAutoTrade.value = false;
      }
    };

    const placeDirectMarketBuy = async () => {
      if (!isTradableOnExchange.value) {
        showToast(`⚠️ Mã ${currentActiveSymbol.value} không được hỗ trợ giao dịch trên ${activeExchange.value.toUpperCase()} Spot (chỉ hỗ trợ Crypto USDT)!`, 'danger');
        return;
      }
      if (orderBudget.value <= 0) return;
      if (isBudgetExceeded.value) {
        showToast('Số tiền vào lệnh vượt quá số dư khả dụng!', 'danger');
        return;
      }
      if (!confirm(`🚀 XÁC NHẬN MUA NGAY LẬP TỨC ${currentActiveSymbol.value} với số vốn $${orderBudget.value} (SL: -2%)?`)) return;

      isPlacingMarketOrder.value = true;
      try {
        const sym = currentActiveSymbol.value;
        const cleanSym = sym.replace('/', '').replace('USDT', '').trim() + 'USDT';

        const res = await fetch('/breakout/order/market-buy', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify({
            symbol: cleanSym,
            amount_usd: orderBudget.value,
            sl_pct: 2.0,
            sl_mode: 'TRAILING',
            is_real_trading: true
          })
        });

        if (res.ok) {
          const data = await res.json();
          showToast(`🎉 ${data.message || 'Khớp lệnh mua thành công!'}`, 'success');
          await Promise.all([fetchPositions(), fetchExchangeBalance(), fetchWatchlist()]);
        } else {
          const errData = await res.json();
          showToast(`⚠️ Không thể khớp lệnh: ${errData.message || 'Lỗi server'}`, 'danger');
        }
      } catch (err) {
        console.error('Error placing market order:', err);
        showToast('Lỗi kết nối khi đặt lệnh mua ngay!', 'danger');
      } finally {
        isPlacingMarketOrder.value = false;
      }
    };

    const resolveVnStockCode = (code) => {
      const upper = String(code || '').trim().toUpperCase();
      if (upper === 'VN30FM1') return 'VN30F1M';
      if (upper === 'UPCOMINDEX') return 'UPCOMINDEX';
      return upper;
    };

    const checkIsVnStock = (sym, type, asset) => {
      const raw = String(sym || '').trim().toUpperCase();
      if (!raw) return false;
      const t = String(type || asset?.asset_type || asset?.assetType || '').toLowerCase();

      // Explicit VN stock types
      if (t === 'stock_vn' || t === 'stock_vietnam') return true;
      
      // Explicit US stock indicators
      if (t === 'stock_us' || asset?.isUS) return false;
      if (asset?.message && (asset.message.includes('Stock US') || asset.message.includes('US Stock'))) return false;

      // Common US Stock tickers & market indices -> TradingView
      const commonUS = [
        'AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'META', 'AMD', 'NFLX', 
        'INTC', 'COIN', 'PLTR', 'BABA', 'NIO', 'SPY', 'QQQ', 'IWM', 'DIA', 'V', 'MA', 
        'JPM', 'BAC', 'DIS', 'BA', 'XOM', 'CVX', 'WMT', 'PG', 'JNJ', 'UNH', 'HD', 'LLY'
      ];
      if (commonUS.includes(raw) || raw.includes(':') || raw === 'SPX' || raw === 'US30' || raw === 'NDX') {
        return false;
      }

      // Vietnamese indices & derivatives
      if (['VNINDEX', 'VN30', 'VN30F1M', 'VN30FM1', 'HNXINDEX', 'UPCOMINDEX'].includes(raw)) {
        return true;
      }

      // Standard Vietnamese 3-letter stock tickers (e.g. VIC, VCB, HPG, FPT, VHM, SSI, etc.)
      const majorCrypto = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOT', 'DOGE', 'AVAX', 'LINK', 'UNI', 'LTC', 'BCH', 'TRX', 'APT', 'SUI', 'ARB', 'OP', 'TIA', 'SEI', 'INJ', 'FTM', 'NEAR', 'PEPE', 'SHIB', 'TON', 'XLM', 'ATOM', 'FIL', 'ETC', 'HBAR', 'ICP', 'RNDR', 'FET', 'WIF', 'BONK', 'FLOKI'];
      const majorForex = ['EUR', 'USD', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD', 'DXY', 'CNY', 'VND', 'SGD', 'HKD'];
      const majorCommodity = ['GOLD', 'SILVER', 'USOIL', 'UKOIL', 'BRENT', 'WTI', 'NATGAS', 'COPPER'];
      if (/^[A-Z]{3}$/.test(raw) && !majorCrypto.includes(raw) && !majorForex.includes(raw) && !majorCommodity.includes(raw)) {
        return true;
      }

      return false;
    };

    const resolveChartSymbol = (rawSymbol, assetType) => {
      const raw = String(rawSymbol || '').trim().toUpperCase();
      if (!raw) return 'BINANCE:BTCUSDT';

      if (raw.includes(':')) {
        return raw;
      }

      const clean = raw.replace('/', '').replace('-', '').trim();
      const type = String(assetType || '').toLowerCase();

      if (type === 'forex' || ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'EURJPY', 'GBPJPY', 'DXY'].includes(clean)) {
        if (clean === 'DXY') return 'CAPITALCOM:DXY';
        return `FX:${clean}`;
      }

      if (type === 'commodities' || type === 'commodity' || ['XAUUSD', 'GOLD', 'XAGUSD', 'SILVER', 'USOIL', 'UKOIL', 'BRENT', 'WTI', 'COPPER', 'NATGAS'].includes(clean)) {
        if (clean === 'GOLD' || clean === 'XAUUSD' || clean === 'GC') return 'OANDA:XAUUSD';
        if (clean === 'SILVER' || clean === 'XAGUSD' || clean === 'SI') return 'OANDA:XAGUSD';
        if (clean === 'USOIL' || clean === 'WTI' || clean === 'CL') return 'TVC:USOIL';
        if (clean === 'UKOIL' || clean === 'BRENT' || clean === 'BZ') return 'TVC:UKOIL';
        if (clean === 'COPPER' || clean === 'HG') return 'CAPITALCOM:COPPER';
        if (clean === 'NATGAS' || clean === 'NG') return 'TVC:NATGAS';
      }

      if (type === 'stock' || type === 'stock_us' || ['SPX', 'US30', 'DJI', 'NDX', 'NASDAQ', 'NIKKEI', 'NI225', 'DAX', 'DEU40', 'FTSE', 'UK100', 'AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN', 'GOOGL', 'META'].includes(clean)) {
        if (clean === 'SPX') return 'FOREXCOM:SPXUSD';
        if (clean === 'US30' || clean === 'DJI') return 'FOREXCOM:DJI';
        if (clean === 'NDX' || clean === 'NASDAQ') return 'NASDAQ:NDX';
        if (clean === 'NIKKEI' || clean === 'NI225') return 'FOREXCOM:JP225';
        if (clean === 'DAX' || clean === 'DEU40') return 'FOREXCOM:GER40';
        if (clean === 'FTSE' || clean === 'UK100') return 'FOREXCOM:UK100';
        return clean;
      }

      if (type === 'crypto' || clean.endsWith('USDT') || clean.endsWith('BUSD') || clean.endsWith('BTC')) {
        if (clean.endsWith('USDT')) {
          return `BINANCE:${clean}`;
        }
        return `BINANCE:${clean}USDT`;
      }

      if (/^[A-Z0-9]{2,10}$/.test(clean)) {
        return `BINANCE:${clean}USDT`;
      }

      return clean;
    };

    const detectAssetType = (symbol) => {
      const upper = String(symbol || '').trim().toUpperCase();
      if (checkIsVnStock(upper)) {
        return 'stock_vn';
      }
      const forex = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'EURJPY', 'GBPJPY', 'DXY'];
      if (forex.includes(upper)) return 'forex';
      const commodity = ['XAUUSD', 'GOLD', 'XAGUSD', 'SILVER', 'USOIL', 'UKOIL', 'BRENT', 'WTI', 'COPPER', 'NATGAS'];
      if (commodity.includes(upper)) return 'commodities';
      if (upper === 'SPX' || upper === 'US30' || upper === 'DJI' || upper === 'NDX') {
        return 'stock';
      }
      return 'crypto';
    };

    const setSlotSymbol = (index, symbol, type = '', forcedEngine = null) => {
      if (index < 0 || index >= slots.value.length) return;
      const clean = String(symbol || '').trim().toUpperCase();
      if (!clean) return;

      const isVn = checkIsVnStock(clean, type);
      const engine = forcedEngine || (isVn ? 'vietstock' : 'tradingview');
      const inferredType = (engine === 'vietstock') ? 'stock_vn' : (type || detectAssetType(clean));
      const resolved = (engine === 'vietstock') 
        ? resolveVnStockCode(clean) 
        : resolveChartSymbol(clean, inferredType);

      const slot = slots.value[index];
      slot.symbol = clean;
      slot.tempInput = clean;
      slot.assetType = inferredType;
      slot.isVnStock = (engine === 'vietstock');
      slot.chartEngine = engine;
      slot.resolvedSymbol = resolved;

      if (isRealTradeOpen.value) {
        fetchExchangeBalance();
        fetchPositions();
        fetchWatchlist();
      }
    };

    const setSlotEngine = (index, engine) => {
      if (index < 0 || index >= slots.value.length) return;
      const slot = slots.value[index];
      slot.chartEngine = engine;
      slot.isVnStock = (engine === 'vietstock');
      const clean = slot.symbol;
      const inferredType = (engine === 'vietstock') ? 'stock_vn' : detectAssetType(clean);
      slot.assetType = inferredType;
      slot.resolvedSymbol = (engine === 'vietstock') 
        ? resolveVnStockCode(clean) 
        : resolveChartSymbol(clean, inferredType);
    };

    const refreshTradeState = async () => {
      if (!props.visible) return;
      await Promise.all([
        fetchTradingSettings(),
        fetchPositions(),
        fetchWatchlist()
      ]);
      if (currentOpenPosition.value || isSymbolAutoTradeActive.value) {
        isRealTradeOpen.value = true;
      }
      if (isRealTradeOpen.value && apiKeyConfigured.value) {
        fetchExchangeBalance();
      }
    };

    let livePollInterval = null;

    const initInitialSlot = () => {
      let initSym = props.initialAsset?.symbol || props.initialSymbol || '';
      if (!initSym && props.initialAsset?.message) {
        const match = props.initialAsset.message.match(/\[.*?\]\s*([A-Z0-9/.-]+)/i) || props.initialAsset.message.match(/\b([A-Z0-9]{2,10}(?:USDT|USD)?)\b/);
        if (match) initSym = match[1];
      }
      if (!initSym) initSym = 'BTCUSDT';

      initSym = String(initSym).trim().toUpperCase();

      const initType = props.initialAsset?.assetType || props.initialAsset?.asset_type || '';
      const isUS = props.initialAsset?.isUS || initType === 'stock_us' || (props.initialAsset?.message && (props.initialAsset.message.includes('Stock US') || props.initialAsset.message.includes('US Stock')));
      const isVn = !isUS && checkIsVnStock(initSym, initType, props.initialAsset);
      const engine = isVn ? 'vietstock' : 'tradingview';
      setSlotSymbol(0, initSym, initType, engine);

      refreshTradeState();
    };

    watch(() => props.visible, (val) => {
      if (val) {
        isMinimized.value = false;
        initInitialSlot();
        if (livePollInterval) clearInterval(livePollInterval);
        livePollInterval = setInterval(refreshTradeState, 4000);
      } else {
        if (livePollInterval) {
          clearInterval(livePollInterval);
          livePollInterval = null;
        }
      }
    }, { immediate: true });

    watch([() => props.initialSymbol, () => props.initialAsset], () => {
      if (props.visible) {
        isMinimized.value = false;
        initInitialSlot();
      }
    }, { deep: true });

    watch(activeSlotIndex, () => {
      refreshTradeState();
    });

    const activeSlots = computed(() => {
      return slots.value.slice(0, splitCount.value);
    });

    const activeSlot = computed(() => {
      return slots.value[activeSlotIndex.value] || slots.value[0];
    });

    const activeSymbolDisplay = computed(() => {
      return activeSlot.value?.symbol || 'Chart';
    });

    const modalTitle = computed(() => {
      if (props.initialAsset?.name && splitCount.value === 1) {
        return props.initialAsset.name;
      }
      return `${activeSymbolDisplay.value} - Multi-Chart Studio`;
    });

    const activeSubtitle = computed(() => {
      return `Hiển thị ${splitCount.value} biểu đồ đồng thời • Nhấp vào từng ô để đổi mã`;
    });

    const setSplitCount = (count) => {
      splitCount.value = count;
      if (activeSlotIndex.value >= count) {
        activeSlotIndex.value = 0;
      }
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
      }, 100);
    };

    const toggleMaximize = () => {
      isMaximized.value = !isMaximized.value;
      if (isMinimized.value) isMinimized.value = false;
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
      }, 100);
    };

    const toggleMinimize = () => {
      isMinimized.value = !isMinimized.value;
    };

    const closeModal = () => {
      emit('close');
      emit('update:visible', false);
      isMinimized.value = false;
      if (toastTimeout) clearTimeout(toastTimeout);
    };

    const handleBackdropClick = () => {
      closeModal();
    };

    const focusAndSelectInput = (input) => {
      if (!input) return;
      input.focus();
      input.setSelectionRange(0, input.value.length);
    };

    const updateCellSymbol = (index, event) => {
      const slot = slots.value[index];
      const input = event?.currentTarget;
      if (slot && slot.tempInput && slot.tempInput.trim()) {
        const clean = slot.tempInput.trim().toUpperCase();
        setSlotSymbol(index, clean, '', slot.chartEngine);
      }
      nextTick(() => {
        requestAnimationFrame(() => {
          focusAndSelectInput(input);
          requestAnimationFrame(() => focusAndSelectInput(input));
        });
      });
    };

    const handleKeyDown = (e) => {
      if (!props.visible) return;
      if (e.key === 'Escape') {
        if (showApiKeyModal.value) {
          showApiKeyModal.value = false;
        } else if (isMaximized.value) {
          isMaximized.value = false;
        } else {
          closeModal();
        }
      }
    };

    onMounted(() => {
      window.addEventListener('keydown', handleKeyDown);
    });

    onUnmounted(() => {
      window.removeEventListener('keydown', handleKeyDown);
      if (toastTimeout) clearTimeout(toastTimeout);
      if (livePollInterval) {
        clearInterval(livePollInterval);
        livePollInterval = null;
      }
    });

    return {
      splitCount,
      isMaximized,
      isMinimized,
      activeSlotIndex,
      slots,
      activeSlots,
      activeSlot,
      activeSymbolDisplay,
      modalTitle,
      activeSubtitle,
      setSplitCount,
      toggleMaximize,
      toggleMinimize,
      closeModal,
      handleBackdropClick,
      focusAndSelectInput,
      updateCellSymbol,
      setSlotSymbol,
      setSlotEngine,
      // Auto Live Trade State & Actions
      isRealTradeOpen,
      activeExchange,
      apiKeyConfigured,
      loadingBalance,
      exchangeBalance,
      orderBudget,
      tradeMode,
      customTriggerPrice,
      isPlacingMarketOrder,
      activePositions,
      watchlistItems,
      currentWatchlistItem,
      isSymbolAutoTradeActive,
      showApiKeyModal,
      apiKeyForm,
      isSavingKey,
      isConfiguringAutoTrade,
      isClosingOrder,
      toastMessage,
      toastType,
      currentActiveSymbol,
      currentOpenPosition,
      isTradableOnExchange,
      isBudgetExceeded,
      toggleRealTrade,
      selectExchange,
      setBudgetPct,
      fetchExchangeBalance,
      saveApiKey,
      selectCustomPriceMode,
      placeCustomPriceOrder,
      placeDirectMarketBuy,
      enableAutoTradeForSymbol,
      disableAutoTradeForSymbol,
      closeActivePosition,
      formatNumber
    };
  }
};
</script>

<style scoped>
.multi-chart-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(4, 7, 15, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 999999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  animation: modal-fade-in 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}

.multi-chart-backdrop.is-minimized-backdrop {
  background: transparent !important;
  pointer-events: none;
  backdrop-filter: none;
}

@keyframes modal-fade-in {
  from { opacity: 0; transform: scale(0.98); }
  to { opacity: 1; transform: scale(1); }
}

/* Floating Minimized Pill */
.minimized-pill {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: rgba(13, 20, 36, 0.95);
  border: 1px solid rgba(0, 242, 254, 0.4);
  border-radius: 999px;
  padding: 10px 18px;
  display: flex;
  align-items: center;
  color: #ffffff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6), 0 0 20px rgba(0, 242, 254, 0.25);
  cursor: pointer;
  z-index: 1000000;
  pointer-events: auto;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.minimized-pill:hover {
  transform: translateY(-2px);
  border-color: #00f2fe;
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.7), 0 0 25px rgba(0, 242, 254, 0.4);
}

.pill-btn {
  background: rgba(255, 255, 255, 0.08);
  border: none;
  color: #94a3b8;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.75rem;
}

.pill-btn:hover {
  background: rgba(0, 242, 254, 0.2);
  color: #00f2fe;
}

.pill-btn--close:hover {
  background: rgba(248, 113, 113, 0.25);
  color: #f87171;
}

/* Main Modal Window */
.multi-chart-modal {
  width: 95vw;
  height: 92vh;
  max-width: 1780px;
  max-height: 1080px;
  background: #080c16;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(0, 242, 254, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.multi-chart-modal.is-maximized {
  width: 100vw !important;
  height: 100vh !important;
  max-width: 100vw !important;
  max-height: 100vh !important;
  border-radius: 0 !important;
  border: none !important;
  margin: 0 !important;
}

/* Modal Header Bar */
.modal-header-bar {
  padding: 10px 16px;
  background: rgba(11, 17, 30, 0.96);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
  user-select: none;
  z-index: 100;
}

.chart-header-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00f2fe;
  font-size: 0.95rem;
}

.modal-title {
  font-size: 0.96rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.3px;
  font-family: 'Outfit', sans-serif;
  line-height: 1.2;
}

.modal-subtitle {
  font-size: 0.72rem;
  color: #64748b;
  display: block;
}

/* Auto Live Trade Toggle Button */
.quick-trade-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 700;
  background: rgba(255, 75, 114, 0.12);
  border: 1px solid rgba(255, 75, 114, 0.35);
  color: #ff4b72;
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
}

.quick-trade-toggle-btn:hover {
  background: rgba(255, 75, 114, 0.22);
  color: #ffffff;
  border-color: #ff4b72;
  box-shadow: 0 0 12px rgba(255, 75, 114, 0.3);
}

.quick-trade-toggle-btn.is-active {
  background: linear-gradient(135deg, #ff4b72 0%, #e11d48 100%);
  color: #ffffff;
  border-color: transparent;
  box-shadow: 0 2px 10px rgba(255, 75, 114, 0.4);
}

.quick-trade-toggle-btn.has-open-position {
  background: rgba(0, 245, 160, 0.15);
  border-color: #00f5a0;
  color: #00f5a0;
  box-shadow: 0 0 12px rgba(0, 245, 160, 0.3);
}

.quick-trade-toggle-btn.has-open-position.is-active {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  color: #ffffff;
  border-color: transparent;
}

.quick-trade-toggle-btn.has-auto-trade {
  background: rgba(0, 242, 254, 0.15);
  border-color: #00f2fe;
  color: #00f2fe;
  box-shadow: 0 0 12px rgba(0, 242, 254, 0.3);
}

.quick-trade-toggle-btn.has-auto-trade.is-active {
  background: linear-gradient(135deg, #0284c7 0%, #00f2fe 100%);
  color: #080c16;
  border-color: transparent;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff4b72;
  display: inline-block;
  animation: pulse-red 1.5s infinite;
}

.live-dot--active {
  background: #ffffff;
}

@keyframes pulse-red {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 75, 114, 0.7); }
  70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(255, 75, 114, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 75, 114, 0); }
}

/* REAL-TIME AUTO TRADE ACTION BAR */
.real-trade-bar {
  background: rgba(13, 20, 36, 0.98);
  border-bottom: 1px solid rgba(255, 75, 114, 0.3);
  padding: 8px 16px;
  position: relative;
  z-index: 95;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.trade-symbol-badge {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.82rem;
  color: #ffffff;
}

.exchange-pills {
  display: inline-flex;
  gap: 2px;
  background: rgba(255, 255, 255, 0.04);
  padding: 2px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.exchange-pill {
  padding: 3px 8px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #94a3b8;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.exchange-pill:hover {
  color: #ffffff;
}

.exchange-pill.is-active {
  background: rgba(0, 242, 254, 0.2);
  color: #00f2fe;
  font-weight: 700;
}

.btn-config-key {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  color: #cbd5e1;
  font-size: 0.74rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-config-key:hover {
  background: rgba(0, 242, 254, 0.15);
  color: #00f2fe;
  border-color: rgba(0, 242, 254, 0.4);
}

.trade-position-status {
  background: rgba(0, 245, 160, 0.08);
  border: 1px solid rgba(0, 245, 160, 0.25);
  border-radius: 6px;
  padding: 4px 12px;
  font-size: 0.78rem;
}

.pos-badge-live {
  font-weight: 700;
  color: #00f5a0;
}

.pos-stat {
  color: #e2e8f0;
}

.btn-close-position-instant {
  background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 10px rgba(239, 68, 68, 0.4);
}

.btn-close-position-instant:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.6);
}

.btn-close-position-instant:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.balance-display {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 4px 10px;
  border-radius: 6px;
}

.btn-refresh-balance {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 2px 4px;
  font-size: 0.75rem;
  transition: color 0.2s;
}

.btn-refresh-balance:hover {
  color: #00f2fe;
}

.budget-input-wrap {
  position: relative;
}

.input-with-suffix {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.budget-input {
  width: 130px;
  padding: 5px 44px 5px 10px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  background: rgba(10, 13, 20, 0.9);
  color: #00f2fe;
  font-size: 0.82rem;
  font-weight: 700;
  outline: none;
  transition: all 0.2s;
}

.budget-input:focus {
  border-color: #00f2fe;
  box-shadow: 0 0 0 2px rgba(0, 242, 254, 0.2);
}

.budget-input.is-invalid {
  border-color: #ef4444 !important;
  color: #ef4444 !important;
}

.input-suffix {
  position: absolute;
  right: 8px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #64748b;
  pointer-events: none;
}

.quick-pct-btns {
  display: inline-flex;
  gap: 2px;
}

.quick-pct-btn {
  padding: 3px 6px;
  font-size: 0.68rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s;
}

.quick-pct-btn:hover {
  background: rgba(0, 242, 254, 0.15);
  color: #00f2fe;
}

.trade-mode-pills {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 2px;
  gap: 2px;
}

.mode-pill {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 4px 9px;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.mode-pill:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.06);
}

.mode-pill.is-active {
  background: rgba(0, 242, 254, 0.2);
  color: #00f2fe;
}

.mode-pill--market.is-active {
  background: rgba(16, 185, 129, 0.25);
  color: #10b981;
}

.trigger-price-wrap .trigger-input {
  width: 120px;
  border-color: rgba(0, 242, 254, 0.4);
}

.btn-place-order {
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  color: #080c16;
  border: none;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 0.78rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 10px rgba(0, 242, 254, 0.35);
  white-space: nowrap;
}

.btn-place-order:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(0, 242, 254, 0.55);
}

.btn-trigger-order {
  background: linear-gradient(135deg, #06b6d4 0%, #0284c7 100%);
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(6, 182, 212, 0.35);
}

.btn-trigger-order:hover:not(:disabled) {
  box-shadow: 0 4px 15px rgba(6, 182, 212, 0.6);
}

.btn-market-buy-now {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(16, 185, 129, 0.35);
}

.btn-market-buy-now:hover:not(:disabled) {
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.6);
}

.btn-place-order:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: grayscale(0.6);
}

.btn-cancel-auto-trade {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #94a3b8;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-cancel-auto-trade:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.4);
}

.budget-error-banner {
  margin-top: 6px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.35);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #f87171;
}

.unsupported-symbol-banner {
  margin-top: 6px;
  background: rgba(234, 179, 8, 0.12);
  border: 1px solid rgba(234, 179, 8, 0.35);
  border-radius: 6px;
  padding: 5px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #facc15;
}

.modal-toast {
  position: absolute;
  top: 55px;
  right: 20px;
  z-index: 1000;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.6);
  animation: slideInRight 0.2s ease;
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

.toast-success {
  background: rgba(6, 78, 59, 0.95);
  border: 1px solid #10b981;
  color: #ecfdf5;
}

.toast-danger {
  background: rgba(127, 29, 29, 0.95);
  border: 1px solid #ef4444;
  color: #fef2f2;
}

/* Split Controls Group */
.split-controls-group {
  display: flex;
  align-items: center;
  gap: 3px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 3px 5px;
}

.split-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: #64748b;
  margin-right: 4px;
}

.split-btn {
  background: transparent;
  border: 1px solid transparent;
  border-radius: 5px;
  color: #94a3b8;
  padding: 3px 8px;
  font-size: 0.74rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  line-height: 1;
}

.split-icon {
  font-size: 0.8rem;
  line-height: 1;
}

.split-btn:hover {
  color: #00f2fe;
  background: rgba(0, 242, 254, 0.08);
}

.split-btn.is-active {
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  color: #080c16 !important;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(0, 242, 254, 0.35);
}

/* Window Control Buttons */
.window-ctrl-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.window-ctrl-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.window-ctrl-btn--close:hover {
  background: #ef4444;
  border-color: #ef4444;
  color: #ffffff;
}

/* Modal Charts Grid Wrapper */
.modal-charts-grid-wrapper {
  flex: 1;
  min-height: 0;
  height: 100%;
  padding: 8px;
  overflow: auto;
  background: #060912;
  display: flex;
}

.charts-grid {
  width: 100%;
  height: 100%;
  display: grid;
  gap: 8px;
}

.grid-count-1 {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
}

.grid-count-2 {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: 1fr;
}

.grid-count-4 {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
}

.grid-count-8 {
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(2, 1fr);
}

/* Responsive grid layouts */
@media (max-width: 991px) {
  .grid-count-2 {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(2, 1fr);
  }
  .grid-count-4 {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, 1fr);
  }
  .grid-count-8 {
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(4, 1fr);
  }
}

/* Individual Chart Cell */
.chart-cell {
  background: #0e1526;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.chart-cell.is-active-cell {
  border-color: rgba(0, 242, 254, 0.45);
  box-shadow: 0 0 15px rgba(0, 242, 254, 0.15);
}

.cell-header {
  padding: 6px 10px;
  background: rgba(14, 21, 38, 0.95);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-shrink: 0;
  user-select: none;
}

.cell-num-badge {
  font-size: 0.7rem;
  font-weight: 700;
  color: #00f2fe;
  background: rgba(0, 242, 254, 0.12);
  padding: 2px 6px;
  border-radius: 4px;
}

.cell-engine-toggle {
  display: inline-flex;
  gap: 1px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 5px;
  padding: 1px;
}

.engine-btn {
  padding: 2px 6px;
  font-size: 0.65rem;
  font-weight: 700;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.engine-btn:hover {
  color: #00f2fe;
}

.engine-btn.is-active {
  background: #00f2fe;
  color: #080c16;
}

.cell-symbol-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: #ffffff;
}

.cell-type-badge {
  font-size: 0.62rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  color: #94a3b8;
}

.cell-search-bar {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cell-input-group {
  display: flex;
  align-items: center;
  position: relative;
}

.cell-search-icon {
  position: absolute;
  left: 8px;
  color: #64748b;
  pointer-events: none;
}

.cell-symbol-input {
  width: 120px;
  padding: 3px 22px 3px 26px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  background: rgba(8, 12, 22, 0.8);
  color: #ffffff;
  font-size: 0.75rem;
  font-weight: 600;
  outline: none;
  transition: all 0.2s;
}

.cell-symbol-input:focus {
  border-color: #00f2fe;
  width: 140px;
  box-shadow: 0 0 0 2px rgba(0, 242, 254, 0.2);
}

.cell-input-clear-btn {
  position: absolute;
  right: 6px;
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 0.65rem;
  cursor: pointer;
  padding: 2px;
  border-radius: 3px;
}

.cell-input-clear-btn:hover {
  color: #f87171;
}

.cell-view-btn {
  padding: 4px 10px;
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  border: none;
  border-radius: 6px;
  color: #080c16;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.cell-view-btn:hover {
  opacity: 0.92;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 242, 254, 0.35);
}

.cell-body {
  flex: 1;
  min-height: 0;
  height: 100%;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.vnstock-iframe {
  width: 100%;
  height: 100%;
  flex: 1;
  border: none;
  background: #ffffff;
  border-radius: 0 0 10px 10px;
}

/* API Key Modal */
.modal-backdrop-custom {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  z-index: 1000002;
  display: flex;
  align-items: center;
  justify-content: center;
}

.api-key-modal {
  background: #0f172a;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 14px;
  width: 90%;
  max-width: 480px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7);
  color: #e2e8f0;
}

.btn-modal-close-custom {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 1.1rem;
  cursor: pointer;
}

.btn-modal-close-custom:hover {
  color: #ffffff;
}

.exchange-modal-tabs {
  background: rgba(0, 0, 0, 0.3);
  padding: 4px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.btn-ex-tab {
  flex: 1;
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #94a3b8;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ex-tab:hover {
  color: #ffffff;
}

.btn-ex-tab.active {
  background: rgba(0, 242, 254, 0.15);
  color: #00f2fe;
  font-weight: 700;
  border: 1px solid rgba(0, 242, 254, 0.3);
}

.stk-label {
  display: block;
  font-size: 0.76rem;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 4px;
  text-transform: uppercase;
}

.stk-input {
  width: 100%;
  padding: 8px 12px;
  background: rgba(10, 13, 20, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  color: #ffffff;
  font-size: 0.85rem;
  outline: none;
  transition: all 0.2s;
}

.stk-input:focus {
  border-color: #00f2fe;
  box-shadow: 0 0 0 2px rgba(0, 242, 254, 0.2);
}

.stk-btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.stk-btn--outline {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #94a3b8;
}

.stk-btn--outline:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.stk-btn--primary {
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  color: #080c16;
}

.stk-btn--primary:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(0, 242, 254, 0.4);
}

.stk-btn--primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(10, 13, 20, 0.5);
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 99px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 242, 254, 0.4);
}

.text-cyan {
  color: #00f2fe !important;
}

.text-green {
  color: #00f5a0 !important;
}

.text-red {
  color: #ff4b72 !important;
}

.text-gold {
  color: #f6d365 !important;
}

.text-yellow {
  color: #facc15 !important;
}
</style>
