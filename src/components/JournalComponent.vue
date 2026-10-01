<template>
  <div class="jnl">
    <!-- Header -->
    <div class="jnl-header">
      <div class="jnl-header-left">
        <div class="jnl-total-label">Tổng tài sản ròng (VND)</div>
        <div class="jnl-total-value" :class="{ 'jnl-negative': totalAssetValueVnd < 0 }">
          {{ formatCurrency(totalAssetValueVnd, 'VND') }}
        </div>
        <div class="jnl-meta">
          <span v-if="isRateLoading" class="jnl-meta-item">⏳ Đang tải tỷ giá...</span>
          <span v-else-if="usdToVndRate" class="jnl-meta-item">💱 1 USD = {{ formatNumber(usdToVndRate) }} VND</span>
          <span v-else-if="hasUsdEntries" class="jnl-meta-item jnl-meta-warn">⚠️ Thiếu tỷ giá USD/VND</span>
          <span 
            class="jnl-meta-item jnl-meta-gold-btn"
            @click="openGoldPriceModal"
            title="Nhấn để cập nhật giá vàng theo ý muốn (VN mỗi cửa hàng mỗi khác)"
          >
            <span>🥇 Gold: {{ goldLatestDate || (goldPriceRows.length > 0 ? 'Thị trường' : 'Cập nhật') }}</span>
            <span v-if="customGoldPrice" class="jnl-custom-gold-tag">Tùy chỉnh: {{ formatCurrency(customGoldPrice, 'VND') }}</span>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </span>
        </div>
      </div>
      <div class="jnl-header-actions">
        <button class="jnl-refresh-price-btn" :disabled="isUpdatingPrices || entries.length === 0" @click="updateAllCurrentPrices" title="Tự động tính và cập nhật giá hiện tại của tất cả tài sản">
          <svg v-if="!isUpdatingPrices" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
          </svg>
          <span v-else class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
          <span>{{ isUpdatingPrices ? 'Đang cập nhật giá...' : 'Cập nhật giá' }}</span>
        </button>
        <button class="jnl-chart-btn" @click="openAllocationModal">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 8L8 1a7 7 0 1 1-6.06 3.5L8 8z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><path d="M8 1a7 7 0 0 1 7 7H8V1z" fill="currentColor" opacity="0.35"/></svg>
          Tỷ lệ danh mục
        </button>
        <button class="jnl-add-btn" @click="openModal('add')">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          Thêm mới
        </button>
      </div>
    </div>

    <!-- Filters & Search Bar -->
    <div v-if="entries.length > 0" class="jnl-filter-bar">
      <div class="jnl-filter-pills">
        <button
          v-for="tab in filterTabs"
          :key="tab.key"
          type="button"
          class="jnl-filter-pill"
          :class="{
            'is-active': activeFilter === tab.key,
            'jnl-filter-pill--warning': tab.key === 'HIGH_LOSS'
          }"
          @click="activeFilter = tab.key"
        >
          <span class="jnl-filter-pill-icon">{{ tab.icon }}</span>
          <span class="jnl-filter-pill-label">{{ tab.label }}</span>
          <span class="jnl-filter-pill-count">{{ tab.count }}</span>
        </button>
      </div>

      <div class="jnl-search-wrap">
        <svg class="jnl-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <input
          type="text"
          v-model="searchKeyword"
          class="jnl-search-input"
          placeholder="Tìm mã, tên, ghi chú..."
        />
        <button v-if="searchKeyword" class="jnl-search-clear" @click="searchKeyword = ''" title="Xóa tìm kiếm">✕</button>
      </div>
    </div>

    <!-- Table: Render immediately as soon as entries are present -->
    <div v-if="entries.length > 0" class="jnl-table-wrap">
      <table v-if="sortedEntries.length > 0" class="jnl-table">
        <thead>
          <tr>
            <th>
              <button type="button" class="jnl-sort-btn" @click="toggleSort('entry_date')">
                <span>Ngày</span>
                <span class="jnl-sort-indicator" :class="getSortIndicatorClass('entry_date')">{{ getSortIndicator('entry_date') }}</span>
              </button>
            </th>
            <th>
              <button type="button" class="jnl-sort-btn" @click="toggleSort('asset_type')">
                <span>Loại</span>
                <span class="jnl-sort-indicator" :class="getSortIndicatorClass('asset_type')">{{ getSortIndicator('asset_type') }}</span>
              </button>
            </th>
            <th>
              <button type="button" class="jnl-sort-btn" @click="toggleSort('symbol')">
                <span>Tên / Mã</span>
                <span class="jnl-sort-indicator" :class="getSortIndicatorClass('symbol')">{{ getSortIndicator('symbol') }}</span>
              </button>
            </th>
            <th class="text-end">
              <button type="button" class="jnl-sort-btn jnl-sort-btn--right" @click="toggleSort('quantity')">
                <span>SL</span>
                <span class="jnl-sort-indicator" :class="getSortIndicatorClass('quantity')">{{ getSortIndicator('quantity') }}</span>
              </button>
            </th>
            <th class="text-end">
              <button type="button" class="jnl-sort-btn jnl-sort-btn--right" @click="toggleSort('price')">
                <span>Giá mua</span>
                <span class="jnl-sort-indicator" :class="getSortIndicatorClass('price')">{{ getSortIndicator('price') }}</span>
              </button>
            </th>
            <th class="text-end">
              <button type="button" class="jnl-sort-btn jnl-sort-btn--right" @click="toggleSort('book_value')">
                <span>Giá trị</span>
                <span class="jnl-sort-indicator" :class="getSortIndicatorClass('book_value')">{{ getSortIndicator('book_value') }}</span>
              </button>
            </th>
            <th class="text-end">
              <button type="button" class="jnl-sort-btn jnl-sort-btn--right" @click="toggleSort('current_value')">
                <span>Hiện tại</span>
                <span class="jnl-sort-indicator" :class="getSortIndicatorClass('current_value')">{{ getSortIndicator('current_value') }}</span>
              </button>
            </th>
            <th class="text-end">
              <button type="button" class="jnl-sort-btn jnl-sort-btn--right" @click="toggleSort('price_change')">
                <span>Thay đổi</span>
                <span class="jnl-sort-indicator" :class="getSortIndicatorClass('price_change')">{{ getSortIndicator('price_change') }}</span>
              </button>
            </th>
            <th class="text-end">
              <button type="button" class="jnl-sort-btn jnl-sort-btn--right" @click="toggleSort('change_percent')">
                <span>% Thay đổi</span>
                <span class="jnl-sort-indicator" :class="getSortIndicatorClass('change_percent')">{{ getSortIndicator('change_percent') }}</span>
              </button>
            </th>
            <th class="text-center">Info</th>
            <th class="text-center">Thao tác</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in sortedEntries" :key="entry.id" :class="{ 'jnl-row-debt': entry.asset_type === 'DEBT', 'jnl-row-loss-warning': isHighLoss(entry) }">
            <td class="jnl-cell-date">{{ formatDate(entry.entry_date) }}</td>
            <td>
              <span class="jnl-badge" :class="'jnl-badge--' + (entry.asset_type || 'OTHER').toLowerCase()">
                {{ entry.asset_type }}
              </span>
            </td>
            <td class="jnl-cell-symbol"
                :class="{ 'jnl-cell-symbol--clickable': isChartable(entry) }"
                @click="isChartable(entry) && openChartModal(entry)"
                :title="isChartable(entry) ? 'Nhấn để xem biểu đồ' : ''">
              <div class="jnl-symbol-header-row">
                <span class="jnl-symbol-text">{{ entry.symbol }}</span>
                <span class="jnl-currency-tag" :class="entry.currency === 'USD' ? 'jnl-currency-tag--usd' : ''" :title="entry.currency === 'USD' ? `Tỷ giá hiện tại: 1 USD = ${formatNumber(usdToVndRate || 25450)} VND` : ''">{{ entry.currency || 'VND' }}</span>
                <svg v-if="isChartable(entry)" class="jnl-symbol-chart-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>
                </svg>
              </div>
              <div v-if="isHighLoss(entry)" class="jnl-loss-warning-tag" title="Cần chú ý, thanh lý sớm nếu không muốn lỗ nặng hơn">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <span>Cần chú ý, thanh lý sớm nếu không muốn lỗ nặng hơn</span>
              </div>
            </td>
            <td class="text-end">{{ formatNumber(entry.quantity) }}</td>
            <td class="text-end" :class="{ 'jnl-cell-usd': entry.currency === 'USD' }" :title="getUsdToVndTooltip(entry.price, entry.currency)">{{ formatCurrency(entry.price, entry.currency) }}</td>
            <td class="text-end fw-600" :class="{ 'jnl-cell-usd': entry.currency === 'USD' }" :title="getUsdToVndTooltip(entry.price * entry.quantity, entry.currency)">
              <span :class="entry.asset_type === 'DEBT' ? 'jnl-negative' : ''">
                {{ formatCurrency(entry.asset_type === 'DEBT' ? -(entry.price * entry.quantity) : (entry.price * entry.quantity), entry.currency) }}
              </span>
            </td>
            <td class="text-end fw-600" :class="{ 'jnl-cell-usd': entry.currency === 'USD' }" :title="getUsdToVndTooltip(getCurrentValue(entry), entry.currency)">
              <template v-if="entry.asset_type === 'DEBT'">
                <span class="jnl-negative">{{ formatCurrency(-(entry.price * entry.quantity), entry.currency) }}</span>
              </template>
              <template v-else-if="getCurrentValue(entry) !== null">
                {{ formatCurrency(getCurrentValue(entry), entry.currency) }}
              </template>
              <template v-else>
                <span class="jnl-muted">—</span>
              </template>
            </td>
            <td class="text-end" :class="{ 'jnl-cell-usd': entry.currency === 'USD' }" :title="getPriceChangeTooltip(entry)">
              <template v-if="entry.asset_type === 'DEBT' || entry.asset_type === 'CASH'">
                <span class="jnl-muted">—</span>
              </template>
              <template v-else>
                <span v-if="getPriceChange(entry) !== null"
                  class="jnl-change"
                  :class="{
                    'jnl-change--up': getPriceChange(entry) > 0,
                    'jnl-change--down': getPriceChange(entry) < 0 && !isHighLoss(entry),
                    'jnl-change--high-loss': isHighLoss(entry),
                    'jnl-cell-usd': entry.currency === 'USD'
                  }"
                  :title="getPriceChangeTooltip(entry)"
                >
                  {{ getPriceChange(entry) > 0 ? '+' : '' }}{{ formatCurrency(getPriceChange(entry), entry.currency) }}
                </span>
                <span v-else class="jnl-muted">—</span>
              </template>
            </td>
            <td class="text-end" :class="{ 'jnl-cell-usd': entry.currency === 'USD' }" :title="getChangePercentTooltip(entry)">
              <template v-if="entry.asset_type === 'DEBT' || entry.asset_type === 'CASH'">
                <span class="jnl-muted">—</span>
              </template>
              <template v-else>
                <span v-if="getChangePercent(entry) !== null"
                  class="jnl-change"
                  :class="{
                    'jnl-change--up': getChangePercent(entry) > 0,
                    'jnl-change--down': getChangePercent(entry) < 0 && !isHighLoss(entry),
                    'jnl-change--high-loss': isHighLoss(entry),
                    'jnl-cell-usd': entry.currency === 'USD'
                  }"
                  :title="getChangePercentTooltip(entry)">
                  {{ getChangePercent(entry) > 0 ? '+' : '' }}{{ getChangePercent(entry).toFixed(2) }}%
                </span>
                <span v-else class="jnl-muted">—</span>
              </template>
            </td>
            <td class="text-center">
              <span v-if="entry.notes" class="jnl-note-icon" :title="entry.notes">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.4"/><path d="M8 7v4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><circle cx="8" cy="5" r="0.8" fill="currentColor"/></svg>
                <span class="jnl-note-tooltip">{{ entry.notes }}</span>
              </span>
              <span v-else class="jnl-muted">—</span>
            </td>
            <td class="text-center jnl-cell-actions">
              <button class="jnl-icon-btn jnl-icon-btn--edit" @click="openModal('edit', entry)" title="Sửa">
                <svg width="15" height="15" viewBox="0 0 16 16" fill="none"><path d="M11.5 1.5l3 3L5 14H2v-3L11.5 1.5z" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
              <button class="jnl-icon-btn jnl-icon-btn--del" @click="deleteEntry(entry.id)" title="Xóa">
                <svg width="15" height="15" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M5.333 4V2.667a1.333 1.333 0 011.334-1.334h2.666a1.333 1.333 0 011.334 1.334V4m2 0v9.333a1.333 1.333 0 01-1.334 1.334H4.667a1.333 1.333 0 01-1.334-1.334V4h9.334z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Filter Empty State -->
      <div v-else class="jnl-filter-empty">
        <div class="jnl-filter-empty-icon">🔍</div>
        <h6>Không tìm thấy tài sản nào phù hợp</h6>
        <p>Thử chọn tab phân loại khác hoặc xóa từ khóa tìm kiếm</p>
        <button class="jnl-filter-reset-btn" @click="activeFilter = 'ALL'; searchKeyword = ''">
          Xóa bộ lọc
        </button>
      </div>
    </div>

    <!-- Loading state (only shown if no entries have been loaded yet) -->
    <div v-else-if="isLoading" class="jnl-loading">
      <div class="spinner-border text-primary" role="status"></div>
      <p>Đang tải dữ liệu...</p>
    </div>

    <!-- Empty state -->
    <div v-else class="jnl-empty">
      <div class="jnl-empty-icon">📒</div>
      <h5>Chưa có khoản đầu tư nào</h5>
      <p>Bắt đầu bằng cách thêm tài sản hoặc khoản nợ đầu tiên</p>
      <button class="jnl-add-btn" @click="openModal('add')">+ Thêm mới</button>
    </div>

    <!-- AI Section -->
    <div class="jnl-ai" :class="{ 'jnl-ai--initial': !generatedPrompt }">
      <div class="jnl-ai-header">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="9" stroke="#3b82f6" stroke-width="1.5"/><path d="M7 10l2 2 4-4" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <h4>AI Market Analysis</h4>
      </div>
      <div v-if="!generatedPrompt">
        <button class="jnl-ai-btn" @click="generateAiPrompt">✨ Tạo prompt phân tích</button>
      </div>
      <div v-else>
        <textarea class="jnl-ai-textarea" rows="5" v-model="generatedPrompt"></textarea>
        <div class="jnl-ai-actions">
          <button class="jnl-ai-btn jnl-ai-btn--go" @click="askAI" :disabled="isAnalyzing">
            {{ isAnalyzing ? '⏳ Đang phân tích...' : '🚀 Hỏi AI' }}
          </button>
          <button class="jnl-ai-btn jnl-ai-btn--cancel" @click="generatedPrompt = ''">Hủy</button>
        </div>
        <div v-if="aiResponse" class="jnl-ai-result">
          <strong>📊 Kết quả phân tích:</strong>
          <div class="jnl-ai-content" style="margin-top: 0.5rem;" v-html="parsedAiResponse"></div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="jnl-overlay" @click.self="closeModal">
      <div class="jnl-modal">
        <div class="jnl-modal-header">
          <h3>{{ modalMode === 'add' ? '➕ Thêm khoản mới' : '✏️ Chỉnh sửa' }}</h3>
          <button class="jnl-modal-close" @click="closeModal">✕</button>
        </div>
        <form @submit.prevent="submitForm" class="jnl-form">
          <div class="jnl-form-group">
            <label>Loại tài sản</label>
            <select v-model="formData.asset_type" required>
              <option value="STOCK">📈 Cổ phiếu</option>
              <option value="CRYPTO">₿ Crypto</option>
              <option value="GOLD">🥇 Vàng</option>
              <option value="SILVER">🥈 Bạc</option>
              <option value="CASH">💵 Tiền mặt</option>
              <option value="REAL_ESTATE">🏠 Bất động sản</option>
              <option value="DEBT">🔴 Nợ (Debt)</option>
              <option value="OTHER">📦 Khác</option>
            </select>
          </div>

          <div v-if="isRealEstate" class="jnl-form-group">
            <label>Loại bất động sản</label>
            <select v-model="realEstateCategory">
              <option value="NHA">🏠 Nhà</option>
              <option value="DAT">🧱 Đất</option>
              <option value="CHUNG_CU">🏢 Chung cư</option>
            </select>
          </div>

          <div class="jnl-form-group">
            <label>Tên / Mã</label>
            <input type="text" v-model="formData.symbol" placeholder="VD: SJC, VN30, BTC..." :disabled="isCash || isDebt" :required="!isCash && !isDebt" />
          </div>

          <div class="jnl-form-row">
            <div class="jnl-form-group">
              <label>{{ isDebt ? 'Số tiền nợ' : 'Số lượng' }}</label>
              <input type="text" inputmode="decimal" lang="en-US"
                :value="quantityDisplay"
                @input="onQuantityInput"
                @blur="onQuantityBlur"
                @focus="onQuantityFocus"
                required />
            </div>
            <div class="jnl-form-group">
              <label>Giá mua (mỗi đơn vị)</label>
              <input type="text" inputmode="decimal" lang="en-US"
                :value="priceDisplay"
                @input="onPriceInput"
                @blur="onPriceBlur"
                @focus="onPriceFocus"
                :disabled="isCash || isDebt"
                :required="!isCash && !isDebt" />
            </div>
          </div>

          <div v-if="!isCash && !isDebt" class="jnl-form-group">
            <label>Giá hiện tại (mỗi đơn vị) <small class="text-muted fw-normal">(tùy chọn nhập thủ công)</small></label>
            <input type="text" inputmode="decimal" lang="en-US"
              :value="manualCurrentPriceDisplay"
              @input="onManualCurrentPriceInput"
              @blur="onManualCurrentPriceBlur"
              @focus="onManualCurrentPriceFocus"
              placeholder="VD: 78,500,000 (để trống nếu muốn hệ thống tự cập nhật)" />
          </div>

          <div class="jnl-form-row">
            <div class="jnl-form-group">
              <label>Ngày</label>
              <input type="datetime-local" v-model="formData.entry_date" required />
            </div>
            <div class="jnl-form-group">
              <label>Tiền tệ</label>
              <select v-model="formData.currency" required>
                <option value="VND">VND</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>

          <div class="jnl-form-group">
            <label>Ghi chú</label>
            <textarea v-model="formData.notes" rows="2" placeholder="Lãi suất, mục đích, ghi nhớ..."></textarea>
          </div>

          <button type="submit" class="jnl-submit-btn">
            {{ modalMode === 'add' ? '💾 Lưu' : '✅ Cập nhật' }}
          </button>
        </form>
      </div>
    </div>

    <div v-if="showAllocationModal" class="jnl-overlay" @click.self="closeAllocationModal">
      <div class="jnl-modal jnl-modal--allocation">
        <div class="jnl-modal-header">
          <h3>🥧 Tỷ lệ danh mục tài sản</h3>
          <button class="jnl-modal-close" @click="closeAllocationModal">✕</button>
        </div>
        <div class="jnl-allocation-body">
          <div v-if="allocationSegments.length === 0" class="jnl-allocation-empty">
            Chưa có dữ liệu tài sản để hiển thị biểu đồ.
          </div>
          <template v-else>
            <div class="jnl-pie-wrap">
              <div class="jnl-pie-chart" :style="pieChartConicStyle">
                <div class="jnl-pie-center">
                  <strong>100%</strong>
                  <span>Danh mục</span>
                </div>
              </div>
            </div>
            <!-- Summary KPI Bar -->
            <div class="jnl-allocation-summary-card">
              <div class="summary-col">
                <span class="summary-label">Tài sản ròng (NAV)</span>
                <span class="summary-val summary-val--cyan">{{ formatCurrency(totalAllocationValue, 'VND') }}</span>
              </div>
              <div class="summary-divider" v-if="totalAllocationCost > 0"></div>
              <div class="summary-col" v-if="totalAllocationCost > 0">
                <span class="summary-label">Tổng vốn gốc</span>
                <span class="summary-val">{{ formatCurrency(totalAllocationCost, 'VND') }}</span>
              </div>
              <div class="summary-divider" v-if="totalAllocationGrowth !== null"></div>
              <div class="summary-col" v-if="totalAllocationGrowth !== null">
                <span class="summary-label">Tăng trưởng</span>
                <span class="summary-val" :class="totalAllocationGrowth >= 0 ? 'text-change--up' : 'text-change--down'">
                  {{ totalAllocationGrowth >= 0 ? '▲ +' : '▼ ' }}{{ totalAllocationGrowth.toFixed(1) }}%
                </span>
              </div>
            </div>

            <!-- Breakdown List with Growth % -->
            <div class="jnl-allocation-list">
              <div v-for="segment in allocationSegments" :key="segment.key" class="jnl-allocation-item">
                <div class="jnl-allocation-main">
                  <div class="jnl-allocation-label">
                    <span class="jnl-allocation-dot" :style="{ backgroundColor: segment.color }"></span>
                    <span class="jnl-allocation-icon">{{ segment.icon }}</span>
                    <span class="jnl-allocation-name">{{ segment.label }}</span>
                  </div>
                  <div class="jnl-allocation-sub">
                    <span class="jnl-allocation-pct">{{ segment.percent.toFixed(1) }}% danh mục</span>
                    <template v-if="segment.cost > 0 && segment.key !== 'DEBT' && segment.key !== 'CASH'">
                      <span class="jnl-allocation-sep">•</span>
                      <span class="jnl-allocation-cost">Vốn: {{ formatCurrency(segment.cost, 'VND') }}</span>
                    </template>
                  </div>
                </div>

                <div class="jnl-allocation-metrics">
                  <div class="jnl-allocation-cur-val">
                    {{ formatCurrency(segment.value, 'VND') }}
                  </div>
                  <div 
                    v-if="segment.growth !== null" 
                    class="jnl-growth-pill" 
                    :class="segment.growth > 0 ? 'growth-pill--up' : (segment.growth < 0 ? 'growth-pill--down' : 'growth-pill--zero')"
                    :title="`Giá gốc: ${formatCurrency(segment.cost, 'VND')} ➔ Hiện tại: ${formatCurrency(segment.value, 'VND')} (Chênh lệch: ${segment.pnl >= 0 ? '+' : ''}${formatCurrency(segment.pnl, 'VND')})`"
                  >
                    <span class="growth-arrow">{{ segment.growth > 0 ? '▲ +' : (segment.growth < 0 ? '▼ ' : '') }}</span>
                    <span>{{ segment.growth.toFixed(1) }}%</span>
                  </div>
                  <div v-else class="jnl-growth-pill growth-pill--neutral" title="Không áp dụng tính tăng trưởng">
                    <span>--</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- MODAL: CẬP NHẬT GIÁ VÀNG TÙY CHỌN -->
    <div v-if="showGoldPriceModal" class="jnl-overlay" @click.self="closeGoldPriceModal">
      <div class="jnl-modal jnl-modal--gold">
        <div class="jnl-modal-header">
          <div class="d-flex align-items-center gap-2">
            <span style="font-size: 1.3rem;">🥇</span>
            <div>
              <h3 style="margin: 0; font-size: 1.1rem;">Tùy chỉnh giá vàng</h3>
              <div style="font-size: 0.75rem; color: #94a3b8;">Cập nhật theo giá cửa hàng mua bán thực tế</div>
            </div>
          </div>
          <button class="jnl-modal-close" @click="closeGoldPriceModal">✕</button>
        </div>

        <div class="jnl-modal-body" style="padding: 1.25rem 1.5rem;">
          <!-- Reference Market Rates from API -->
          <div class="jnl-gold-market-box">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <span class="jnl-gold-market-title">🌐 Giá thị trường tham khảo (API):</span>
              <span class="jnl-gold-market-time" v-if="goldLatestDate">🕒 {{ goldLatestDate }}</span>
            </div>
            <div class="jnl-gold-market-grid" v-if="marketGoldOptions.length > 0">
              <button 
                v-for="opt in marketGoldOptions" 
                :key="opt.name" 
                type="button"
                class="jnl-gold-market-chip" 
                @click="applyMarketPriceToInput(opt.price)"
                :title="`Bấm để chọn giá ${opt.name}: ${formatCurrency(opt.price, 'VND')}`"
              >
                <span class="chip-name">{{ opt.name }}:</span>
                <span class="chip-price">{{ formatNumber(opt.price) }}đ</span>
              </button>
            </div>
            <div v-else class="text-muted" style="font-size: 0.8rem;">
              Giá SJC chuẩn: <b>{{ formatCurrency(baseMarketGoldPrice, 'VND') }}</b>
            </div>
          </div>

          <!-- Price Input Field -->
          <div class="jnl-form-group mt-3">
            <label style="font-weight: 600; color: #f1f5f9; display: flex; justify-content: space-between;">
              <span>Giá vàng mong muốn (VND / lượng):</span>
              <span v-if="customGoldPriceInput > 0" style="color: #fbbf24; font-size: 0.82rem;">
                ~ {{ formatCurrency(Math.round(customGoldPriceInput / 10), 'VND') }} / chỉ
              </span>
            </label>
            <div class="jnl-gold-input-wrap">
              <input
                type="text"
                inputmode="decimal"
                lang="en-US"
                :value="customGoldPriceDisplay"
                @input="onCustomGoldPriceInput"
                @blur="onCustomGoldPriceBlur"
                @focus="onCustomGoldPriceFocus"
                placeholder="VD: 85,000,000"
                class="jnl-gold-input"
                required
              />
              <span class="jnl-gold-currency">VND</span>
            </div>
            <div class="d-flex justify-content-between align-items-center mt-1">
              <div style="font-size: 0.78rem; color: #94a3b8;">
                Bằng chữ: <b style="color: #38bdf8;">{{ formatCurrency(customGoldPriceInput || 0, 'VND') }}</b>
              </div>
            </div>
          </div>

          <!-- Quick Increment / Decrement Buttons -->
          <div class="d-flex gap-2 mt-2 mb-3">
            <button type="button" class="jnl-quick-step-btn" @click="adjustGoldPriceInput(-500000)">-500K</button>
            <button type="button" class="jnl-quick-step-btn" @click="adjustGoldPriceInput(-100000)">-100K</button>
            <button type="button" class="jnl-quick-step-btn" @click="adjustGoldPriceInput(100000)">+100K</button>
            <button type="button" class="jnl-quick-step-btn" @click="adjustGoldPriceInput(500000)">+500K</button>
            <button type="button" class="jnl-quick-step-btn" @click="adjustGoldPriceInput(1000000)">+1 Triệu</button>
          </div>

          <!-- Notice & Affected items -->
          <div class="jnl-gold-notice">
            <div class="d-flex align-items-center gap-1 mb-1">
              <span>💡</span>
              <span style="font-weight: 600;">Tự động cập nhật:</span>
            </div>
            <p style="margin: 0; font-size: 0.76rem; color: #94a3b8; line-height: 1.4;">
              Khi bấm lưu, tất cả <b>{{ goldEntriesCount }} tài sản Vàng</b> trong danh mục sẽ lập tức được cập nhật theo mức giá này. 
              <br/>
              Nếu sau này bạn bấm nút <b>"Cập nhật giá"</b> ở thanh công cụ chính, giá vàng sẽ tự động được đồng bộ lại theo giá thị trường API.
            </p>
          </div>
        </div>

        <div class="jnl-modal-footer" style="padding: 1rem 1.5rem; display: flex; justify-content: space-between; gap: 0.75rem; border-top: 1px solid rgba(255,255,255,0.08); background: rgba(15, 23, 42, 0.4);">
          <button 
            v-if="customGoldPrice" 
            type="button" 
            class="jnl-btn-secondary" 
            @click="resetGoldPriceToMarket"
            title="Xóa giá tùy chỉnh và dùng lại giá thị trường từ API"
          >
            🔄 Dùng giá thị trường
          </button>
          <div v-else></div>

          <div class="d-flex gap-2">
            <button type="button" class="jnl-btn-secondary" @click="closeGoldPriceModal">Hủy</button>
            <button type="button" class="jnl-btn-primary" :disabled="isSavingGoldPrice || !customGoldPriceInput || customGoldPriceInput <= 0" @click="saveCustomGoldPrice">
              <span v-if="isSavingGoldPrice" class="spinner-border spinner-border-sm me-1"></span>
              {{ isSavingGoldPrice ? 'Đang lưu...' : '💾 Lưu & Cập nhật' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL: CHART POPUP (TRADINGVIEW & VNSTOCK) -->
    <div v-if="showChartModal" class="modal-backdrop-chart" @click.self="closeChartModal">
      <div class="jnl-modal-chart">
        <div class="chart-modal-head">
          <div class="chart-modal-title-wrap">
            <span class="jnl-badge" :class="'jnl-badge--' + (selectedChartAsset.asset_type || 'OTHER').toLowerCase()">
              {{ selectedChartAsset.asset_type }}
            </span>
            <div class="chart-title-text">
              <h3>{{ selectedChartAsset.symbol }}</h3>
              <span class="chart-sub" v-if="selectedChartAsset.asset_type === 'GOLD'">({{ selectedChartAsset.name && selectedChartAsset.name.toUpperCase() !== selectedChartAsset.symbol.toUpperCase() ? selectedChartAsset.name + ' • ' : '' }}XAU/USD - Vàng Thế Giới)</span>
              <span class="chart-sub" v-else-if="selectedChartAsset.asset_type === 'SILVER'">({{ selectedChartAsset.name && selectedChartAsset.name.toUpperCase() !== selectedChartAsset.symbol.toUpperCase() ? selectedChartAsset.name + ' • ' : '' }}XAG/USD - Bạc)</span>
              <span class="chart-sub" v-else-if="selectedChartAsset.asset_type === 'CRYPTO'">(Crypto / USD)</span>
              <span class="chart-sub" v-else-if="selectedChartAsset.currency === 'USD'">(Stock US / USD)</span>
              <span class="chart-sub" v-else-if="selectedChartAsset.currency === 'VND'">(VN Stock / VND)</span>
            </div>
          </div>

          <div class="chart-modal-header-actions">
            <!-- Chart Mode Switcher: Vietstock vs TradingView for VN Stock -->
            <div class="chart-tab-switcher" v-if="isVnStockSelected">
              <button 
                type="button"
                class="chart-switch-btn" 
                :class="{ active: chartTab === 'tradingview' }"
                @click="chartTab = 'tradingview'"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>
                </svg>
                HaoNguyen V14.4
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
            
            <button @click="closeChartModal" class="jnl-modal-close" aria-label="Đóng">✕</button>
          </div>
        </div>

        <!-- Symbol Quick Switcher Bar -->
        <div class="chart-modal-search-bar">
          <div class="chart-search-box position-relative">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input 
              ref="jnlChartSearchRef"
              v-model="chartSearchInput" 
              @focus="$event.target.select()"
              @click="$event.target.select()"
              @keydown.enter.prevent="applyChartSearch($event)" 
              @input="chartSearchInput = $event.target.value.toUpperCase()"
              placeholder="Nhập mã khác (VD: TCB, BTC, AAPL, GOLD, XAUUSD...)"
              class="chart-search-input" 
              style="text-transform: uppercase;"
            />
            <button 
              v-if="chartSearchInput" 
              type="button" 
              class="chart-search-clear-btn" 
              @click.stop="chartSearchInput = ''; $refs.jnlChartSearchRef?.focus()" 
              title="Xóa nhanh"
            >
              ✕
            </button>
            <button class="btn-search-apply" @click="applyChartSearch">Xem</button>
          </div>
          <div class="chart-quick-chips" v-if="quickChartChips.length > 0">
            <span class="quick-chips-lbl">Danh mục:</span>
            <button 
              v-for="chip in quickChartChips" 
              :key="chip.symbol + chip.asset_type" 
              class="quick-chip"
              :class="{ 'quick-chip-active': selectedChartAsset.symbol.toUpperCase() === chip.symbol.toUpperCase() }"
              @click="openChartModal(chip)"
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
              :key="resolvedTvSymbol + '_' + (selectedChartAsset.asset_type || '')" 
              :coin="resolvedTvSymbol" 
              :height="520" 
              default-engine="haonguyen"
              :entry-price="selectedChartAsset.price"
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
import { ref, onMounted, reactive, computed, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useUser } from '@clerk/vue';
import { useNotification } from '@kyvg/vue3-notification';
import { parseMarkdown } from '@/utils/markdown';
import TradingViewChart from './TradingViewChart.vue';

export default {
  name: 'JournalComponent',
  components: {
    TradingViewChart
  },
  props: {
    accountNumber: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const { user: clerkUser, isLoaded, isSignedIn: isClerkSignedIn } = useUser();
    const { notify } = useNotification();
    const router = useRouter();
    const entries = ref([]);
    const isLoading = ref(true);
    const showModal = ref(false);
    const showAllocationModal = ref(false);
    const modalMode = ref('add');
    const realEstateCategory = ref('NHA');
    const formData = reactive({
      id: null,
      asset_type: 'STOCK',
      symbol: '',
      quantity: 1,
      price: 0,
      currency: 'VND',
      entry_date: new Date().toISOString().slice(0, 16),
      notes: '',
      current_price: null
    });

    const quantityDisplay = ref('1');
    const priceDisplay = ref('0');
    const manualCurrentPriceDisplay = ref('');
    
    const isCash = computed(() => formData.asset_type === 'CASH');
    const isDebt = computed(() => formData.asset_type === 'DEBT');
    const isRealEstate = computed(() => formData.asset_type === 'REAL_ESTATE');

    const realEstateSymbolMap = {
      NHA: 'NHA',
      DAT: 'DAT',
      CHUNG_CU: 'CHUNG_CU'
    };

    const assetTypeLabels = {
      STOCK: 'Cổ phiếu',
      CRYPTO: 'Crypto',
      GOLD: 'Vàng',
      SILVER: 'Bạc',
      CASH: 'Tiền mặt',
      REAL_ESTATE: 'Bất động sản',
      DEBT: 'Nợ',
      OTHER: 'Khác'
    };
    const sortState = ref({
      field: 'entry_date',
      direction: 'desc'
    });

    const setRealEstateSymbolFromCategory = () => {
      if (!isRealEstate.value) return;
      formData.symbol = realEstateSymbolMap[realEstateCategory.value] || 'NHA';
    };

    watch(() => formData.asset_type, (newType) => {
      if (newType === 'CRYPTO') {
        formData.currency = 'USD';
      } else if (newType === 'CASH') {
        formData.symbol = 'CASH';
        formData.price = 1;
        priceDisplay.value = '1';
      } else if (newType === 'DEBT') {
        formData.symbol = 'DEBT';
        formData.price = 1;
        priceDisplay.value = '1';
      } else if (newType === 'REAL_ESTATE') {
        setRealEstateSymbolFromCategory();
      }
    });

    watch(realEstateCategory, () => {
      setRealEstateSymbolFromCategory();
    });

    // AI Feature State
    const generatedPrompt = ref('');
    const aiResponse = ref('');
    const parsedAiResponse = computed(() => parseMarkdown(aiResponse.value));
    const isAnalyzing = ref(false);
    const usdToVndRate = ref(25450);
    const isRateLoading = ref(false);
    const marketRates = ref([]);
    const dealProfitBySymbol = ref({});
    const FX_RATE_CACHE_KEY = 'journal_usd_vnd_rate_cache';
    const FX_RATE_CACHE_TTL_MS = 24 * 60 * 60 * 1000;
    const MARKET_RATES_CACHE_KEY = 'journal_market_rates_cache';
    const MARKET_RATES_CACHE_TTL_MS = 30 * 60 * 1000;
    const FX_RATE_ERROR_COOLDOWN_KEY = 'journal_usd_vnd_rate_error_cooldown_until';
    const FX_RATE_ERROR_COOLDOWN_MS = 60 * 60 * 1000;
    const GOLD_PRICE_CACHE_KEY = 'journal_gold_prices_cache';
    const GOLD_PRICE_CACHE_TTL_MS = 30 * 60 * 1000;
    const CUSTOM_GOLD_PRICE_KEY = 'journal_custom_gold_price_vnd';
    const goldPriceRows = ref([]);
    const goldLatestDate = ref('');
    const customGoldPrice = ref(null);
    const showGoldPriceModal = ref(false);
    const customGoldPriceInput = ref(0);
    const customGoldPriceDisplay = ref('');
    const isSavingGoldPrice = ref(false);

    try {
      const savedCustom = localStorage.getItem(CUSTOM_GOLD_PRICE_KEY);
      if (savedCustom && !isNaN(Number(savedCustom)) && Number(savedCustom) > 0) {
        customGoldPrice.value = Number(savedCustom);
      }
    } catch (e) {
      console.warn('Error reading custom gold price from localStorage:', e);
    }

    const hasUsdEntries = computed(() => {
      return entries.value.some(entry => (entry.currency || 'VND') === 'USD');
    });

    const toNumber = (value) => {
      const num = typeof value === 'string'
        ? parseFloat(value.replace(/,/g, ''))
        : Number(value);
      return Number.isFinite(num) ? num : null;
    };

    const extractUsdVndRate = (rates) => {
      if (!Array.isArray(rates)) return null;

      const findByCode = (codes) => rates.find(item => {
        const code = String(item?.currency || item?.symbol || item?.pair || '')
          .toUpperCase()
          .replace(/[^A-Z]/g, '');
        return codes.includes(code);
      });

      const direct = findByCode(['USDVND']);
      if (direct) {
        return toNumber(direct.rate) ?? toNumber(direct.close) ?? toNumber(direct.bid) ?? toNumber(direct.ask);
      }

      const inverse = findByCode(['VNDUSD']);
      if (inverse) {
        const inverseRate = toNumber(inverse.rate) ?? toNumber(inverse.close) ?? toNumber(inverse.bid) ?? toNumber(inverse.ask);
        return inverseRate ? 1 / inverseRate : null;
      }

      return null;
    };

    const fetchUsdVndRate = async () => {
      isRateLoading.value = true;
      try {
        const response = await fetch('/api/rates', { signal: AbortSignal.timeout(6000) });
        if (!response.ok) {
          localStorage.setItem(FX_RATE_ERROR_COOLDOWN_KEY, String(Date.now() + FX_RATE_ERROR_COOLDOWN_MS));
          return;
        }

        const data = await response.json();
        marketRates.value = Array.isArray(data) ? data : [];
        localStorage.setItem(MARKET_RATES_CACHE_KEY, JSON.stringify({
          data: marketRates.value,
          cachedAt: Date.now()
        }));
        const parsedRate = extractUsdVndRate(data);
        if (parsedRate) {
          usdToVndRate.value = parsedRate;
          localStorage.setItem(FX_RATE_CACHE_KEY, JSON.stringify({
            rate: parsedRate,
            cachedAt: Date.now()
          }));
          localStorage.removeItem(FX_RATE_ERROR_COOLDOWN_KEY);
          return;
        }

        localStorage.setItem(FX_RATE_ERROR_COOLDOWN_KEY, String(Date.now() + FX_RATE_ERROR_COOLDOWN_MS));
      } catch (error) {
        console.error('Error fetching USD/VND rate:', error);
        localStorage.setItem(FX_RATE_ERROR_COOLDOWN_KEY, String(Date.now() + FX_RATE_ERROR_COOLDOWN_MS));
      } finally {
        isRateLoading.value = false;
      }
    };

    const loadUsdVndRate = async () => {
      let hasFreshCache = false;
      let hasFreshMarketRates = false;

      try {
        const marketRatesCacheRaw = localStorage.getItem(MARKET_RATES_CACHE_KEY);
        if (marketRatesCacheRaw) {
          const cache = JSON.parse(marketRatesCacheRaw);
          const cachedAt = Number(cache?.cachedAt);
          const cachedData = Array.isArray(cache?.data) ? cache.data : [];
          const isFresh = Number.isFinite(cachedAt) && (Date.now() - cachedAt) < MARKET_RATES_CACHE_TTL_MS;

          if (cachedData.length > 0) {
            marketRates.value = cachedData;
            hasFreshMarketRates = isFresh;
          }
        }
      } catch (error) {
        console.error('Error reading market rates cache:', error);
      }

      try {
        const cacheRaw = localStorage.getItem(FX_RATE_CACHE_KEY);
        if (cacheRaw) {
          const cache = JSON.parse(cacheRaw);
          const cachedRate = toNumber(cache?.rate);
          const cachedAt = Number(cache?.cachedAt);
          const isFresh = Number.isFinite(cachedAt) && (Date.now() - cachedAt) < FX_RATE_CACHE_TTL_MS;

          if (cachedRate) {
            usdToVndRate.value = cachedRate;
            hasFreshCache = isFresh;
          }
        }
      } catch (error) {
        console.error('Error reading USD/VND rate cache:', error);
      }

      if (hasFreshCache && hasFreshMarketRates) return;

      const cooldownUntil = Number(localStorage.getItem(FX_RATE_ERROR_COOLDOWN_KEY) || 0);
      if (Number.isFinite(cooldownUntil) && cooldownUntil > Date.now()) {
        return;
      }

      await fetchUsdVndRate();
    };

    const normalizeCode = (value) => {
      return String(value || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    };

    const normalizeText = (value) => {
      return String(value || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/đ/g, 'd')
        .replace(/Đ/g, 'D')
        .toUpperCase()
        .replace(/[^A-Z0-9 ]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    };

    const getRateNumber = (rateItem) => {
      return toNumber(rateItem?.rate) ?? toNumber(rateItem?.close) ?? toNumber(rateItem?.bid) ?? toNumber(rateItem?.ask);
    };

    const findMarketRateExact = (candidates) => {
      if (!Array.isArray(marketRates.value) || marketRates.value.length === 0) return null;

      const exactCandidates = candidates
        .map(item => String(item || '').toUpperCase().trim())
        .filter(Boolean);
      if (exactCandidates.length === 0) return null;

      for (const candidate of exactCandidates) {
        const matched = marketRates.value.find(item => String(item?.currency || item?.symbol || item?.pair || '').toUpperCase().trim() === candidate);
        if (!matched) continue;

        const value = getRateNumber(matched);
        if (value !== null) return value;
      }

      return null;
    };

    const findMarketRate = (candidates) => {
      if (!Array.isArray(marketRates.value) || marketRates.value.length === 0) return null;

      const normalizedCandidates = candidates.map(normalizeCode).filter(Boolean);
      if (normalizedCandidates.length === 0) return null;

      for (const item of marketRates.value) {
        const itemCode = normalizeCode(item?.currency || item?.symbol || item?.pair);
        if (!itemCode || !normalizedCandidates.includes(itemCode)) continue;

        const value = getRateNumber(item);
        if (value !== null) return value;
      }

      return null;
    };

    const toBuyValueVnd = (item) => {
      let value = null;
      const buyValue = toNumber(item?.BuyValue);

      if (buyValue !== null) {
        value = buyValue;
      } else {
        const buyText = String(item?.Buy || '').replace(/,/g, '');
        value = toNumber(buyText);
      }

      if (value === null) return null;

      // Gold prices in Vietnam are usually quoted per tael (lượng) and are currently around 70M - 90M VND.
      // We normalize the value to raw VND based on its scale:
      // - Values under 1000 (e.g. 81.3) represent million VND
      // - Values under 1000000 (e.g. 81300) represent thousand VND
      // - Values 1000000 and above (e.g. 81300000) are already in VND
      if (value < 1000) {
        return value * 1000000;
      } else if (value < 1000000) {
        return value * 1000;
      } else {
        return value;
      }
    };

    const loadGoldPrices = async () => {
      try {
        const cacheRaw = localStorage.getItem(GOLD_PRICE_CACHE_KEY);
        if (cacheRaw) {
          const cache = JSON.parse(cacheRaw);
          const cachedAt = Number(cache?.cachedAt);
          const isFresh = Number.isFinite(cachedAt) && (Date.now() - cachedAt) < GOLD_PRICE_CACHE_TTL_MS;
          const cachedData = Array.isArray(cache?.data) ? cache.data : [];
          const cachedLatestDate = String(cache?.latestDate || '');

          if (cachedData.length > 0) {
            goldPriceRows.value = cachedData;
            goldLatestDate.value = cachedLatestDate;
            if (isFresh) return;
          }
        }
      } catch (error) {
        console.error('Error reading gold price cache:', error);
      }

      let success = false;
      let rows = [];
      let latestDate = '';

      // 1. Try giavang.now public API (Fast, CORS-friendly, avoids SJC 403 block)
      try {
        const response = await fetch('https://giavang.now/api/prices', { signal: AbortSignal.timeout(6000) });
        if (response.ok) {
          const data = await response.json();
          if (data && data.success && data.prices) {
            rows = [];
            for (const [key, item] of Object.entries(data.prices)) {
              if (key === 'XAUUSD') continue; // Skip world gold
              rows.push({
                Id: key,
                TypeName: item.name || key,
                BranchName: item.name?.toLowerCase().includes('hanoi') || item.name?.toLowerCase().includes('hà nội') ? 'Hà Nội' : 'TP.HCM',
                Buy: String(item.buy),
                Sell: String(item.sell),
                BuyValue: item.buy,
                SellValue: item.sell
              });
            }
            if (rows.length > 0) {
              latestDate = `${data.date || ''} ${data.time || ''}`.trim();
              success = true;
            }
          }
        }
      } catch (error) {
        console.warn('giavang.now fetch failed, trying fallback...', error);
      }

      // 2. Fallback: Try local/proxy SJC endpoint
      if (!success) {
        try {
          const response = await fetch('/goldprice/services/priceservice.ashx', { signal: AbortSignal.timeout(6000) });
          if (response.ok && response.headers.get('content-type')?.includes('json')) {
            const data = await response.json();
            if (data && Array.isArray(data.data) && data.data.length > 0) {
              rows = data.data;
              latestDate = String(data.latestDate || '');
              success = true;
            }
          }
        } catch (error) {
          console.warn('SJC relative fetch failed...', error);
        }
      }

      if (success && rows.length > 0) {
        goldPriceRows.value = rows;
        goldLatestDate.value = latestDate;
        try {
          localStorage.setItem(GOLD_PRICE_CACHE_KEY, JSON.stringify({
            data: rows,
            latestDate,
            cachedAt: Date.now()
          }));
        } catch (error) {
          console.error('Error writing gold price cache:', error);
        }
      }
    };

    const getRawMarketGoldPrice = () => {
      if (!Array.isArray(goldPriceRows.value) || goldPriceRows.value.length === 0) return 85000000;
      const sjcRow = goldPriceRows.value.find(item => {
        const typeName = normalizeText(item?.TypeName);
        return typeName.includes('SJC');
      });
      if (sjcRow) {
        const val = toBuyValueVnd(sjcRow);
        if (val) return val;
      }
      return toBuyValueVnd(goldPriceRows.value[0]) || 85000000;
    };

    const baseMarketGoldPrice = computed(() => {
      return getRawMarketGoldPrice();
    });

    const marketGoldOptions = computed(() => {
      if (!Array.isArray(goldPriceRows.value) || goldPriceRows.value.length === 0) return [];
      const list = [];
      for (const row of goldPriceRows.value) {
        const buyVal = toBuyValueVnd(row);
        if (buyVal && buyVal > 0) {
          const rawName = row.TypeName || row.name || row.Id || 'Vàng';
          let shortName = rawName.replace(/Vàng nhẫn/i, 'Nhẫn').replace(/Vàng/i, '').trim();
          if (!shortName) shortName = rawName;
          if (list.length < 6 && !list.some(x => x.name === shortName)) {
            list.push({
              name: shortName,
              price: buyVal
            });
          }
        }
      }
      return list;
    });

    const goldEntriesCount = computed(() => {
      return entries.value.filter(e => (e.asset_type || '').toUpperCase() === 'GOLD').length;
    });

    const findGoldBuyValueBySymbol = (symbol) => {
      if (customGoldPrice.value && customGoldPrice.value > 0) {
        return customGoldPrice.value;
      }
      const normalizedSymbol = normalizeText(symbol);
      if (!normalizedSymbol || !Array.isArray(goldPriceRows.value) || goldPriceRows.value.length === 0) return null;

      const rowsWithBranch = goldPriceRows.value
        .filter(item => {
          const typeName = normalizeText(item?.TypeName);
          return typeName.includes(normalizedSymbol);
        })
        .sort((a, b) => {
          const aHcm = normalizeText(a?.BranchName).includes('HO CHI MINH') ? 1 : 0;
          const bHcm = normalizeText(b?.BranchName).includes('HO CHI MINH') ? 1 : 0;
          return bHcm - aHcm;
        });

      if (rowsWithBranch.length === 0) return null;

      return toBuyValueVnd(rowsWithBranch[0]);
    };

    const getBaseSjcGoldPrice = () => {
      if (customGoldPrice.value && customGoldPrice.value > 0) {
        return customGoldPrice.value;
      }
      if (!Array.isArray(goldPriceRows.value) || goldPriceRows.value.length === 0) return null;
      const sjcVal = findGoldBuyValueBySymbol('SJC');
      if (sjcVal !== null) return sjcVal;
      return toBuyValueVnd(goldPriceRows.value[0]);
    };

    const getNormalizedSymbol = (entry) => String(entry?.symbol || '').toUpperCase().trim();

    const getUnrealizedProfit = (entry) => {
      const normalizedSymbol = getNormalizedSymbol(entry);
      return toNumber(dealProfitBySymbol.value[normalizedSymbol]) ?? 0;
    };

    const hasDealBySymbol = (entry) => {
      const normalizedSymbol = getNormalizedSymbol(entry);
      return Object.prototype.hasOwnProperty.call(dealProfitBySymbol.value, normalizedSymbol);
    };

    const getCurrentPrice = (entry) => {
      if (entry && entry.current_price !== undefined && entry.current_price !== null && entry.current_price !== 0) {
        return toNumber(entry.current_price);
      }

      const assetType = String(entry?.asset_type || '').toUpperCase();
      const quantity = toNumber(entry?.quantity) ?? 0;
      const entryPrice = toNumber(entry?.price);

      // unrealizedProfit is for the whole position, so convert to per-unit only for display.
      if ((assetType === 'STOCK' || assetType === 'STOCK_VN') && hasDealBySymbol(entry) && entryPrice !== null && quantity > 0) {
        return entryPrice + (getUnrealizedProfit(entry) / quantity);
      }

      if (assetType !== 'CRYPTO' && assetType !== 'GOLD') {
        return entryPrice;
      }

      if (assetType === 'GOLD') {
        const goldBuyValueVnd = findGoldBuyValueBySymbol(entry?.symbol) || getBaseSjcGoldPrice();
        if (goldBuyValueVnd === null) return null;

        const currency = entry?.currency || 'VND';

        if (currency === 'VND') {
          return goldBuyValueVnd;
        }

        if (!usdToVndRate.value) return null;
        return goldBuyValueVnd / usdToVndRate.value;
      }

      const symbol = String(entry?.symbol || '').toUpperCase().trim();
      if (!symbol) return null;

      const symbolNoSlash = symbol.replace('/', '');
      let base = symbolNoSlash;
      if (symbolNoSlash.endsWith('USDT')) {
        base = symbolNoSlash.slice(0, -4);
      } else if (symbolNoSlash.endsWith('USD')) {
        base = symbolNoSlash.slice(0, -3);
      }

      // CRYPTO pricing should prioritize exact BASE/USD first, then BASEUSD, then BASE itself.
      const pairSlash = `${base}/USD`;
      const pairCompact = `${base}USD`;
      const rateInUsd = findMarketRateExact([pairSlash, pairCompact]) ?? 
                        findMarketRate([pairSlash, pairCompact]) ?? 
                        findMarketRateExact([base]) ?? 
                        findMarketRate([base]);
      if (rateInUsd === null) return null;

      const currency = entry?.currency || 'VND';
      if (currency === 'VND') {
        const marketPrice = usdToVndRate.value ? rateInUsd * usdToVndRate.value : null;
        return marketPrice;
      }
      return rateInUsd;
    };

    const getCurrentValue = (entry) => {
      const assetType = String(entry?.asset_type || '').toUpperCase();
      const quantity = toNumber(entry?.quantity) ?? 0;
      const entryPrice = toNumber(entry?.price) ?? 0;

      // 1. If entry has explicit current_price (manual or synced), always compute from it!
      if (entry && entry.current_price !== undefined && entry.current_price !== null && entry.current_price !== 0) {
        return toNumber(entry.current_price) * quantity;
      }

      // 2. If DNSE deal profit is available for stock without explicit manual price:
      if (assetType === 'STOCK' && hasDealBySymbol(entry)) {
        return (entryPrice * quantity) + getUnrealizedProfit(entry);
      }

      if (assetType === 'GOLD') {
        const unitCurrentPrice = getCurrentPrice(entry);
        if (unitCurrentPrice === null) return entryPrice * quantity;
        return unitCurrentPrice * quantity;
      }

      const currentPrice = getCurrentPrice(entry);
      if (currentPrice === null) return entryPrice * quantity;
      return currentPrice * quantity;
    };

    const getEntryDisplayValue = (entry) => {
      const currentValue = getCurrentValue(entry);
      if (currentValue !== null) return currentValue;
      return (entry?.price || 0) * (entry?.quantity || 0);
    };

    const getBookValue = (entry) => {
      const rawValue = (toNumber(entry?.price) ?? 0) * (toNumber(entry?.quantity) ?? 0);
      return String(entry?.asset_type || '').toUpperCase() === 'DEBT' ? -rawValue : rawValue;
    };

    const compareNullable = (left, right) => {
      const leftMissing = left === null || left === undefined || left === '';
      const rightMissing = right === null || right === undefined || right === '';

      if (leftMissing && rightMissing) return 0;
      if (leftMissing) return 1;
      if (rightMissing) return -1;

      if (typeof left === 'number' && typeof right === 'number') {
        return left - right;
      }

      return String(left).localeCompare(String(right), 'vi', { numeric: true, sensitivity: 'base' });
    };

    const getSortValue = (entry, field) => {
      switch (field) {
        case 'entry_date':
          return new Date(entry?.entry_date || 0).getTime();
        case 'asset_type':
          return assetTypeLabels[String(entry?.asset_type || '').toUpperCase()] || String(entry?.asset_type || '');
        case 'symbol':
          return `${String(entry?.symbol || '').trim()} ${String(entry?.currency || 'VND').trim()}`.trim();
        case 'quantity':
          return toNumber(entry?.quantity) ?? 0;
        case 'price':
          return toNumber(entry?.price) ?? 0;
        case 'book_value':
          return getBookValue(entry);
        case 'current_value': {
          const currentValue = getCurrentValue(entry);
          if (currentValue === null) return null;
          return String(entry?.asset_type || '').toUpperCase() === 'DEBT' ? -currentValue : currentValue;
        }
        case 'change_percent':
          return getChangePercent(entry);
        case 'price_change':
          return getPriceChange(entry);
        default:
          return entry?.[field];
      }
    };

    const activeFilter = ref('ALL');
    const searchKeyword = ref('');

    const filterTabs = computed(() => {
      const allCount = entries.value.length;
      const counts = {
        ALL: allCount,
        GOLD: 0,
        CRYPTO: 0,
        STOCK: 0,
        SILVER: 0,
        REAL_ESTATE: 0,
        CASH: 0,
        DEBT: 0,
        OTHER: 0,
        HIGH_LOSS: 0
      };

      for (const entry of entries.value) {
        const type = String(entry?.asset_type || 'OTHER').toUpperCase();
        if (type === 'GOLD') counts.GOLD++;
        else if (type === 'CRYPTO') counts.CRYPTO++;
        else if (type === 'STOCK' || type === 'STOCK_VN') counts.STOCK++;
        else if (type === 'SILVER') counts.SILVER++;
        else if (type === 'REAL_ESTATE') counts.REAL_ESTATE++;
        else if (type === 'CASH') counts.CASH++;
        else if (type === 'DEBT') counts.DEBT++;
        else counts.OTHER++;

        if (isHighLoss(entry)) {
          counts.HIGH_LOSS++;
        }
      }

      const tabs = [
        { key: 'ALL', label: 'Tất cả', icon: '📁', count: counts.ALL },
        { key: 'GOLD', label: 'Vàng', icon: '🥇', count: counts.GOLD },
        { key: 'CRYPTO', label: 'Crypto', icon: '₿', count: counts.CRYPTO },
        { key: 'STOCK', label: 'Chứng khoán', icon: '📈', count: counts.STOCK },
        { key: 'SILVER', label: 'Bạc', icon: '🥈', count: counts.SILVER },
        { key: 'REAL_ESTATE', label: 'Bất động sản', icon: '🏠', count: counts.REAL_ESTATE },
        { key: 'CASH', label: 'Tiền mặt', icon: '💵', count: counts.CASH },
        { key: 'DEBT', label: 'Nợ', icon: '🔴', count: counts.DEBT },
        { key: 'OTHER', label: 'Khác', icon: '📦', count: counts.OTHER }
      ];

      const visibleTabs = tabs.filter(t => t.key === 'ALL' || t.count > 0);

      if (counts.HIGH_LOSS > 0) {
        visibleTabs.push({
          key: 'HIGH_LOSS',
          label: 'Cảnh báo lỗ (≤ -5%)',
          icon: '⚠️',
          count: counts.HIGH_LOSS
        });
      }

      return visibleTabs;
    });

    const filteredEntries = computed(() => {
      let list = entries.value;

      if (activeFilter.value === 'HIGH_LOSS') {
        list = list.filter(e => isHighLoss(e));
      } else if (activeFilter.value !== 'ALL') {
        list = list.filter(e => {
          const type = String(e?.asset_type || 'OTHER').toUpperCase();
          if (activeFilter.value === 'STOCK') {
            return type === 'STOCK' || type === 'STOCK_VN';
          }
          return type === activeFilter.value;
        });
      }

      const q = (searchKeyword.value || '').trim().toLowerCase();
      if (q) {
        list = list.filter(e => {
          const sym = String(e?.symbol || '').toLowerCase();
          const notes = String(e?.notes || '').toLowerCase();
          const type = String(e?.asset_type || '').toLowerCase();
          const label = String(assetTypeLabels[e?.asset_type] || '').toLowerCase();
          return sym.includes(q) || notes.includes(q) || type.includes(q) || label.includes(q);
        });
      }

      return list;
    });

    const sortedEntries = computed(() => {
      const { field, direction } = sortState.value;
      const directionFactor = direction === 'asc' ? 1 : -1;

      return filteredEntries.value
        .map((entry, index) => ({ entry, index }))
        .sort((left, right) => {
          const valueCompare = compareNullable(
            getSortValue(left.entry, field),
            getSortValue(right.entry, field)
          );

          if (valueCompare !== 0) {
            return valueCompare * directionFactor;
          }

          return left.index - right.index;
        })
        .map(item => item.entry);
    });

    const convertToVnd = (amount, currency) => {
      const normalizedCurrency = currency || 'VND';
      if (normalizedCurrency === 'USD') {
        const rate = usdToVndRate.value || 25450;
        return amount * rate;
      }
      return amount;
    };

    const totalAssetValueVnd = computed(() => {
      return entries.value.reduce((sum, entry) => {
        const assetType = String(entry?.asset_type || '').toUpperCase();
        const entryValue = getEntryDisplayValue(entry);
        const vndValue = convertToVnd(entryValue, entry.currency);
        // DEBT is subtracted from total
        return sum + (assetType === 'DEBT' ? -vndValue : vndValue);
      }, 0);
    });

    const allocationSegments = computed(() => {
      const totalsByType = {};
      const costsByType = {};

      for (const entry of entries.value) {
        const assetType = String(entry?.asset_type || 'OTHER').toUpperCase();
        const entryValue = getEntryDisplayValue(entry);
        const vndValue = convertToVnd(entryValue, entry.currency);
        if (!Number.isFinite(vndValue) || vndValue <= 0) continue;

        // DEBT is shown in allocation as a liability bucket, so it uses absolute value.
        const segmentValue = assetType === 'DEBT' ? Math.abs(vndValue) : vndValue;
        totalsByType[assetType] = (totalsByType[assetType] || 0) + segmentValue;

        // Calculate original cost in VND
        const rawCost = (toNumber(entry?.price) ?? 0) * (toNumber(entry?.quantity) ?? 0);
        const costVnd = convertToVnd(rawCost, entry.currency);
        if (Number.isFinite(costVnd) && costVnd > 0) {
          costsByType[assetType] = (costsByType[assetType] || 0) + (assetType === 'DEBT' ? Math.abs(costVnd) : costVnd);
        }
      }

      const rows = Object.entries(totalsByType)
        .map(([key, value]) => {
          const cost = costsByType[key] || 0;
          let growth = null;
          if (cost > 0 && key !== 'DEBT' && key !== 'CASH') {
            growth = ((value - cost) / cost) * 100;
          }
          return {
            key,
            value,
            cost,
            growth,
            pnl: value - cost
          };
        })
        .sort((a, b) => b.value - a.value);

      const total = rows.reduce((sum, row) => sum + row.value, 0);
      if (total <= 0) return [];

      const typeColorMap = {
        DEBT: '#dc2626'
      };
      const palette = ['#2563eb', '#16a34a', '#d97706', '#06b6d4', '#7c3aed', '#db2777', '#475569', '#65a30d'];

      const assetTypeIcons = {
        STOCK: '📈',
        CRYPTO: '₿',
        GOLD: '🥇',
        SILVER: '🥈',
        CASH: '💵',
        REAL_ESTATE: '🏠',
        DEBT: '🔴',
        OTHER: '📦'
      };

      return rows.map((row, idx) => ({
        ...row,
        label: assetTypeLabels[row.key] || row.key,
        icon: assetTypeIcons[row.key] || '📦',
        percent: (row.value / total) * 100,
        color: typeColorMap[row.key] || palette[idx % palette.length]
      }));
    });

    const totalAllocationValue = computed(() => {
      return allocationSegments.value.reduce((sum, segment) => {
        return sum + (segment.key === 'DEBT' ? -segment.value : segment.value);
      }, 0);
    });

    const totalAllocationCost = computed(() => {
      return allocationSegments.value
        .filter(s => s.key !== 'DEBT' && s.key !== 'CASH')
        .reduce((sum, s) => sum + (s.cost || 0), 0);
    });

    const totalAllocationGrowth = computed(() => {
      const investable = allocationSegments.value.filter(s => s.key !== 'DEBT' && s.key !== 'CASH');
      const totalCost = investable.reduce((sum, s) => sum + (s.cost || 0), 0);
      const totalVal = investable.reduce((sum, s) => sum + (s.value || 0), 0);
      if (totalCost <= 0) return null;
      return ((totalVal - totalCost) / totalCost) * 100;
    });

    const pieChartConicStyle = computed(() => {
      if (allocationSegments.value.length === 0) {
        return { background: 'conic-gradient(#e2e8f0 0 360deg)' };
      }

      let currentAngle = 0;
      const slices = allocationSegments.value.map(segment => {
        const start = currentAngle;
        const end = currentAngle + (segment.percent / 100) * 360;
        currentAngle = end;
        return `${segment.color} ${start.toFixed(2)}deg ${end.toFixed(2)}deg`;
      });

      return { background: `conic-gradient(${slices.join(', ')})` };
    });

    const getChangePercent = (entry) => {
      const assetType = String(entry?.asset_type || '').toUpperCase();
      if (assetType === 'DEBT' || assetType === 'CASH') return null;
      const totalCost = (toNumber(entry?.price) ?? 0) * (toNumber(entry?.quantity) ?? 0);
      if (totalCost === 0) return null;
      const currentVal = getCurrentValue(entry);
      if (currentVal === null) return null;
      return ((currentVal - totalCost) / totalCost) * 100;
    };

    const getPriceChange = (entry) => {
      const assetType = String(entry?.asset_type || '').toUpperCase();
      if (assetType === 'DEBT' || assetType === 'CASH') return null;
      const currentVal = getCurrentValue(entry);
      if (currentVal === null) return null;
      const bookValue = (toNumber(entry?.price) ?? 0) * (toNumber(entry?.quantity) ?? 0);
      return currentVal - bookValue;
    };

    const isHighLoss = (entry) => {
      const change = getChangePercent(entry);
      return change !== null && Number.isFinite(change) && change <= -5;
    };

    const getUsdToVndTooltip = (value, currency) => {
      if (String(currency || '').toUpperCase() !== 'USD') return null;
      const num = Number(value);
      if (!Number.isFinite(num)) return null;
      const rate = usdToVndRate.value || 25450;
      const vndVal = num * rate;
      return `Quy đổi: ≈ ${formatCurrency(Math.round(vndVal), 'VND')}`;
    };

    const getPriceChangeTooltip = (entry) => {
      const curVal = getCurrentValue(entry);
      const bookVal = getBookValue(entry);
      const diff = getPriceChange(entry);
      if (curVal === null || diff === null) return null;

      if (String(entry?.currency || '').toUpperCase() === 'USD') {
        const rate = usdToVndRate.value || 25450;
        const diffVnd = diff * rate;
        const sign = diff >= 0 ? '+' : '';
        return `Quy đổi: ≈ ${sign}${formatCurrency(Math.round(diffVnd), 'VND')}`;
      }
      return `Hiện tại: ${formatCurrency(curVal, entry.currency)} | Giá trị gốc: ${formatCurrency(bookVal, entry.currency)}`;
    };

    const getChangePercentTooltip = (entry) => {
      const pct = getChangePercent(entry);
      const isLoss = isHighLoss(entry);
      if (pct === null) return isLoss ? 'Cần chú ý, thanh lý sớm nếu không muốn lỗ nặng hơn' : null;
      const warning = isLoss ? '⚠️ Cần chú ý, thanh lý sớm nếu không muốn lỗ nặng hơn\n' : '';
      if (String(entry?.currency || '').toUpperCase() === 'USD') {
        const diff = getPriceChange(entry);
        const rate = usdToVndRate.value || 25450;
        const sign = pct >= 0 ? '+' : '';
        const diffVnd = diff !== null ? (diff * rate) : 0;
        return `${warning}Tỷ suất: ${sign}${pct.toFixed(2)}%\n` +
               `Quy đổi lãi/lỗ: ≈ ${sign}${formatCurrency(Math.round(diffVnd), 'VND')}`;
      }
      return isLoss ? 'Cần chú ý, thanh lý sớm nếu không muốn lỗ nặng hơn' : null;
    };

    const toggleSort = (field) => {
      if (sortState.value.field === field) {
        sortState.value.direction = sortState.value.direction === 'asc' ? 'desc' : 'asc';
        return;
      }

      sortState.value = {
        field,
        direction: field === 'entry_date' ? 'desc' : 'asc'
      };
    };

    const getSortIndicator = (field) => {
      if (sortState.value.field !== field) return '↕';
      return sortState.value.direction === 'asc' ? '↑' : '↓';
    };

    const getSortIndicatorClass = (field) => {
      return sortState.value.field === field ? 'is-active' : '';
    };

    const generateAiPrompt = async () => {
        const now = new Date().toLocaleString('vi-VN');
        let assetsList = '';
        entries.value.forEach(entry => {
            assetsList += `- ${entry.symbol} (${entry.asset_type}): ${entry.quantity} units @ ${formatCurrency(entry.price, entry.currency)}\n`;
        });
        
        let thesesText = '';
        try {
          const response = await fetch('/api/osint/theses');
          if (response.ok) {
            const theses = await response.json();
            if (theses && theses.length > 0) {
              thesesText = '\n--- TÌNH HÌNH VĨ MÔ HIỆN TẠI ---\n';
              theses.slice(0, 3).forEach(t => {
                thesesText += `Nhận định: ${t.thesis}\nCơ sở: ${t.supporting_evidence}\n\n`;
              });
            }
          }
        } catch (e) {
          console.error("Error fetching theses for prompt", e);
        }

        generatedPrompt.value = `Hôm nay là ${now}.
Dưới đây là Danh mục tài sản hiện tại của tôi:
${assetsList}
${thesesText}
Nhiệm vụ của bạn là: Tính ra giá trị hiện tại của toàn bộ tài sản này, sau đó kết hợp với tình hình vĩ mô để phân tích, đánh giá rủi ro và đưa ra lời khuyên hành động cụ thể cho từng tài sản mà tôi đang nắm giữ.`;
        aiResponse.value = '';
    };

    const askAI = async () => {
        if (!generatedPrompt.value || generatedPrompt.value.trim() === '') {
            return;
        }
        
        isAnalyzing.value = true;
        aiResponse.value = '';
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: generatedPrompt.value,
                    use_groq: false
                })
            });

            if (!response.ok) {
                throw new Error('Không thể kết nối đến máy chủ AI');
            }

            const data = await response.json();

            if (data.gemini_failed) {
                const proceedWithGroq = confirm("Gemini API không khả dụng. Bạn có muốn chuyển sang sử dụng Groq (có tính phí) không?");
                if (proceedWithGroq) {
                    aiResponse.value = '🔄 Đang chuyển hướng yêu cầu sang Groq... Vui lòng đợi.';
                    const groqResponse = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            message: generatedPrompt.value,
                            use_groq: true
                        })
                    });

                    if (!groqResponse.ok) {
                        throw new Error('Groq API cũng gặp sự cố');
                    }

                    const groqData = await groqResponse.json();
                    aiResponse.value = groqData.response || 'Không thể lấy phản hồi từ Groq.';
                } else {
                    aiResponse.value = '❌ Yêu cầu phân tích đã bị hủy.';
                }
            } else {
                aiResponse.value = data.response || 'Không thể lấy phản hồi từ AI.';
            }
        } catch (err) {
            console.error('Ask AI Error:', err);
            aiResponse.value = 'Rất tiếc, đã xảy ra lỗi trong quá trình xử lý yêu cầu AI. Vui lòng thử lại sau.';
        } finally {
            isAnalyzing.value = false;
        }
    };

    const getUserInfo = () => {
        if (clerkUser && clerkUser.value) {
          const u = clerkUser.value;
          const userEmail = u.primaryEmailAddress?.emailAddress || u.username || u.id || '';
          return {
            id: userEmail,
            clerkId: u.id,
            name: u.fullName || u.username || userEmail || 'User',
            email: userEmail,
            custodyCode: userEmail
          };
        }
        const userInfoStr = localStorage.getItem('userInfo');
        if (userInfoStr) {
          try {
            return JSON.parse(userInfoStr);
          } catch (e) {
            // Ignore parse error
          }
        }
        return null;
    };

    const getHeaders = () => {
        const userInfo = getUserInfo();
        const token = localStorage.getItem('token') || (isClerkSignedIn && isClerkSignedIn.value ? 'clerk_session' : '');
        return {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : '',
            'X-User-ID': userInfo ? (userInfo.id || userInfo.custodyCode || '') : '' 
        };
    };

    const JOURNAL_CACHE_KEY_PREFIX = 'journal_entries_cache_';

    const loadCachedEntries = () => {
      try {
        const userInfo = getUserInfo();
        if (!userInfo) return;
        const userId = userInfo.id || userInfo.custodyCode;
        if (!userId) return;
        const cached = localStorage.getItem(`${JOURNAL_CACHE_KEY_PREFIX}${userId}`);
        if (cached) {
          const parsed = JSON.parse(cached);
          if (Array.isArray(parsed) && parsed.length > 0) {
            entries.value = parsed;
            isLoading.value = false;
          }
        }
      } catch (e) {
        console.warn('Error reading journal cache:', e);
      }
    };

    const fetchEntries = async () => {
      if (entries.value.length === 0) {
        isLoading.value = true;
      }
      try {
        const userInfo = getUserInfo();
        if (!userInfo) {
            return;
        }

        const userId = userInfo.id || userInfo.email || userInfo.custodyCode;
        const response = await fetch(`/journal?user_id=${encodeURIComponent(userId)}`, {
            headers: getHeaders(),
            signal: AbortSignal.timeout(8000)
        });
        
        if (response.status === 401) {
            router.push('/login');
            return;
        }

        let list = [];
        if (response.ok) {
            const data = await response.json();
            list = Array.isArray(data) ? data : [];
        }

        entries.value = list;
        try {
          localStorage.setItem(`${JOURNAL_CACHE_KEY_PREFIX}${userId}`, JSON.stringify(list));
        } catch (e) {
          console.warn('Error saving journal cache:', e);
        }
      } catch (error) {
        console.error('Error fetching journal, falling back to cache:', error);
        if (entries.value.length === 0) {
          loadCachedEntries();
        }
      } finally {
        isLoading.value = false;
      }
    };

    const fetchDealsProfitBySymbol = async () => {
      const accountNumber = String(props.accountNumber || '').trim();
      if (!accountNumber) {
        dealProfitBySymbol.value = {};
        return;
      }

      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        const response = await fetch(`/dnse-deal-service/deals?accountNo=${encodeURIComponent(accountNumber)}`, {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: AbortSignal.timeout(6000)
        });
        if (!response.ok) {
          return;
        }

        const data = await response.json();
        const nextProfitBySymbol = {};
        const dealsList = Array.isArray(data?.deals) ? data.deals : [];

        for (const item of dealsList) {
          const symbol = String(item?.symbol || '').toUpperCase().trim();
          if (!symbol) continue;

          const unrealizedProfit = toNumber(item?.unrealizedProfit) ?? 0;
          nextProfitBySymbol[symbol] = (nextProfitBySymbol[symbol] || 0) + unrealizedProfit;
        }

        dealProfitBySymbol.value = nextProfitBySymbol;
      } catch (error) {
        console.error('Error fetching deal profits:', error);
      }
    };

    const isUpdatingPrices = ref(false);

    const fetchDirectLivePrice = async (entry) => {
      const assetType = String(entry?.asset_type || '').toUpperCase();
      const symbol = String(entry?.symbol || '').toUpperCase().trim();
      const currency = String(entry?.currency || 'VND').toUpperCase();

      if (assetType === 'CASH' || assetType === 'DEBT') {
        return 1.0;
      }

      if (assetType === 'CRYPTO') {
        try {
          const cleanSym = symbol.replace('/', '').replace('USDT', '').replace('USD', '').trim();
          if (cleanSym) {
            const bRes = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${cleanSym}USDT`, { signal: AbortSignal.timeout(4000) });
            if (bRes.ok) {
              const bData = await bRes.json();
              const usdPrice = parseFloat(bData.price);
              if (usdPrice && usdPrice > 0) {
                return currency === 'VND' ? usdPrice * (usdToVndRate.value || 25450) : usdPrice;
              }
            }
          }
        } catch (e) {
          console.warn(`Binance ticker fetch failed for ${symbol}:`, e);
        }
      }

      if (assetType === 'STOCK' || assetType === 'STOCK_VN') {
        const isVnStock = (/^[A-Z0-9]{3}$/.test(symbol) || assetType === 'STOCK_VN') && currency === 'VND';
        if (isVnStock) {
          // 1. KBS API (Direct match price / close price)
          try {
            const kbsRes = await fetch('https://kbbuddywts.kbsec.com.vn/iis-server/investment/stock/iss', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'x-lang': 'vi'
              },
              body: JSON.stringify({ code: symbol.toUpperCase().trim() }),
              signal: AbortSignal.timeout(4000)
            });
            if (kbsRes.ok) {
              const kbsData = await kbsRes.json();
              if (Array.isArray(kbsData) && kbsData.length > 0) {
                const item = kbsData[0];
                const price = item?.CP || item?.RE || item?.OP;
                if (price && price > 0) {
                  return price;
                }
              }
            }
          } catch (e) {
            console.warn(`KBS API fetch failed for ${symbol}:`, e);
          }

          // 2. Entrade / DNSE Securities product API fallback
          try {
            const secRes = await fetch(`https://services.entrade.com.vn/dnse-financial-product/securities/${symbol}`, { signal: AbortSignal.timeout(4000) });
            if (secRes.ok) {
              const secData = await secRes.json();
              const price = secData?.basicPrice || secData?.closePrice || secData?.matchPrice;
              if (price && price > 0) {
                return price;
              }
            }
          } catch (e) {
            console.warn(`Entrade securities fetch failed for ${symbol}:`, e);
          }

          // 3. Entrade Chart API with resolution='D' (look back 30 days so weekends/holidays are covered)
          try {
            const nowSec = Math.floor(Date.now() / 1000);
            const fromSec = nowSec - (30 * 86400);
            const eRes = await fetch(`https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol=${symbol}&resolution=D&from=${fromSec}&to=${nowSec}`, { signal: AbortSignal.timeout(4000) });
            if (eRes.ok) {
              const eData = await eRes.json();
              if (eData && Array.isArray(eData.c) && eData.c.length > 0) {
                const closePrice = eData.c[eData.c.length - 1];
                if (closePrice && closePrice > 0) {
                  return closePrice;
                }
              }
            }
          } catch (e) {
            console.warn(`Entrade daily chart fetch failed for ${symbol}:`, e);
          }

          // 4. VNDirect Finfo API fallback
          try {
            const vnRes = await fetch(`https://api-finfo.vndirect.com.vn/v4/stocks?q=code:${symbol}`, { signal: AbortSignal.timeout(4000) });
            if (vnRes.ok) {
              const vnData = await vnRes.json();
              const item = Array.isArray(vnData?.data) ? vnData.data[0] : null;
              const price = item?.basicPrice || item?.closePrice;
              if (price && price > 0) {
                return price;
              }
            }
          } catch (e) {
            console.warn(`VNDirect finfo fetch failed for ${symbol}:`, e);
          }
        } else {
          try {
            const yRes = await fetch(`/yahoo-finance/v8/finance/chart/${symbol}?interval=1d&range=1d`, { signal: AbortSignal.timeout(5000) });
            if (yRes.ok) {
              const yData = await yRes.json();
              const price = yData?.chart?.result?.[0]?.meta?.regularMarketPrice;
              if (price && price > 0) {
                return currency === 'VND' ? price * (usdToVndRate.value || 25450) : price;
              }
            }
          } catch (e) {
            console.warn(`Yahoo Finance fetch failed for ${symbol}:`, e);
          }
        }
      }

      if (assetType === 'GOLD') {
        const goldVnd = findGoldBuyValueBySymbol(symbol) || getBaseSjcGoldPrice();
        if (goldVnd && goldVnd > 0) {
          return currency === 'USD' ? (goldVnd / (usdToVndRate.value || 25450)) : goldVnd;
        }
        try {
          const yRes = await fetch(`/yahoo-finance/v8/finance/chart/GC=F?interval=1d&range=1d`, { signal: AbortSignal.timeout(4000) });
          if (yRes.ok) {
            const yData = await yRes.json();
            const price = yData?.chart?.result?.[0]?.meta?.regularMarketPrice;
            if (price && price > 0) {
              return currency === 'VND' ? price * (usdToVndRate.value || 25450) : price;
            }
          }
        } catch (e) {
          console.warn(`Gold Yahoo fetch failed:`, e);
        }
      }

      if (assetType === 'SILVER') {
        try {
          const yRes = await fetch(`/yahoo-finance/v8/finance/chart/SI=F?interval=1d&range=1d`, { signal: AbortSignal.timeout(4000) });
          if (yRes.ok) {
            const yData = await yRes.json();
            const price = yData?.chart?.result?.[0]?.meta?.regularMarketPrice;
            if (price && price > 0) {
              return currency === 'VND' ? price * (usdToVndRate.value || 25450) : price;
            }
          }
        } catch (e) {
          console.warn(`Silver Yahoo fetch failed:`, e);
        }
      }

      const calculated = getCurrentPrice(entry);
      if (calculated !== null && calculated > 0) {
        return calculated;
      }

      return entry?.price || null;
    };

    const updateAllCurrentPrices = async () => {
      if (isUpdatingPrices.value || entries.value.length === 0) return;
      isUpdatingPrices.value = true;
      try {
        // Reset any custom gold price back to market price as requested
        customGoldPrice.value = null;
        try {
          localStorage.removeItem(CUSTOM_GOLD_PRICE_KEY);
        } catch (e) {
          /* ignore */
        }

        const userInfo = getUserInfo();
        const userId = userInfo ? (userInfo.id || userInfo.custodyCode) : '';
        if (!userId) {
          notify({ type: 'warn', title: 'Cảnh báo', text: 'Vui lòng đăng nhập để cập nhật giá.' });
          return;
        }

        // 1. Refresh global rates & Batch fetch KBS prices for all VN stocks in portfolio
        const vnStockSymbols = Array.from(new Set(
          entries.value
            .filter(e => {
              const type = (e.asset_type || '').toUpperCase();
              const cur = (e.currency || 'VND').toUpperCase();
              const sym = (e.symbol || '').toUpperCase().trim();
              return (type === 'STOCK' || type === 'STOCK_VN') && (/^[A-Z0-9]{3}$/.test(sym) || type === 'STOCK_VN') && cur === 'VND';
            })
            .map(e => (e.symbol || '').toUpperCase().trim())
            .filter(Boolean)
        ));

        const kbsBatchPromise = (async () => {
          if (vnStockSymbols.length === 0) return {};
          try {
            const kbsRes = await fetch('https://kbbuddywts.kbsec.com.vn/iis-server/investment/stock/iss', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'x-lang': 'vi'
              },
              body: JSON.stringify({ code: vnStockSymbols.join(',') }),
              signal: AbortSignal.timeout(5000)
            });
            if (kbsRes.ok) {
              const kbsData = await kbsRes.json();
              const map = {};
              if (Array.isArray(kbsData)) {
                for (const item of kbsData) {
                  const sym = item?.SB?.toUpperCase();
                  const price = item?.CP || item?.RE || item?.OP;
                  if (sym && price && price > 0) {
                    map[sym] = price;
                  }
                }
              }
              return map;
            }
          } catch (err) {
            console.warn('Batch KBS API fetch failed, falling back to individual:', err);
          }
          return {};
        })();

        const [, , , , kbsPriceMap] = await Promise.all([
          loadUsdVndRate(),
          loadGoldPrices(),
          fetchDealsProfitBySymbol(),
          fetchUsdVndRate(),
          kbsBatchPromise
        ]);

        // 2. Calculate latest unit price for each entry
        const updates = [];
        for (const entry of entries.value) {
          try {
            const sym = (entry.symbol || '').toUpperCase().trim();
            const type = (entry.asset_type || '').toUpperCase();
            const cur = (entry.currency || 'VND').toUpperCase();
            let livePrice = null;

            if ((type === 'STOCK' || type === 'STOCK_VN') && cur === 'VND' && kbsPriceMap && kbsPriceMap[sym]) {
              livePrice = kbsPriceMap[sym];
            } else {
              livePrice = await fetchDirectLivePrice(entry);
            }

            if (livePrice !== null && Number.isFinite(livePrice) && livePrice > 0) {
              updates.push({
                id: entry.id,
                current_price: livePrice
              });
            }
          } catch (err) {
            console.warn(`Error computing live price for ${entry.symbol}:`, err);
          }
        }

        if (updates.length === 0) {
          notify({ type: 'warn', title: 'Thông báo', text: 'Không tìm thấy dữ liệu giá mới để cập nhật.' });
          return;
        }

        // 3. Send batch update to Backend API
        const response = await fetch(`/journal/batch-prices?user_id=${userId}`, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify({ updates })
        });

        if (response.ok) {
          notify({
            type: 'success',
            title: '🎉 Cập nhật thành công',
            text: `Đã tính và cập nhật giá hiện tại cho ${updates.length} tài sản trong danh mục!`
          });
          await fetchEntries();
        } else {
          // Fallback: Individual PUT updates
          let updatedCount = 0;
          for (const u of updates) {
            const item = entries.value.find(e => e.id === u.id);
            if (!item) continue;
            const putBody = {
              id: item.id,
              asset_type: item.asset_type,
              symbol: item.symbol,
              quantity: item.quantity,
              price: item.price,
              currency: item.currency || 'VND',
              entry_date: new Date(item.entry_date).toISOString(),
              notes: item.notes || '',
              current_price: u.current_price
            };
            try {
              const res = await fetch(`/journal?user_id=${userId}`, {
                method: 'PUT',
                headers: getHeaders(),
                body: JSON.stringify(putBody)
              });
              if (res.ok) updatedCount++;
            } catch (e) {
              console.warn(`Failed individual update for item ${item.id}:`, e);
            }
          }
          notify({
            type: 'success',
            title: '🎉 Cập nhật thành công',
            text: `Đã tính và cập nhật giá hiện tại cho ${updatedCount} tài sản trong danh mục!`
          });
          await fetchEntries();
        }
      } catch (error) {
        console.error('Lỗi khi cập nhật giá danh mục:', error);
        notify({ type: 'error', title: 'Lỗi', text: 'Có lỗi xảy ra khi cập nhật giá thị trường.' });
      } finally {
        isUpdatingPrices.value = false;
      }
    };

    const syncGoldPriceDisplay = () => {
      customGoldPriceDisplay.value = customGoldPriceInput.value ? formatNumber(customGoldPriceInput.value) : '';
    };

    const openGoldPriceModal = () => {
      if (customGoldPrice.value && customGoldPrice.value > 0) {
        customGoldPriceInput.value = customGoldPrice.value;
      } else {
        customGoldPriceInput.value = getRawMarketGoldPrice();
      }
      syncGoldPriceDisplay();
      showGoldPriceModal.value = true;
    };

    const closeGoldPriceModal = () => {
      showGoldPriceModal.value = false;
    };

    const adjustGoldPriceInput = (delta) => {
      const current = Number(customGoldPriceInput.value) || 0;
      customGoldPriceInput.value = Math.max(0, current + delta);
      syncGoldPriceDisplay();
    };

    const applyMarketPriceToInput = (price) => {
      if (price && price > 0) {
        customGoldPriceInput.value = price;
        syncGoldPriceDisplay();
      }
    };

    const saveCustomGoldPrice = async () => {
      const price = Number(customGoldPriceInput.value);
      if (!price || isNaN(price) || price <= 0) {
        notify({ type: 'warn', title: 'Giá không hợp lệ', text: 'Vui lòng nhập giá vàng lớn hơn 0.' });
        return;
      }

      isSavingGoldPrice.value = true;
      try {
        customGoldPrice.value = price;
        localStorage.setItem(CUSTOM_GOLD_PRICE_KEY, String(price));

        const userInfo = getUserInfo();
        const userId = userInfo ? (userInfo.id || userInfo.custodyCode) : '';

        // Find all gold items in portfolio
        const goldEntries = entries.value.filter(e => (e.asset_type || '').toUpperCase() === 'GOLD');
        const updates = [];

        for (const entry of goldEntries) {
          const isUsd = (entry.currency || 'VND').toUpperCase() === 'USD';
          const newPrice = isUsd ? (price / (usdToVndRate.value || 25450)) : price;
          entry.current_price = newPrice;
          updates.push({
            id: entry.id,
            current_price: newPrice
          });
        }

        if (updates.length > 0 && userId) {
          try {
            const response = await fetch(`/journal/batch-prices?user_id=${userId}`, {
              method: 'POST',
              headers: getHeaders(),
              body: JSON.stringify({ updates })
            });

            if (!response.ok) {
              for (const u of updates) {
                const item = entries.value.find(e => e.id === u.id);
                if (!item) continue;
                await fetch(`/journal?user_id=${userId}`, {
                  method: 'PUT',
                  headers: getHeaders(),
                  body: JSON.stringify({
                    id: item.id,
                    asset_type: item.asset_type,
                    symbol: item.symbol,
                    quantity: item.quantity,
                    price: item.price,
                    currency: item.currency || 'VND',
                    entry_date: new Date(item.entry_date).toISOString(),
                    notes: item.notes || '',
                    current_price: u.current_price
                  })
                });
              }
            }
          } catch (apiErr) {
            console.warn('Failed saving gold price updates to backend:', apiErr);
          }
        }

        notify({
          type: 'success',
          title: '🎉 Cập nhật thành công',
          text: goldEntries.length > 0 
            ? `Đã cập nhật giá vàng ${formatCurrency(price, 'VND')} cho ${goldEntries.length} tài sản vàng!`
            : `Đã lưu giá vàng tùy chỉnh ${formatCurrency(price, 'VND')}!`
        });

        closeGoldPriceModal();
      } catch (err) {
        console.error('Error saving custom gold price:', err);
        notify({ type: 'error', title: 'Lỗi', text: 'Không thể cập nhật giá vàng. Vui lòng thử lại.' });
      } finally {
        isSavingGoldPrice.value = false;
      }
    };

    const resetGoldPriceToMarket = async () => {
      isSavingGoldPrice.value = true;
      try {
        customGoldPrice.value = null;
        localStorage.removeItem(CUSTOM_GOLD_PRICE_KEY);

        const userInfo = getUserInfo();
        const userId = userInfo ? (userInfo.id || userInfo.custodyCode) : '';

        const goldEntries = entries.value.filter(e => (e.asset_type || '').toUpperCase() === 'GOLD');
        const updates = [];

        for (const entry of goldEntries) {
          const goldVnd = findGoldBuyValueBySymbol(entry.symbol) || getRawMarketGoldPrice();
          if (goldVnd && goldVnd > 0) {
            const isUsd = (entry.currency || 'VND').toUpperCase() === 'USD';
            const newPrice = isUsd ? (goldVnd / (usdToVndRate.value || 25450)) : goldVnd;
            entry.current_price = newPrice;
            updates.push({
              id: entry.id,
              current_price: newPrice
            });
          }
        }

        if (updates.length > 0 && userId) {
          try {
            await fetch(`/journal/batch-prices?user_id=${userId}`, {
              method: 'POST',
              headers: getHeaders(),
              body: JSON.stringify({ updates })
            });
          } catch (e) {
            console.warn('Failed resetting gold prices in backend:', e);
          }
        }

        notify({
          type: 'info',
          title: 'Đã khôi phục',
          text: 'Đã khôi phục giá vàng theo giá thị trường API.'
        });

        closeGoldPriceModal();
      } catch (err) {
        console.error('Error resetting gold price:', err);
      } finally {
        isSavingGoldPrice.value = false;
      }
    };

    const openModal = (mode, entry = null) => {
      modalMode.value = mode;
      if (mode === 'edit' && entry) {
        formData.id = entry.id;
        formData.asset_type = entry.asset_type;
        formData.symbol = entry.symbol;
        formData.quantity = entry.quantity;
        formData.price = entry.price;
        formData.currency = entry.currency || 'VND';
        if (entry.asset_type === 'REAL_ESTATE') {
          realEstateCategory.value = Object.prototype.hasOwnProperty.call(realEstateSymbolMap, entry.symbol)
            ? entry.symbol
            : 'NHA';
        }
        quantityDisplay.value = formatNumber(entry.quantity);
        priceDisplay.value = formatNumber(entry.price);
        // Format date for datetime-local input (YYYY-MM-DDTHH:mm)
        formData.entry_date = new Date(entry.entry_date).toISOString().slice(0, 16);
        formData.notes = entry.notes;
        if (entry.current_price !== undefined && entry.current_price !== null && entry.current_price !== 0) {
          formData.current_price = entry.current_price;
          manualCurrentPriceDisplay.value = formatNumber(entry.current_price);
        } else {
          formData.current_price = null;
          manualCurrentPriceDisplay.value = '';
        }
      } else {
        // Reset form
        formData.id = null;
        formData.asset_type = 'STOCK';
        formData.symbol = '';
        realEstateCategory.value = 'NHA';
        formData.quantity = 0;
        formData.price = 0;
        formData.currency = 'VND';
        quantityDisplay.value = '0';
        priceDisplay.value = '0';
        formData.entry_date = new Date().toISOString().slice(0, 16);
        formData.notes = '';
        formData.current_price = null;
        manualCurrentPriceDisplay.value = '';
      }
      showModal.value = true;
    };

    const openAllocationModal = () => {
      showAllocationModal.value = true;
    };

    const closeAllocationModal = () => {
      showAllocationModal.value = false;
    };

    const closeModal = () => {
      showModal.value = false;
    };

    const submitForm = async () => {
        try {
            const userInfo = getUserInfo();
            const userId = userInfo ? (userInfo.id || userInfo.custodyCode) : '';
            
            // Backend expects user_id in query for all methods
            const url = `/journal?user_id=${userId}`;
            const method = modalMode.value === 'add' ? 'POST' : 'PUT';
            const body = { ...formData };
            body.entry_date = new Date(body.entry_date).toISOString();
            body.current_price = formData.current_price || null;

            const response = await fetch(url, {
                method: method,
                headers: getHeaders(),
                body: JSON.stringify(body)
            });

            if (response.ok) {
                closeModal();
                fetchEntries();
            } else {
                const errorText = await response.text();
                notify({ type: 'error', title: 'Error', text: `Failed to save entry: ${response.status} ${response.statusText}\n${errorText}` });
            }
        } catch (error) {
            console.error("Error saving entry:", error);
            notify({ type: 'error', title: 'Error', text: 'An error occurred.' });
        }
    };

    const deleteEntry = async (id) => {
        if (!confirm("Are you sure you want to delete this entry?")) return;
        
        try {
            const userInfo = getUserInfo();
            const userId = userInfo ? (userInfo.id || userInfo.custodyCode) : '';
            
            const response = await fetch(`/journal?id=${id}&user_id=${userId}`, {
                method: 'DELETE',
                headers: getHeaders()
            });

            if (response.ok) {
                fetchEntries();
            } else {
                const errorText = await response.text();
                notify({ type: 'error', title: 'Error', text: `Failed to delete entry: ${response.status} ${response.statusText}\n${errorText}` });
            }
        } catch (error) {
            console.error("Error deleting entry:", error);
        }
    };

    const formatLiveNumber = (val) => {
      if (val === null || val === undefined || val === '') return '';
      let raw = String(val).trim();
      if (!raw) return '';

      // If user starts typing with '.' or ',', auto prefix with '0.'
      if (raw.startsWith('.') || raw.startsWith(',')) {
        raw = '0.' + raw.slice(1);
      }

      let clean = '';
      if (raw.includes('.')) {
        // If there's already a dot '.', all commas are thousands separators
        clean = raw.replace(/,/g, '');
      } else if (raw.includes(',')) {
        // Only commas present.
        if (raw.endsWith(',')) {
          // User just pressed ',' -> treat as decimal dot '.'
          clean = raw.slice(0, -1).replace(/,/g, '') + '.';
        } else if (raw.startsWith('0,')) {
          // e.g. "0,1" -> "0.1"
          clean = '0.' + raw.slice(2).replace(/,/g, '');
        } else {
          // Standard thousands separators (e.g. "1,000", "10,000,000")
          clean = raw.replace(/,/g, '');
        }
      } else {
        clean = raw;
      }

      // Filter out invalid characters and handle dot
      const dotIdx = clean.indexOf('.');
      let intStr = '';
      let decStr = null;
      let hasTrailingDot = false;

      if (dotIdx !== -1) {
        intStr = clean.slice(0, dotIdx).replace(/[^0-9]/g, '');
        decStr = clean.slice(dotIdx + 1).replace(/[^0-9]/g, '');
        hasTrailingDot = true;
      } else {
        intStr = clean.replace(/[^0-9]/g, '');
        decStr = null;
        hasTrailingDot = false;
      }

      if (!intStr && decStr === null) return '';

      intStr = intStr || '0';
      // Remove leading zeros if more than 1 digit (e.g. "05" -> "5", but keep "0")
      if (intStr.length > 1 && intStr.startsWith('0')) {
        intStr = intStr.replace(/^0+/, '') || '0';
      }

      // Format integer part with commas every 3 digits
      const formattedInt = intStr.replace(/\B(?=(\d{3})+(?!\d))/g, ',');

      if (hasTrailingDot) {
        return `${formattedInt}.${decStr}`;
      }
      return formattedInt;
    };

    const applyLiveFormat = (e, updateFn) => {
      const input = e.target;
      const originalVal = input.value;
      const originalPos = input.selectionStart || 0;

      // Extract text before cursor and count digits/dots before cursor
      const sliceBefore = originalVal.slice(0, originalPos);
      let normSlice = sliceBefore;
      if (!originalVal.includes('.') && originalVal.includes(',')) {
        if (originalVal.endsWith(',')) {
          normSlice = sliceBefore.slice(0, -1).replace(/,/g, '') + '.';
        } else if (originalVal.startsWith('0,')) {
          normSlice = '0.' + sliceBefore.slice(2).replace(/,/g, '');
        } else {
          normSlice = sliceBefore.replace(/,/g, '');
        }
      } else {
        normSlice = sliceBefore.replace(/,/g, '');
      }

      const digitsBefore = normSlice.replace(/[^0-9.]/g, '').length;

      const formatted = formatLiveNumber(originalVal);
      const rawNum = parseFloat(formatted.replace(/,/g, '')) || 0;

      input.value = formatted;
      updateFn(formatted, rawNum);

      // Restore cursor position accurately taking newly inserted/removed commas into account
      if (input && typeof input.setSelectionRange === 'function') {
        requestAnimationFrame(() => {
          if ((originalVal === '.' || originalVal === ',') && formatted === '0.') {
            input.setSelectionRange(2, 2);
            return;
          }
          let newPos = 0;
          let count = 0;
          for (let i = 0; i < formatted.length; i++) {
            if (/[0-9.]/.test(formatted[i])) {
              count++;
            }
            if (count === digitsBefore) {
              newPos = i + 1;
              break;
            }
          }
          if (count < digitsBefore) {
            newPos = formatted.length;
          }
          input.setSelectionRange(newPos, newPos);
        });
      }
    };

    const onQuantityInput = (e) => {
      applyLiveFormat(e, (formatted, rawNum) => {
        quantityDisplay.value = formatted;
        formData.quantity = rawNum;
      });
    };
    const onQuantityBlur = () => {
      if (!quantityDisplay.value || quantityDisplay.value === '.' || quantityDisplay.value === '0.') {
        quantityDisplay.value = '0';
        formData.quantity = 0;
      } else if (quantityDisplay.value.endsWith('.')) {
        quantityDisplay.value = quantityDisplay.value.slice(0, -1);
      }
    };
    const onQuantityFocus = () => {
      if (formData.quantity === 0 && (quantityDisplay.value === '0' || quantityDisplay.value === '0.0')) {
        quantityDisplay.value = '';
      }
    };

    const onPriceInput = (e) => {
      applyLiveFormat(e, (formatted, rawNum) => {
        priceDisplay.value = formatted;
        formData.price = rawNum;
      });
    };
    const onPriceBlur = () => {
      if (!priceDisplay.value || priceDisplay.value === '.' || priceDisplay.value === '0.') {
        priceDisplay.value = '0';
        formData.price = 0;
      } else if (priceDisplay.value.endsWith('.')) {
        priceDisplay.value = priceDisplay.value.slice(0, -1);
      }
    };
    const onPriceFocus = () => {
      if (formData.price === 0 && (priceDisplay.value === '0' || priceDisplay.value === '0.0')) {
        priceDisplay.value = '';
      }
    };

    const onManualCurrentPriceInput = (e) => {
      applyLiveFormat(e, (formatted, rawNum) => {
        manualCurrentPriceDisplay.value = formatted;
        formData.current_price = formatted ? rawNum : null;
      });
    };
    const onManualCurrentPriceBlur = () => {
      if (!manualCurrentPriceDisplay.value || manualCurrentPriceDisplay.value === '.' || manualCurrentPriceDisplay.value === '0.') {
        manualCurrentPriceDisplay.value = '';
        formData.current_price = null;
      } else if (manualCurrentPriceDisplay.value.endsWith('.')) {
        manualCurrentPriceDisplay.value = manualCurrentPriceDisplay.value.slice(0, -1);
      }
    };
    const onManualCurrentPriceFocus = () => {
      if (formData.current_price === null || formData.current_price === undefined) {
        manualCurrentPriceDisplay.value = '';
      }
    };

    const onCustomGoldPriceInput = (e) => {
      applyLiveFormat(e, (formatted, rawNum) => {
        customGoldPriceDisplay.value = formatted;
        customGoldPriceInput.value = rawNum;
      });
    };
    const onCustomGoldPriceBlur = () => {
      if (!customGoldPriceDisplay.value || customGoldPriceDisplay.value === '.' || customGoldPriceDisplay.value === '0.') {
        customGoldPriceDisplay.value = customGoldPriceInput.value ? formatNumber(customGoldPriceInput.value) : '';
      } else if (customGoldPriceDisplay.value.endsWith('.')) {
        customGoldPriceDisplay.value = customGoldPriceDisplay.value.slice(0, -1);
      }
    };
    const onCustomGoldPriceFocus = () => {
      if (customGoldPriceInput.value === 0 && (customGoldPriceDisplay.value === '0' || customGoldPriceDisplay.value === '0.0')) {
        customGoldPriceDisplay.value = '';
      }
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        return new Date(dateStr).toLocaleDateString() + ' ' + new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const formatNumber = (value) => {
        if (value === null || value === undefined || isNaN(value)) return '0';
        return new Intl.NumberFormat('en-US', { maximumFractionDigits: 8 }).format(value);
    };

    const formatCurrency = (value, currency) => {
        const cur = currency || 'VND';
        if (cur === 'USD') {
            return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
        }
        return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
    };

    const getBadgeClass = (type) => {
        switch(type) {
            case 'GOLD': return 'bg-warning text-dark';
            case 'STOCK': return 'bg-success';
            case 'CRYPTO': return 'bg-info text-dark';
            case 'SILVER': return 'bg-secondary';
            case 'CASH': return 'bg-dark text-white';
            case 'DEBT': return 'bg-danger';
            default: return 'bg-primary';
        }
    };

    // Chart Modal State
    const showChartModal = ref(false);
    const chartTab = ref('tradingview'); // 'tradingview' | 'vietstock'
    const selectedChartAsset = ref({
      symbol: '',
      asset_type: '',
      currency: 'VND',
      name: ''
    });
    const chartSearchInput = ref('');
    const jnlChartSearchRef = ref(null);

    const isChartable = (entry) => {
      const type = String(entry?.asset_type || '').toUpperCase();
      return ['CRYPTO', 'STOCK', 'GOLD', 'SILVER'].includes(type);
    };

    const isLikelyUsStock = (symbol, currency) => {
      if (currency === 'USD') return true;
      const sym = String(symbol || '').toUpperCase().trim();
      if (sym.startsWith('NASDAQ:') || sym.startsWith('NYSE:') || sym.startsWith('AMEX:') || sym.startsWith('SP:')) return true;
      const usTickers = [
        'SPX', 'AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'META', 'NFLX', 
        'AMD', 'INTC', 'CRWD', 'OKTA', 'PLTR', 'COIN', 'BABA', 'NIO', 'DIS', 'PYPL', 
        'UBER', 'ABNB', 'ORCL', 'CRM', 'QCOM', 'TXN', 'AVGO', 'COST', 'PEP', 'KO', 
        'WMT', 'JPM', 'BAC', 'GS', 'MS', 'V', 'MA'
      ];
      return usTickers.includes(sym);
    };

    const isLikelyVnStock = (symbol, currency) => {
      if (currency === 'VND') return true;
      const sym = String(symbol || '').toUpperCase().trim();
      if (sym.startsWith('HOSE:') || sym.startsWith('HNX:') || sym.startsWith('UPCOM:')) return true;
      if (['VNINDEX', 'VN30', 'VN30F1M', 'HNXINDEX'].includes(sym)) return true;
      return false;
    };

    const isVnStockSelected = computed(() => {
      const type = String(selectedChartAsset.value.asset_type || '').toUpperCase();
      if (type !== 'STOCK') return false;
      const cur = selectedChartAsset.value.currency;
      const sym = selectedChartAsset.value.symbol;
      return isLikelyVnStock(sym, cur) && !isLikelyUsStock(sym, cur);
    });

    const isGoldAsset = (symbol, assetType) => {
      const type = String(assetType || '').toUpperCase();
      if (type === 'GOLD') return true;
      const s = String(symbol || '').trim().toUpperCase();
      return ['MI HỒNG', 'MI HONG', 'MIHONG', 'SJC', 'DOJI', 'PNJ', 'BTMC', 'VÀNG', 'VANG', 'GOLD', 'XAUUSD', 'GC=F'].includes(s) ||
             s.includes('MI HỒNG') || s.includes('MI HONG') || s.includes('SJC') || s.includes('DOJI') || s.includes('PNJ') || s.includes('VÀNG');
    };

    const isSilverAsset = (symbol, assetType) => {
      const type = String(assetType || '').toUpperCase();
      if (type === 'SILVER') return true;
      const s = String(symbol || '').trim().toUpperCase();
      return ['SILVER', 'BAC', 'BẠC', 'XAGUSD', 'SI=F'].includes(s) || s.includes('SILVER') || s.includes('BẠC');
    };

    const openChartModal = (entry) => {
      if (!entry || !entry.symbol) return;
      const rawSym = String(entry.symbol).trim();
      let assetType = String(entry.asset_type || 'STOCK').toUpperCase();
      let currency = entry.currency || 'VND';
      let chartSymbol = rawSym;
      let displayName = entry.name || '';
      let entryPrice = entry.price !== undefined && entry.price !== null ? entry.price : null;

      if (isGoldAsset(rawSym, assetType)) {
        assetType = 'GOLD';
        currency = 'USD';
        chartSymbol = 'XAUUSD';
        displayName = rawSym;
      } else if (isSilverAsset(rawSym, assetType)) {
        assetType = 'SILVER';
        currency = 'USD';
        chartSymbol = 'XAGUSD';
        displayName = rawSym;
      }

      if (entryPrice === null) {
        const found = entries.value.find(e => String(e.symbol || '').trim().toUpperCase() === rawSym.toUpperCase());
        if (found && found.price !== undefined && found.price !== null) {
          entryPrice = found.price;
        }
      }

      selectedChartAsset.value = {
        symbol: chartSymbol,
        asset_type: assetType,
        currency: currency,
        name: displayName,
        price: entryPrice
      };
      chartSearchInput.value = chartSymbol;
      chartTab.value = 'tradingview';

      showChartModal.value = true;
    };

    const closeChartModal = () => {
      showChartModal.value = false;
    };

    const applyChartSearch = (event) => {
      const inputElement = event?.currentTarget || jnlChartSearchRef.value;
      const input = (chartSearchInput.value || '').trim().toUpperCase();
      if (!input) return;

      let guessedType = selectedChartAsset.value.asset_type || 'STOCK';
      let guessedCurrency = selectedChartAsset.value.currency || 'VND';

      if (['XAUUSD', 'GOLD', 'SJC', 'MI HỒNG', 'MI HONG', 'DOJI', 'PNJ', 'GC=F'].includes(input) || input.includes('GOLD') || input.includes('VANG') || input.includes('MI HONG')) {
        guessedType = 'GOLD';
        guessedCurrency = 'USD';
      } else if (['XAGUSD', 'SILVER', 'SI=F'].includes(input) || input.includes('SILVER') || input.includes('BAC')) {
        guessedType = 'SILVER';
        guessedCurrency = 'USD';
      } else if (input.endsWith('USDT') || input.endsWith('BTC') || ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE', 'ADA', 'AVAX', 'LINK', 'DOT', 'NEAR', 'SUI', 'HYPE', 'ZEC', 'XMR'].includes(input)) {
        guessedType = 'CRYPTO';
        guessedCurrency = 'USD';
      } else if (isLikelyUsStock(input, 'USD')) {
        guessedType = 'STOCK';
        guessedCurrency = 'USD';
      } else {
        guessedType = 'STOCK';
        guessedCurrency = 'VND';
      }

      openChartModal({
        symbol: input,
        asset_type: guessedType,
        currency: guessedCurrency
      });

      nextTick(() => {
        requestAnimationFrame(() => {
          const target = jnlChartSearchRef.value || inputElement;
          target?.focus();
          target?.select();
        });
      });
    };

    const resolvedTvSymbol = computed(() => {
      const asset = selectedChartAsset.value;
      if (!asset || !asset.symbol) return '';
      const sym = asset.symbol.trim();
      const type = String(asset.asset_type || '').toUpperCase();

      if (sym.includes(':')) return sym;

      if (type === 'GOLD') {
        return 'OANDA:XAUUSD';
      }
      if (type === 'SILVER') {
        return 'OANDA:XAGUSD';
      }
      if (type === 'CRYPTO') {
        const upperSym = sym.toUpperCase();
        if (upperSym === 'ZEC') return 'KRAKEN:ZECUSD';
        if (upperSym === 'XMR') return 'KRAKEN:XMRUSD';
        if (upperSym.endsWith('USDT')) return `BINANCE:${upperSym}`;
        if (upperSym.endsWith('USD')) return `BINANCE:${upperSym.slice(0, -3)}USDT`;
        return `BINANCE:${upperSym}USDT`;
      }
      if (type === 'STOCK') {
        if (isLikelyUsStock(sym, asset.currency)) {
          if (sym.toUpperCase() === 'SPX') return 'SP:SPX';
          return sym.toUpperCase();
        }
        // VN stock
        const upperSym = sym.toUpperCase();
        if (upperSym === 'VNINDEX') return 'HOSE:VNINDEX';
        if (upperSym === 'VN30') return 'HOSE:VN30';
        if (upperSym === 'VN30F1M') return 'HNX:VN30F1M';
        if (upperSym === 'HNXINDEX') return 'HNX:HNXINDEX';
        return `HOSE:${upperSym}`;
      }

      return sym;
    });

    const resolvedVnCode = computed(() => {
      const asset = selectedChartAsset.value;
      if (!asset || !asset.symbol) return '';
      let sym = asset.symbol.trim().toUpperCase();
      if (sym.includes(':')) {
        sym = sym.split(':').pop();
      }
      return sym;
    });

    const quickChartChips = computed(() => {
      const chips = [];
      const seen = new Set();
      for (const entry of entries.value) {
        if (isChartable(entry)) {
          const rawSym = String(entry.symbol).trim();
          let assetType = String(entry.asset_type || 'STOCK').toUpperCase();
          let currency = entry.currency || 'VND';
          let chipSym = rawSym;
          let chipName = rawSym;

          if (isGoldAsset(rawSym, assetType)) {
            assetType = 'GOLD';
            currency = 'USD';
            chipSym = 'XAUUSD';
          } else if (isSilverAsset(rawSym, assetType)) {
            assetType = 'SILVER';
            currency = 'USD';
            chipSym = 'XAGUSD';
          }

          const key = `${chipSym.toUpperCase()}_${assetType}`;
          if (!seen.has(key)) {
            seen.add(key);
            chips.push({
              symbol: chipSym,
              asset_type: assetType,
              currency: currency,
              name: chipName !== chipSym ? chipName : '',
              price: entry.price
            });
          }
        }
      }
      return chips.slice(0, 10);
    });

    onMounted(() => {
      loadCachedEntries();
      fetchEntries();
      loadUsdVndRate();
      loadGoldPrices();
    });

    watch([() => isLoaded.value, () => clerkUser.value], ([loaded, user]) => {
      if (loaded && user) {
        loadCachedEntries();
        fetchEntries();
      }
    }, { immediate: true });

    watch(() => props.accountNumber, () => {
      fetchDealsProfitBySymbol();
    }, { immediate: true });

    return {
      entries,
      isLoading,
      showModal,
      showAllocationModal,
      modalMode,
      formData,
      realEstateCategory,
      quantityDisplay,
      priceDisplay,
      manualCurrentPriceDisplay,
      onQuantityInput,
      onQuantityBlur,
      onQuantityFocus,
      onPriceInput,
      onPriceBlur,
      onPriceFocus,
      onManualCurrentPriceInput,
      onManualCurrentPriceBlur,
      onManualCurrentPriceFocus,
      openModal,
      openAllocationModal,
      closeAllocationModal,
      closeModal,
      submitForm,
      deleteEntry,
      formatDate,
      formatNumber,
      formatCurrency,
      getBadgeClass,
      getCurrentPrice,
      getCurrentValue,
      getBookValue,
      toNumber,
      getChangePercent,
      getPriceChange,
      getUsdToVndTooltip,
      getPriceChangeTooltip,
      getChangePercentTooltip,
      sortedEntries,
      toggleSort,
      getSortIndicator,
      getSortIndicatorClass,
      totalAssetValueVnd,
      isCash,
      isDebt,
      isRealEstate,
      generatedPrompt,
      aiResponse,
      parsedAiResponse,
      generateAiPrompt,
      askAI,
      isAnalyzing,
      usdToVndRate,
      isRateLoading,
      hasUsdEntries,
      goldLatestDate,
      goldPriceRows,
      customGoldPrice,
      showGoldPriceModal,
      customGoldPriceInput,
      customGoldPriceDisplay,
      onCustomGoldPriceInput,
      onCustomGoldPriceBlur,
      onCustomGoldPriceFocus,
      isSavingGoldPrice,
      marketGoldOptions,
      baseMarketGoldPrice,
      goldEntriesCount,
      openGoldPriceModal,
      closeGoldPriceModal,
      saveCustomGoldPrice,
      resetGoldPriceToMarket,
      adjustGoldPriceInput,
      applyMarketPriceToInput,
      allocationSegments,
      totalAllocationValue,
      totalAllocationCost,
      totalAllocationGrowth,
      pieChartConicStyle,
      showChartModal,
      chartTab,
      selectedChartAsset,
      chartSearchInput,
      jnlChartSearchRef,
      isChartable,
      isVnStockSelected,
      openChartModal,
      closeChartModal,
      applyChartSearch,
      resolvedTvSymbol,
      resolvedVnCode,
      quickChartChips,
      isUpdatingPrices,
      updateAllCurrentPrices,
      isHighLoss,
      activeFilter,
      searchKeyword,
      filterTabs
    };
  }
};
</script>

<style scoped>
/* ── Layout ── */
.jnl { 
  padding: 0; 
  width: 100%;
}

/* ── Header ── */
.jnl-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  background: rgba(18, 24, 38, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  margin-bottom: 1.5rem;
}

.jnl-header-left { flex: 1; min-width: 240px; }
.jnl-total-label { font-size: 0.8rem; color: #94a3b8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
.jnl-total-value { font-size: 2rem; font-weight: 700; color: #00f2fe; line-height: 1.2; margin: 0.25rem 0; font-family: 'Outfit', sans-serif; }
.jnl-total-value.jnl-negative { color: #f43f5e; }

.jnl-meta { display: flex; gap: 0.75rem; flex-wrap: wrap; font-size: 0.78rem; color: #64748b; margin-top: 0.25rem; align-items: center; }
.jnl-meta-item { display: inline-flex; align-items: center; gap: 4px; }
.jnl-meta-warn { color: #f59e0b; }

.jnl-meta-gold-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-radius: 6px;
  color: #fbbf24;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  user-select: none;
}
.jnl-meta-gold-btn:hover {
  background: rgba(245, 158, 11, 0.22);
  border-color: #fbbf24;
  color: #fef08a;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2);
}

.jnl-custom-gold-tag {
  font-size: 0.72rem;
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.4);
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 600;
  margin-left: 2px;
}

.jnl-modal--gold {
  max-width: 480px;
}

.jnl-gold-market-box {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 0.75rem 1rem;
}
.jnl-gold-market-title {
  font-size: 0.8rem;
  color: #94a3b8;
  font-weight: 600;
}
.jnl-gold-market-time {
  font-size: 0.75rem;
  color: #64748b;
}
.jnl-gold-market-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.jnl-gold-market-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #cbd5e1;
  font-size: 0.76rem;
  cursor: pointer;
  transition: all 0.15s;
}
.jnl-gold-market-chip:hover {
  background: rgba(245, 158, 11, 0.2);
  border-color: rgba(245, 158, 11, 0.4);
  color: #fbbf24;
}
.jnl-gold-market-chip .chip-name {
  color: #94a3b8;
}
.jnl-gold-market-chip .chip-price {
  font-weight: 700;
  color: #f1f5f9;
}

.jnl-gold-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.jnl-gold-input {
  width: 100%;
  padding: 0.7rem 3.5rem 0.7rem 0.85rem;
  border: 1.5px solid rgba(245, 158, 11, 0.4);
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 700;
  font-family: inherit;
  color: #fbbf24;
  background: rgba(10, 13, 20, 0.9);
  outline: none;
  transition: all 0.2s;
}
.jnl-gold-input:focus {
  border-color: #fbbf24;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2);
}
.jnl-gold-currency {
  position: absolute;
  right: 12px;
  font-weight: 700;
  font-size: 0.85rem;
  color: #94a3b8;
  pointer-events: none;
}

.jnl-quick-step-btn {
  flex: 1;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.jnl-quick-step-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.2);
}

.jnl-gold-notice {
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 8px;
  padding: 0.65rem 0.85rem;
  color: #7dd3fc;
}

.jnl-btn-primary {
  padding: 0.6rem 1.2rem;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #0f172a;
  border: none;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.jnl-btn-primary:hover:not(:disabled) {
  box-shadow: 0 4px 14px rgba(245, 158, 11, 0.4);
  transform: translateY(-1px);
}
.jnl-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.jnl-btn-secondary {
  padding: 0.6rem 1rem;
  background: rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.jnl-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.14);
  color: #ffffff;
}

.jnl-add-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0.6rem 1.2rem;
  background: linear-gradient(135deg, #00f2fe, #4facfe);
  color: #0f172a;
  border: none;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.jnl-add-btn:hover { box-shadow: 0 4px 14px rgba(0, 242, 254, 0.4); transform: translateY(-1px); }

.jnl-header-actions {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
}

.jnl-refresh-price-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0.6rem 1.15rem;
  background: rgba(14, 165, 233, 0.12);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.jnl-refresh-price-btn:hover:not(:disabled) {
  background: rgba(14, 165, 233, 0.24);
  border-color: #38bdf8;
  color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 4px 18px rgba(14, 165, 233, 0.35);
}

.jnl-refresh-price-btn:active:not(:disabled) {
  transform: translateY(0);
}

.jnl-refresh-price-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  border-color: rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.04);
}

.jnl-refresh-price-btn svg {
  transition: transform 0.4s ease;
}

.jnl-refresh-price-btn:hover:not(:disabled) svg {
  transform: rotate(180deg);
}

.jnl-chart-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0.6rem 1rem;
  background: rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.jnl-chart-btn:hover {
  background: rgba(0, 242, 254, 0.12);
  border-color: rgba(0, 242, 254, 0.3);
  color: #00f2fe;
}

/* ── Loading + Empty ── */
.jnl-loading {
  text-align: center;
  padding: 4rem 1rem;
  color: #94a3b8;
}
.jnl-loading p { margin-top: 0.75rem; }
.jnl-empty {
  text-align: center;
  padding: 3.5rem 1rem;
  background: rgba(18, 24, 38, 0.75);
  border: 1px dashed rgba(255, 255, 255, 0.12);
  border-radius: 14px;
}
.jnl-empty-icon { font-size: 3rem; margin-bottom: 0.75rem; }
.jnl-empty h5 { color: #ffffff; font-weight: 700; }
.jnl-empty p { color: #94a3b8; margin-bottom: 1rem; }

/* ── Filter Bar ── */
.jnl-filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.jnl-filter-pills {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.jnl-filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0.42rem 0.8rem;
  background: rgba(18, 24, 38, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 9px;
  color: #94a3b8;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.jnl-filter-pill:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.16);
  color: #ffffff;
  transform: translateY(-1px);
}

.jnl-filter-pill.is-active {
  background: rgba(0, 242, 254, 0.14);
  border-color: rgba(0, 242, 254, 0.45);
  color: #00f2fe;
  box-shadow: 0 0 12px rgba(0, 242, 254, 0.2);
}

.jnl-filter-pill-count {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 0.7rem;
  font-weight: 700;
  color: #cbd5e1;
}

.jnl-filter-pill.is-active .jnl-filter-pill-count {
  background: rgba(0, 242, 254, 0.25);
  color: #00f2fe;
}

.jnl-filter-pill--warning {
  border-color: rgba(239, 68, 68, 0.4);
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.1);
}

.jnl-filter-pill--warning:hover {
  border-color: rgba(239, 68, 68, 0.7);
  background: rgba(239, 68, 68, 0.18);
  color: #ffffff;
}

.jnl-filter-pill--warning.is-active {
  background: rgba(239, 68, 68, 0.22);
  border-color: #ef4444;
  color: #ff4b72;
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.35);
}

.jnl-filter-pill--warning .jnl-filter-pill-count {
  background: rgba(239, 68, 68, 0.3);
  color: #ff4b72;
}

/* ── Search Input ── */
.jnl-search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 220px;
  max-width: 300px;
  flex: 1;
}

.jnl-search-icon {
  position: absolute;
  left: 10px;
  color: #64748b;
  pointer-events: none;
}

.jnl-search-input {
  width: 100%;
  padding: 0.42rem 2rem 0.42rem 2.1rem;
  background: rgba(18, 24, 38, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 9px;
  color: #e2e8f0;
  font-size: 0.8rem;
  outline: none;
  transition: all 0.2s ease;
}

.jnl-search-input:focus {
  border-color: rgba(0, 242, 254, 0.45);
  background: rgba(18, 24, 38, 0.95);
  box-shadow: 0 0 10px rgba(0, 242, 254, 0.15);
}

.jnl-search-input::placeholder {
  color: #64748b;
}

.jnl-search-clear {
  position: absolute;
  right: 8px;
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 0.75rem;
  cursor: pointer;
  padding: 2px 5px;
  border-radius: 4px;
}

.jnl-search-clear:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

/* ── Filter Empty State ── */
.jnl-filter-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: #94a3b8;
}

.jnl-filter-empty-icon {
  font-size: 2.2rem;
  margin-bottom: 0.5rem;
  opacity: 0.7;
}

.jnl-filter-empty h6 {
  color: #e2e8f0;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.jnl-filter-empty p {
  color: #64748b;
  font-size: 0.82rem;
  margin-bottom: 0.85rem;
}

.jnl-filter-reset-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0.4rem 0.85rem;
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.35);
  border-radius: 8px;
  color: #00f2fe;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.jnl-filter-reset-btn:hover {
  background: rgba(0, 242, 254, 0.22);
  border-color: #00f2fe;
}

/* ── Table ── */
.jnl-table-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  background: rgba(18, 24, 38, 0.75);
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
  margin-bottom: 1.5rem;
  backdrop-filter: blur(16px);
}
.jnl-table-wrap::-webkit-scrollbar {
  height: 6px;
}
.jnl-table-wrap::-webkit-scrollbar-track {
  background: rgba(10, 13, 20, 0.6);
  border-radius: 4px;
}
.jnl-table-wrap::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}
.jnl-table-wrap::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 242, 254, 0.4);
}
.jnl-table {
  width: 100%;
  min-width: 960px;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.jnl-table thead {
  background: #0f1523;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  z-index: 5;
}
.jnl-table th {
  padding: 0.75rem 0.85rem;
  font-weight: 700;
  color: #94a3b8;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  background: #0f1523;
}
.jnl-sort-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  text-transform: inherit;
  letter-spacing: inherit;
  cursor: pointer;
}
.jnl-sort-btn--right {
  justify-content: flex-end;
}
.jnl-sort-indicator {
  color: #64748b;
  font-size: 0.72rem;
  line-height: 1;
  transition: color 0.15s ease;
}
.jnl-sort-indicator.is-active,
.jnl-sort-btn:hover .jnl-sort-indicator {
  color: #00f2fe;
}
.jnl-table td {
  padding: 0.75rem 0.85rem;
  vertical-align: middle;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: #e2e8f0;
}
.jnl-table tbody tr:hover { background: rgba(0, 242, 254, 0.04); }
.jnl-table .text-end { text-align: right; }
.jnl-table .text-center { text-align: center; }
.jnl-table .fw-600 { font-weight: 600; }

.jnl-row-debt { background: rgba(255, 75, 114, 0.06) !important; }
.jnl-row-debt:hover { background: rgba(255, 75, 114, 0.1) !important; }

/* ── High Loss Warning (<= -5%) ── */
.jnl-row-loss-warning {
  background: rgba(239, 68, 68, 0.09) !important;
  box-shadow: inset 4px 0 0 #ef4444, inset 0 1px 0 rgba(239, 68, 68, 0.4), inset 0 -1px 0 rgba(239, 68, 68, 0.4) !important;
}

.jnl-row-loss-warning:hover {
  background: rgba(239, 68, 68, 0.16) !important;
}

.jnl-row-loss-warning td {
  border-bottom: 1px solid rgba(239, 68, 68, 0.28) !important;
}

.jnl-symbol-header-row {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
}

.jnl-loss-warning-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-top: 4px;
  padding: 3px 8px;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.65);
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #fca5a5;
  line-height: 1.35;
  white-space: normal;
  max-width: 320px;
  animation: pulse-loss-border 2.5s infinite ease-in-out;
}

.jnl-loss-warning-tag svg {
  flex-shrink: 0;
  color: #ef4444;
}

.jnl-change--high-loss {
  background: rgba(239, 68, 68, 0.25) !important;
  color: #ff4b72 !important;
  border: 1px solid #ef4444 !important;
  font-weight: 700 !important;
  animation: pulse-loss 2s infinite ease-in-out;
}

@keyframes pulse-loss {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
  }
  50% {
    box-shadow: 0 0 8px 2px rgba(239, 68, 68, 0.5);
  }
}

@keyframes pulse-loss-border {
  0%, 100% {
    border-color: rgba(239, 68, 68, 0.65);
  }
  50% {
    border-color: rgba(239, 68, 68, 1);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.35);
  }
}

.jnl-cell-date {
  font-size: 0.78rem;
  color: #94a3b8;
  white-space: nowrap;
}
.jnl-cell-symbol {
  font-weight: 700;
  color: #ffffff;
  white-space: nowrap;
}
.jnl-cell-usd {
  cursor: help;
  transition: opacity 0.15s ease;
}
.jnl-cell-usd:hover {
  text-decoration: underline dotted rgba(56, 189, 248, 0.7);
  text-underline-offset: 3px;
}
.jnl-cell-symbol--clickable {
  cursor: pointer;
  transition: all 0.18s ease;
}
.jnl-cell-symbol--clickable:hover {
  color: #00f2fe;
}
.jnl-cell-symbol--clickable:hover .jnl-symbol-text {
  text-decoration: underline;
  text-underline-offset: 3px;
  text-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
}
.jnl-cell-symbol--clickable:hover .jnl-symbol-chart-icon {
  opacity: 1;
  color: #00f2fe;
  transform: scale(1.15);
}
.jnl-symbol-chart-icon {
  margin-left: 5px;
  opacity: 0.45;
  color: #94a3b8;
  vertical-align: middle;
  transition: all 0.18s ease;
}
.jnl-currency-tag {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 4px;
  margin-left: 5px;
  background: rgba(0, 242, 254, 0.15);
  color: #00f2fe;
  vertical-align: middle;
}
.jnl-currency-tag--usd {
  background: rgba(0, 245, 160, 0.15);
  color: #00f5a0;
}
.jnl-cell-notes {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #94a3b8;
  font-size: 0.8rem;
}
.jnl-muted { color: #64748b; }
.jnl-negative { color: #ff4b72 !important; font-weight: 600; }

/* ── Note Info Icon + Tooltip ── */
.jnl-note-icon {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s;
}
.jnl-note-icon:hover {
  color: #00f2fe;
  background: rgba(0, 242, 254, 0.12);
}
.jnl-note-tooltip {
  display: none;
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: #111726;
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #f1f5f9;
  font-size: 0.78rem;
  font-weight: 500;
  line-height: 1.45;
  padding: 8px 12px;
  border-radius: 8px;
  white-space: normal;
  word-break: break-word;
  min-width: 160px;
  max-width: 280px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
  z-index: 100;
  text-align: left;
}
.jnl-note-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: #111726;
}
.jnl-note-icon:hover .jnl-note-tooltip {
  display: block;
  animation: jnlTooltipIn 0.15s ease;
}
@keyframes jnlTooltipIn {
  from { opacity: 0; transform: translateX(-50%) translateY(4px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}

/* ── Badge ── */
.jnl-badge {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  white-space: nowrap;
}
.jnl-badge--stock { background: rgba(0, 245, 160, 0.15); color: #00f5a0; border: 1px solid rgba(0, 245, 160, 0.3); }
.jnl-badge--crypto { background: rgba(0, 242, 254, 0.15); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.3); }
.jnl-badge--gold { background: rgba(246, 211, 101, 0.15); color: #f6d365; border: 1px solid rgba(246, 211, 101, 0.3); }
.jnl-badge--silver { background: rgba(203, 213, 225, 0.15); color: #cbd5e1; border: 1px solid rgba(203, 213, 225, 0.3); }
.jnl-badge--cash { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }
.jnl-badge--real_estate { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
.jnl-badge--debt { background: rgba(255, 75, 114, 0.15); color: #ff4b72; border: 1px solid rgba(255, 75, 114, 0.3); }
.jnl-badge--other { background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); }

/* ── % Change ── */
.jnl-change {
  font-weight: 700;
  font-size: 0.82rem;
  padding: 2px 6px;
  border-radius: 4px;
}
.jnl-change--up { color: #00f5a0; background: rgba(0, 245, 160, 0.12); }
.jnl-change--down { color: #ff4b72; background: rgba(255, 75, 114, 0.12); }

/* ── Action buttons ── */
.jnl-cell-actions { white-space: nowrap; }
.jnl-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 7px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s;
  margin: 0 2px;
}
.jnl-icon-btn:hover { border-color: rgba(0, 242, 254, 0.3); color: #00f2fe; }
.jnl-icon-btn--edit:hover { color: #00f2fe; border-color: rgba(0, 242, 254, 0.3); background: rgba(0, 242, 254, 0.12); }
.jnl-icon-btn--del:hover { color: #ff4b72; border-color: rgba(255, 75, 114, 0.3); background: rgba(255, 75, 114, 0.12); }

/* ── AI Section ── */
.jnl-ai {
  background: rgba(18, 24, 38, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 1.5rem;
  margin-top: 1.5rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(16px);
}
.jnl-ai--initial {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem 2rem;
  background: rgba(10, 13, 20, 0.6);
  border: 1px dashed rgba(255, 255, 255, 0.15);
}
.jnl-ai--initial .jnl-ai-header {
  justify-content: center;
  margin-bottom: 1.25rem;
  flex-direction: column;
  gap: 12px;
}
.jnl-ai--initial .jnl-ai-header svg {
  width: 32px;
  height: 32px;
}
.jnl-ai--initial .jnl-ai-header h4 {
  font-size: 1.2rem;
  letter-spacing: -0.01em;
  color: #ffffff;
}
.jnl-ai--initial .jnl-ai-btn {
  padding: 0.65rem 1.75rem;
  font-size: 0.925rem;
  box-shadow: 0 4px 15px rgba(0, 242, 254, 0.2);
  transform: translateY(0);
}
.jnl-ai--initial .jnl-ai-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.3);
}
.jnl-ai-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 1.25rem;
}
.jnl-ai-header h4 {
  font-size: 1.05rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
}
.jnl-ai-textarea {
  width: 100%;
  max-width: 900px;
  margin: 0 auto 0.75rem auto;
  display: block;
  border: 1.5px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 0.75rem;
  font-size: 0.9rem;
  font-family: inherit;
  resize: vertical;
  background: rgba(10, 13, 20, 0.8);
  color: #ffffff;
  outline: none;
  transition: border-color 0.2s;
}
.jnl-ai-textarea:focus { border-color: #00f2fe; background: rgba(10, 13, 20, 0.95); }
.jnl-ai-actions {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.jnl-ai-btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: 0.2s;
  background: rgba(0, 242, 254, 0.15);
  color: #00f2fe;
}
.jnl-ai-btn:hover { background: rgba(0, 242, 254, 0.25); }
.jnl-ai-btn--go { background: #00f5a0; color: #0a0d14; font-weight: 700; }
.jnl-ai-btn--go:hover { background: #10b981; color: #ffffff; }
.jnl-ai-btn--cancel { background: rgba(255, 255, 255, 0.06); color: #94a3b8; }
.jnl-ai-btn--cancel:hover { background: rgba(255, 255, 255, 0.12); color: #ffffff; }
.jnl-ai-result {
  background: rgba(10, 13, 20, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 1rem;
  margin-top: 0.75rem;
  font-size: 0.9rem;
  color: #e2e8f0;
}

/* ── Modal ── */
.jnl-overlay {
  position: fixed;
  inset: 0;
  z-index: 1050;
  background: rgba(0,0,0,0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  backdrop-filter: blur(8px);
  animation: jnlFadeIn 0.15s ease;
}
@keyframes jnlFadeIn { from { opacity: 0; } to { opacity: 1; } }

.jnl-modal {
  background: #111726;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6);
  max-width: 480px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  color: #e2e8f0;
  animation: jnlSlideUp 0.2s ease;
}
@keyframes jnlSlideUp { from { transform: translateY(16px); opacity: 0; } to { transform: none; opacity: 1; } }

.jnl-modal--allocation {
  max-width: 560px;
}

.jnl-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.jnl-modal-header h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
}
.jnl-modal-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
  font-size: 1.1rem;
  cursor: pointer;
  transition: 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.jnl-modal-close:hover { background: rgba(255, 255, 255, 0.12); color: #ffffff; }

/* ── Form ── */
.jnl-form { padding: 1.25rem 1.5rem 1.5rem; }
.jnl-form-group { margin-bottom: 1rem; }
.jnl-form-group label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.jnl-form-group input:not([type="checkbox"]),
.jnl-form-group select,
.jnl-form-group textarea {
  width: 100%;
  padding: 0.6rem 0.85rem;
  border: 1.5px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  font-size: 0.9rem;
  font-family: inherit;
  color: #ffffff;
  background: rgba(10, 13, 20, 0.8);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.jnl-form-group input:not([type="checkbox"]):focus,
.jnl-form-group select:focus,
.jnl-form-group textarea:focus {
  border-color: #00f2fe;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15);
  background: rgba(10, 13, 20, 0.95);
}
.jnl-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}
.jnl-submit-btn {
  width: 100%;
  padding: 0.7rem;
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  color: #0a0d14;
  border: none;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: 0.2s;
  margin-top: 0.5rem;
}
.jnl-submit-btn:hover { box-shadow: 0 4px 14px rgba(0, 242, 254, 0.4); transform: translateY(-1px); }

.jnl-allocation-body {
  padding: 1.1rem 1.5rem 1.5rem;
}

.jnl-allocation-empty {
  text-align: center;
  color: #94a3b8;
  padding: 1.25rem 0;
}

.jnl-pie-wrap {
  display: flex;
  justify-content: center;
  margin: 0.5rem 0 1rem;
}

.jnl-pie-chart {
  width: 220px;
  height: 220px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.jnl-pie-center {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: #111726;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.4);
  color: #ffffff;
}

.jnl-pie-center strong {
  font-size: 1.3rem;
  line-height: 1;
}

.jnl-pie-center span {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.2rem;
}

.jnl-allocation-summary-card {
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}
.summary-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.summary-label {
  font-size: 0.72rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  font-weight: 500;
}
.summary-val {
  font-size: 0.95rem;
  font-weight: 700;
  color: #ffffff;
  font-family: 'Outfit', sans-serif;
}
.summary-val--cyan {
  color: #00f2fe;
}
.text-change--up {
  color: #00f5a0;
}
.text-change--down {
  color: #ff4b72;
}
.summary-divider {
  width: 1px;
  height: 28px;
  background: rgba(255, 255, 255, 0.1);
}

.jnl-allocation-total {
  text-align: center;
  font-size: 0.88rem;
  color: #ffffff;
  font-weight: 600;
  margin-bottom: 0.9rem;
}

.jnl-allocation-list {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  overflow: hidden;
}

.jnl-allocation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.8rem;
  padding: 0.7rem 0.9rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  font-size: 0.84rem;
  transition: background 0.15s;
}
.jnl-allocation-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.jnl-allocation-item:last-child {
  border-bottom: none;
}

.jnl-allocation-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.jnl-allocation-label {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-weight: 600;
  color: #ffffff;
  font-size: 0.88rem;
}

.jnl-allocation-icon {
  font-size: 0.95rem;
}

.jnl-allocation-sub {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.74rem;
  color: #64748b;
  margin-left: 17px;
}

.jnl-allocation-pct {
  color: #94a3b8;
  font-weight: 600;
}

.jnl-allocation-cost {
  color: #64748b;
}

.jnl-allocation-sep {
  opacity: 0.4;
}

.jnl-allocation-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.jnl-allocation-metrics {
  display: flex;
  align-items: center;
  gap: 8px;
  text-align: right;
}

.jnl-allocation-cur-val {
  font-weight: 700;
  color: #ffffff;
  font-size: 0.88rem;
  font-family: 'Outfit', sans-serif;
}

.jnl-growth-pill {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  line-height: 1.2;
}
.growth-pill--up {
  background: rgba(0, 245, 160, 0.12);
  color: #00f5a0;
  border: 1px solid rgba(0, 245, 160, 0.3);
}
.growth-pill--down {
  background: rgba(255, 75, 114, 0.12);
  color: #ff4b72;
  border: 1px solid rgba(255, 75, 114, 0.3);
}
.growth-pill--zero {
  background: rgba(148, 163, 184, 0.12);
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.25);
}
.growth-pill--neutral {
  background: rgba(255, 255, 255, 0.05);
  color: #64748b;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .jnl-header { flex-direction: column; }
  .jnl-header-actions { width: 100%; justify-content: stretch; }
  .jnl-refresh-price-btn, .jnl-chart-btn, .jnl-add-btn { width: 100%; justify-content: center; }
  .jnl-total-value { font-size: 1.35rem; }
  .jnl-form-row { grid-template-columns: 1fr; }
  .jnl-table { font-size: 0.78rem; }
  .jnl-table th, .jnl-table td { padding: 0.5rem 0.5rem; }
  .jnl-allocation-item {
    flex-direction: column;
    align-items: flex-start;
  }
  .jnl-allocation-value {
    text-align: left;
  }
}

/* AI Content Premium Styles */
.jnl-ai-content {
  color: #e2e8f0;
  line-height: 1.65;
  font-size: 0.925rem;
}

/* Beautiful custom headers with left borders */
.jnl-ai-content :deep(.ai-header-h3) {
  font-size: 1.2rem;
  color: #ffffff;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  padding-left: 0.75rem;
  border-left: 4px solid #00f2fe;
  letter-spacing: -0.02em;
}

.jnl-ai-content :deep(.ai-header-h4) {
  font-size: 1.1rem;
  color: #ffffff;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  padding-left: 0.5rem;
  border-left: 3px solid #00f5a0;
}

.jnl-ai-content :deep(.ai-header-h5) {
  font-size: 1.0rem;
  color: #f1f5f9;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  padding-left: 0.5rem;
  border-left: 3px solid #f6d365;
}

.jnl-ai-content :deep(.ai-header-h6) {
  font-size: 0.95rem;
  color: #cbd5e1;
  font-weight: 600;
  margin-top: 0.85rem;
  margin-bottom: 0.4rem;
  padding-left: 0.4rem;
  border-left: 2.5px solid #a78bfa;
}

/* Dynamic thin-gradient divider */
.jnl-ai-content :deep(.ai-hr) {
  border: 0;
  height: 1px;
  background: linear-gradient(to right, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0));
  margin: 1.5rem 0;
}

/* Lists styling using modern emerald dots */
.jnl-ai-content :deep(.ai-list-item) {
  list-style: none;
  position: relative;
  padding-left: 1.25rem;
  margin-bottom: 0.5rem;
  color: #e2e8f0;
}

.jnl-ai-content :deep(.ai-list-item::before) {
  content: '';
  position: absolute;
  left: 0.25rem;
  top: 0.55rem;
  width: 6px;
  height: 6px;
  background-color: #00f5a0;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(0, 245, 160, 0.6);
}

/* Premium styled Table */
.jnl-ai-content :deep(.table-responsive) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  margin-top: 1rem;
  margin-bottom: 1rem;
}

.jnl-ai-content :deep(.custom-ai-table) {
  width: 100%;
  margin-bottom: 0;
  border-collapse: collapse;
  font-size: 0.85rem;
  background-color: rgba(18, 24, 38, 0.75);
}

.jnl-ai-content :deep(.custom-ai-table th) {
  background: rgba(10, 13, 20, 0.9) !important;
  color: #ffffff !important;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  padding: 10px 14px;
  border: none;
  text-align: left;
}

.jnl-ai-content :deep(.custom-ai-table td) {
  padding: 10px 14px;
  color: #cbd5e1;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  transition: background-color 0.2s ease;
  text-align: left;
}

.jnl-ai-content :deep(.custom-ai-table tr:last-child td) {
  border-bottom: none;
}

.jnl-ai-content :deep(.custom-ai-table tr:nth-child(even) td) {
  background-color: rgba(255, 255, 255, 0.02);
}

.jnl-ai-content :deep(.custom-ai-table tr:hover td) {
  background-color: rgba(0, 242, 254, 0.06) !important;
  color: #ffffff;
}

/* Inline code and blocks styling */
.jnl-ai-content :deep(.custom-code-inline) {
  background-color: rgba(255, 75, 114, 0.15) !important;
  color: #ff4b72 !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
  font-family: SFMono-Regular, Consolas, monospace !important;
  font-size: 0.85em !important;
}

.jnl-ai-content :deep(.custom-code-block) {
  background-color: #0a0d14 !important;
  color: #e2e8f0 !important;
  padding: 14px 18px !important;
  border-radius: 10px !important;
  font-family: SFMono-Regular, Consolas, monospace !important;
  font-size: 0.85rem !important;
  margin: 1rem 0 !important;
  overflow-x: auto !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.5);
}

.jnl-ai-content :deep(strong) {
  color: #ffffff;
  font-weight: 600;
}

/* ── Chart Popup Modal ── */
.modal-backdrop-chart {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(4, 7, 15, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 16px;
  animation: jnlFadeIn 0.2s ease;
}

.jnl-modal-chart {
  max-width: 1040px;
  width: 96vw;
  background: #0f1523;
  border: 1px solid rgba(0, 242, 254, 0.25);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(0, 242, 254, 0.12);
  animation: jnlScaleUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
}

@keyframes jnlScaleUp {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

@keyframes jnlFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.chart-modal-head {
  padding: 14px 20px;
  background: rgba(15, 21, 35, 0.95);
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
  font-size: 1.25rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.chart-sub {
  font-size: 0.78rem;
  color: #94a3b8;
  font-weight: 500;
}

.chart-modal-header-actions {
  display: flex;
  align-items: center;
  gap: 14px;
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
  padding: 5px 12px;
  border-radius: 7px;
  font-size: 0.78rem;
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
  font-size: 0.8rem;
  font-weight: 600;
  outline: none;
  width: 100%;
  text-transform: uppercase;
}

.chart-search-clear-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #94a3b8;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  font-size: 10px;
  margin-right: 4px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.chart-search-clear-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.btn-search-apply {
  background: rgba(0, 242, 254, 0.15);
  border: 1px solid rgba(0, 242, 254, 0.3);
  color: #00f2fe;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.72rem;
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
  font-size: 0.72rem;
  color: #64748b;
  font-weight: 600;
}

.quick-chip {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.72rem;
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
