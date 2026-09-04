<template>
  <div class="take-notes-card mb-2 mb-md-3" :class="{ 'is-collapsed': isCollapsed }">
    <!-- Compact Strip Mode (Default: 1 row, non-intrusive) -->
    <div v-if="isCollapsed" class="notes-mini-strip d-flex align-items-center justify-content-between gap-2">
      <!-- Left: Badge + Preview notes (Single row text-truncate) -->
      <div 
        class="d-flex align-items-center gap-2 flex-grow-1 text-truncate" 
        style="cursor: pointer; min-width: 0;" 
        @click="toggleCollapse" 
        title="Bấm để mở rộng bảng ghi chú"
      >
        <div class="notes-badge-mini">
          <i class="fa-solid fa-note-sticky text-warning"></i>
          <span>Take Notes</span>
          <span class="notes-count-badge-mini">
            {{ notesList.length }}
          </span>
        </div>

        <!-- Preview Text / Latest Note -->
        <span v-if="notesList.length > 0" class="note-preview-text text-truncate fw-semibold" style="font-size: 0.86rem;">
          <span>{{ notesList[0].text }}</span>
        </span>
        <span v-else class="text-muted small italic text-truncate" style="font-size: 0.84rem;">
          Chưa có ghi chú nào. Bấm mở rộng để thêm ghi chú chiến lược mới...
        </span>

        <span v-if="notesList.length > 1" class="text-muted small flex-shrink-0 d-none d-xl-inline" style="font-size: 0.75rem;">
          (+{{ notesList.length - 1 }} ghi chú khác)
        </span>
      </div>

      <!-- Right: Quick actions (Always stays on single row) -->
      <div class="d-flex align-items-center gap-2 flex-shrink-0">
        <button 
          v-if="isLoggedIn" 
          class="btn-note-action d-none d-md-inline-flex align-items-center gap-1"
          @click.stop="openAddMode"
          title="Thêm ghi chú mới"
        >
          <i class="fa-solid fa-plus"></i>
          <span>Thêm nhanh</span>
        </button>

        <button 
          class="btn-collapse-toggle d-inline-flex align-items-center gap-1" 
          @click="toggleCollapse"
          title="Mở rộng / Thu gọn bảng ghi chú"
        >
          <i class="fa-solid fa-chevron-down"></i>
          <span>Mở rộng</span>
        </button>
      </div>
    </div>

    <!-- Expanded View -->
    <div v-else class="notes-expanded-wrap">
      <!-- Header -->
      <div class="notes-header d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
        <div class="d-flex align-items-center gap-2 flex-wrap">
          <div class="notes-badge d-inline-flex align-items-center gap-2">
            <i class="fa-solid fa-note-sticky text-warning fs-6"></i>
            <span class="fw-bold text-light">Take Notes & Nhắc Nhở Giao Dịch</span>
            <span class="notes-count-badge">
              {{ notesList.length }} mục
            </span>
          </div>
          <span v-if="!isLoggedIn" class="badge bg-danger bg-opacity-10 text-danger border border-danger border-opacity-20 px-2 py-1 rounded" style="font-size: 0.75rem;">
            <i class="fa-solid fa-lock me-1"></i>Chế độ xem (Đăng nhập để thêm/sửa)
          </span>
          <span v-else class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-20 px-2 py-1 rounded" style="font-size: 0.75rem;">
            <i class="fa-solid fa-pen-to-square me-1"></i>Đã đăng nhập - Tự động lưu
          </span>
        </div>

        <div class="d-flex align-items-center gap-2">
          <button 
            class="btn-note-toggle-close" 
            @click="toggleCollapse"
            title="Thu gọn bảng ghi chú"
          >
            <i class="fa-solid fa-chevron-up me-1"></i>
            <span>Thu gọn</span>
          </button>
        </div>
      </div>

      <!-- Add New Note Input Form (Only for logged-in users) -->
      <div class="note-input-container mb-3 p-2.5 rounded-3">
        <div v-if="isLoggedIn" class="d-flex flex-column flex-sm-row gap-2">
          <div class="position-relative flex-grow-1">
            <input 
              ref="newNoteInputRef"
              type="text" 
              class="form-control note-text-input" 
              v-model="newNoteText" 
              placeholder="Nhập ghi chú chiến lược, quản trị vốn, kỷ luật giao dịch... (Enter để lưu)"
              @keydown.enter="addNewNote"
            />
            <span v-if="newNoteText" class="clear-input-btn" @click="newNoteText = ''">
              <i class="fa-solid fa-xmark"></i>
            </span>
          </div>
          <button 
            class="btn-note-submit d-inline-flex align-items-center justify-content-center gap-1.5"
            :disabled="!newNoteText.trim()"
            @click="addNewNote"
          >
            <i class="fa-solid fa-floppy-disk"></i>
            <span>Lưu Ghi Chú</span>
          </button>
        </div>
        <div v-else class="d-flex align-items-center justify-content-between flex-wrap gap-2 p-1">
          <span class="text-muted small" style="color: #94a3b8 !important;">
            <i class="fa-solid fa-circle-info me-1.5 text-warning"></i>
            Bạn đang ở chế độ xem. Hãy đăng nhập để thêm mới, chỉnh sửa hoặc xóa các ghi chú cá nhân.
          </span>
          <button class="btn-note-login-prompt" @click="openLoginModal('Đăng nhập tài khoản để thêm và quản lý Take Notes cá nhân!')">
            <i class="fa-solid fa-right-to-bracket me-1"></i>Đăng nhập ngay
          </button>
        </div>
      </div>

      <!-- Notes List -->
      <div v-if="notesList.length > 0" class="notes-list-wrapper">
        <div class="notes-grid">
          <div 
            v-for="(item, index) in notesList" 
            :key="item.id || index"
            class="note-item-card"
            :class="{ 'is-editing': editingId === item.id }"
          >
            <!-- Normal Mode -->
            <template v-if="editingId !== item.id">
              <div class="d-flex align-items-start justify-content-between gap-2">
                <div class="d-flex align-items-start gap-2 flex-grow-1 min-w-0">
                  <span class="note-bullet text-warning mt-1">
                    <i class="fa-solid fa-circle-dot" style="font-size: 0.55rem;"></i>
                  </span>
                  <div class="note-content-area flex-grow-1">
                    <p class="note-text-body mb-1">{{ item.text }}</p>
                    <div class="d-flex align-items-center gap-2 flex-wrap">
                      <span class="note-timestamp">
                        <i class="fa-regular fa-clock me-1"></i>{{ formatDate(item.updated_at || item.created_at) }}
                      </span>
                      <span v-if="item.edited" class="note-edited-tag">
                        (Đã chỉnh sửa)
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Action buttons -->
                <div class="note-actions d-inline-flex align-items-center gap-1">
                  <!-- Copy button -->
                  <button 
                    class="btn-note-icon" 
                    @click="copyNoteText(item.text, item.id)" 
                    :title="copiedId === item.id ? 'Đã sao chép!' : 'Sao chép ghi chú'"
                  >
                    <i :class="copiedId === item.id ? 'fa-solid fa-check text-success' : 'fa-regular fa-copy'"></i>
                  </button>

                  <!-- Edit button (Logged in) -->
                  <button 
                    class="btn-note-icon" 
                    @click="startEdit(item)" 
                    title="Chỉnh sửa ghi chú"
                  >
                    <i class="fa-solid fa-pen-to-square"></i>
                  </button>

                  <!-- Delete button (Logged in) -->
                  <button 
                    class="btn-note-icon btn-note-icon-delete" 
                    @click="deleteNote(item.id)" 
                    title="Xóa ghi chú này"
                  >
                    <i class="fa-regular fa-trash-can"></i>
                  </button>
                </div>
              </div>
            </template>

            <!-- Inline Edit Mode -->
            <template v-else>
              <div class="edit-note-form">
                <textarea 
                  ref="editInputRef"
                  v-model="editingText" 
                  class="form-control note-edit-textarea mb-2" 
                  rows="2"
                  placeholder="Nhập nội dung chỉnh sửa..."
                  @keydown.enter.exact.prevent="saveEdit(item.id)"
                  @keydown.esc="cancelEdit"
                ></textarea>
                <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
                  <span class="text-muted small" style="font-size: 0.75rem;">
                    Nhấn <b>Enter</b> để lưu, <b>Esc</b> để hủy
                  </span>
                  <div class="d-flex align-items-center gap-1.5">
                    <button class="btn-edit-cancel" @click="cancelEdit">
                      <i class="fa-solid fa-xmark me-1"></i>Hủy
                    </button>
                    <button class="btn-edit-save" :disabled="!editingText.trim()" @click="saveEdit(item.id)">
                      <i class="fa-solid fa-check me-1"></i>Lưu thay đổi
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-notes-box text-center py-4 rounded-3">
        <i class="fa-regular fa-clipboard fs-3 text-muted mb-2 d-block"></i>
        <p class="text-light fw-semibold mb-1" style="font-size: 0.92rem;">Chưa có ghi chú nào được lưu</p>
        <p class="text-muted small mb-0" style="color: #94a3b8 !important; font-size: 0.8rem;">
          {{ isLoggedIn ? 'Nhập nội dung ở ô phía trên và nhấn "Lưu Ghi Chú" để bắt đầu ghi nhớ.' : 'Đăng nhập để thêm ghi chú theo dõi thị trường.' }}
        </p>
      </div>
    </div>

    <!-- Login Required Modal -->
    <transition name="fade">
      <div v-if="showLoginModal" class="podcast-login-modal-backdrop" @click="closeLoginModal">
        <div class="podcast-login-modal-card" @click.stop>
          <div class="modal-header-custom d-flex align-items-center justify-content-between mb-3">
            <div class="d-flex align-items-center gap-2">
              <div class="modal-icon-badge text-warning bg-warning bg-opacity-10 p-2 rounded-circle">
                <i class="fa-solid fa-user-lock"></i>
              </div>
              <h5 class="m-0 text-light fw-bold" style="font-size: 1.05rem;">{{ loginModalTitle }}</h5>
            </div>
            <button class="modal-close-btn" @click="closeLoginModal" title="Đóng modal">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <div class="modal-content-body mb-4">
            <p class="text-light fw-semibold mb-2" style="font-size: 0.96rem; line-height: 1.55;">
              {{ loginModalMessage }}
            </p>
            <p class="text-muted small m-0" style="color: #94a3b8 !important; font-size: 0.82rem; line-height: 1.5;">
              Đăng nhập tài khoản để đồng bộ ghi chú, lưu trữ chiến lược giao dịch và sử dụng đầy đủ các tính năng độc quyền.
            </p>
          </div>

          <div class="d-flex align-items-center justify-content-end gap-2 pt-3 border-top" style="border-color: rgba(255, 255, 255, 0.08) !important;">
            <button class="btn-modal-dismiss" @click="closeLoginModal">
              <i class="fa-solid fa-xmark me-1"></i>Thoát
            </button>
            <button class="btn-modal-confirm" @click="proceedToLogin">
              <i class="fa-solid fa-right-to-bracket me-1"></i>Đăng nhập ngay
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// State
const isCollapsed = ref(true);
const notesList = ref([]);
const newNoteText = ref('');
const newNoteInputRef = ref(null);
const isSyncing = ref(false);

const editingId = ref(null);
const editingText = ref('');
const editInputRef = ref(null);

const copiedId = ref(null);

// Modal state
const showLoginModal = ref(false);
const loginModalTitle = ref('Yêu cầu Đăng nhập');
const loginModalMessage = ref('');

// Auth state
const isLoggedIn = computed(() => {
  return !!localStorage.getItem('token');
});

const getUserInfo = () => {
  const userInfoStr = localStorage.getItem('userInfo');
  if (!userInfoStr) return null;
  try {
    return JSON.parse(userInfoStr);
  } catch (e) {
    return null;
  }
};

const getUserId = () => {
  const info = getUserInfo();
  if (!info) return '';
  return info.id || info.custodyCode || info.username || info.email || '';
};

const getHeaders = () => {
  const token = localStorage.getItem('token');
  const userId = getUserId();
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(userId ? { 'X-User-ID': String(userId) } : {})
  };
};

// Storage Key Helper
const getStorageKey = () => {
  const userId = getUserId();
  return userId ? `take_notes_cache_${userId}` : 'trading_take_notes_v1';
};

// Default initial items if completely new
const DEFAULT_NOTES = [
  {
    id: 'note-1',
    text: 'Duy trì kỷ luật: Không rượt đuổi giá khi đã vượt quá 3% từ điểm Pivot Breakout.',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'note-2',
    text: 'Theo dõi chỉ số DXY & Lợi suất trái phiếu US10Y trước mỗi phiên mở cửa Mỹ (20:30 VN).',
    created_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString()
  }
];

// Load notes from Cache / Storage
const loadLocalCache = () => {
  try {
    const raw = localStorage.getItem(getStorageKey());
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        notesList.value = parsed;
        return true;
      }
    }
  } catch (err) {
    console.error('Error reading take notes cache:', err);
  }
  return false;
};

// Save notes to localStorage & broadcast
const saveNotesToCache = () => {
  try {
    const key = getStorageKey();
    localStorage.setItem(key, JSON.stringify(notesList.value));
    localStorage.setItem('trading_take_notes_v1', JSON.stringify(notesList.value));
    window.dispatchEvent(new CustomEvent('take-notes-updated', { detail: notesList.value }));
  } catch (err) {
    console.error('Error caching take notes:', err);
  }
};

// Fetch notes from Database (Go API)
const fetchNotesFromDB = async () => {
  const userId = getUserId();
  if (!userId) return;

  isSyncing.value = true;
  try {
    const res = await fetch(`/api/take-notes?user_id=${encodeURIComponent(userId)}`, {
      headers: getHeaders(),
      signal: AbortSignal.timeout(8000)
    });

    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data)) {
        if (data.length > 0) {
          notesList.value = data;
          saveNotesToCache();
        } else if (notesList.value.length === 0) {
          notesList.value = [];
          saveNotesToCache();
        }
      }
    }
  } catch (err) {
    console.warn('Could not sync take notes with DB, using local cache:', err);
  } finally {
    isSyncing.value = false;
  }
};

// Main Load Function
const loadNotes = () => {
  const hasCache = loadLocalCache();
  if (!hasCache && !isLoggedIn.value) {
    notesList.value = [...DEFAULT_NOTES];
    saveNotesToCache();
  }

  if (isLoggedIn.value) {
    fetchNotesFromDB();
  }
};

// Toggle collapse
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value;
};

const openAddMode = () => {
  isCollapsed.value = false;
  nextTick(() => {
    newNoteInputRef.value?.focus();
  });
};

// Add new note (DB + Optimistic Cache)
const addNewNote = async () => {
  if (!isLoggedIn.value) {
    openLoginModal('Vui lòng đăng nhập tài khoản để thêm ghi chú mới!');
    return;
  }

  const trimmed = newNoteText.value.trim();
  if (!trimmed) return;

  const tempId = 'temp-' + Date.now();
  const newItem = {
    id: tempId,
    text: trimmed,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };

  // Optimistic UI update
  notesList.value.unshift(newItem);
  saveNotesToCache();
  newNoteText.value = '';

  // Sync with DB
  const userId = getUserId();
  if (userId) {
    try {
      const res = await fetch(`/api/take-notes?user_id=${encodeURIComponent(userId)}`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ text: trimmed }),
        signal: AbortSignal.timeout(8000)
      });
      if (res.ok) {
        const createdNote = await res.json();
        if (createdNote && createdNote.id) {
          const idx = notesList.value.findIndex(n => n.id === tempId);
          if (idx !== -1) {
            notesList.value[idx] = createdNote;
            saveNotesToCache();
          }
        }
      }
    } catch (err) {
      console.warn('Failed to save note to DB, preserved in local cache:', err);
    }
  }
};

// Start edit
const startEdit = (item) => {
  if (!isLoggedIn.value) {
    openLoginModal('Vui lòng đăng nhập tài khoản để chỉnh sửa ghi chú!');
    return;
  }
  editingId.value = item.id;
  editingText.value = item.text;
  nextTick(() => {
    editInputRef.value?.focus();
  });
};

// Cancel edit
const cancelEdit = () => {
  editingId.value = null;
  editingText.value = '';
};

// Save edit (DB + Optimistic Cache)
const saveEdit = async (id) => {
  if (!isLoggedIn.value) {
    openLoginModal('Vui lòng đăng nhập tài khoản để lưu chỉnh sửa!');
    return;
  }

  const trimmed = editingText.value.trim();
  if (!trimmed) return;

  const target = notesList.value.find(n => n.id === id);
  if (target) {
    target.text = trimmed;
    target.updated_at = new Date().toISOString();
    target.edited = true;
    saveNotesToCache();
  }

  cancelEdit();

  // Sync with DB if numeric ID
  const userId = getUserId();
  if (userId && typeof id === 'number') {
    try {
      await fetch(`/api/take-notes?user_id=${encodeURIComponent(userId)}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ id: id, text: trimmed }),
        signal: AbortSignal.timeout(8000)
      });
    } catch (err) {
      console.warn('Failed to update note in DB:', err);
    }
  }
};

// Delete note (DB + Optimistic Cache)
const deleteNote = async (id) => {
  if (!isLoggedIn.value) {
    openLoginModal('Vui lòng đăng nhập tài khoản để xóa ghi chú!');
    return;
  }

  notesList.value = notesList.value.filter(n => n.id !== id);
  saveNotesToCache();

  // Sync with DB if numeric ID
  const userId = getUserId();
  if (userId && typeof id === 'number') {
    try {
      await fetch(`/api/take-notes?user_id=${encodeURIComponent(userId)}&id=${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
        signal: AbortSignal.timeout(8000)
      });
    } catch (err) {
      console.warn('Failed to delete note from DB:', err);
    }
  }
};

// Copy note text
const copyNoteText = async (text, id) => {
  try {
    await navigator.clipboard.writeText(text);
    copiedId.value = id;
    setTimeout(() => {
      if (copiedId.value === id) {
        copiedId.value = null;
      }
    }, 2000);
  } catch (e) {
    console.warn('Copy failed:', e);
  }
};

// Format Date
const formatDate = (isoString) => {
  if (!isoString) return '';
  try {
    const d = new Date(isoString);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    
    const timeStr = d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    if (isToday) {
      return timeStr;
    }
    const dayStr = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
    return `${dayStr} ${timeStr}`;
  } catch (e) {
    return isoString;
  }
};

// Login Modal
const openLoginModal = (msg) => {
  loginModalMessage.value = msg;
  showLoginModal.value = true;
};

const closeLoginModal = () => {
  showLoginModal.value = false;
};

const proceedToLogin = () => {
  showLoginModal.value = false;
  if (router) {
    router.push('/login');
  } else {
    window.location.href = '/login';
  }
};

// Listener for cross-tab or cross-component sync
const onStorageChange = (e) => {
  const currentKey = getStorageKey();
  if ((e.key === currentKey || e.key === 'trading_take_notes_v1') && e.newValue) {
    try {
      notesList.value = JSON.parse(e.newValue);
    } catch (err) {
      console.warn('Error syncing take notes from storage:', err);
    }
  }
};

const onCustomNotesUpdate = (e) => {
  if (e.detail) {
    notesList.value = e.detail;
  }
};

onMounted(() => {
  loadNotes();
  window.addEventListener('storage', onStorageChange);
  window.addEventListener('take-notes-updated', onCustomNotesUpdate);
});

onUnmounted(() => {
  window.removeEventListener('storage', onStorageChange);
  window.removeEventListener('take-notes-updated', onCustomNotesUpdate);
});
</script>

<style scoped>
.take-notes-card {
  background: rgba(15, 23, 42, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 8px 14px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.take-notes-card:hover {
  border-color: rgba(234, 179, 8, 0.25);
}

.take-notes-card.is-collapsed {
  padding: 6px 12px;
}

/* ── Mini Strip ── */
.notes-mini-strip {
  min-height: 28px;
  flex-wrap: nowrap;
}

.notes-badge-mini {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(234, 179, 8, 0.12);
  border: 1px solid rgba(234, 179, 8, 0.35);
  color: #facc15;
  font-size: 0.74rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 14px;
  letter-spacing: 0.4px;
  flex-shrink: 0;
  white-space: nowrap;
}

.note-preview-text {
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.15s ease;
}

.note-preview-text:hover {
  color: #facc15;
}

.btn-note-action {
  background: rgba(234, 179, 8, 0.12);
  border: 1px solid rgba(234, 179, 8, 0.3);
  color: #fef08a;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 8px;
  cursor: pointer;
  flex-shrink: 0;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.btn-note-action:hover {
  background: rgba(234, 179, 8, 0.25);
  border-color: #facc15;
  color: #ffffff;
  transform: translateY(-1px);
}

.btn-collapse-toggle {
  background: rgba(234, 179, 8, 0.1);
  border: 1px solid rgba(234, 179, 8, 0.25);
  color: #facc15;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 4px 11px;
  border-radius: 8px;
  cursor: pointer;
  flex-shrink: 0;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.btn-collapse-toggle:hover {
  background: rgba(234, 179, 8, 0.2);
  border-color: rgba(234, 179, 8, 0.5);
  color: #ffffff;
  transform: translateY(-1px);
}

/* ── Expanded View ── */
.notes-expanded-wrap {
  padding: 4px 2px 2px 2px;
}

.notes-badge {
  background: rgba(234, 179, 8, 0.12);
  border: 1px solid rgba(234, 179, 8, 0.3);
  padding: 5px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
}

.notes-count-badge {
  background: #facc15 !important;
  color: #0f172a !important;
  font-weight: 800 !important;
  font-size: 0.72rem;
  line-height: 1;
  padding: 3px 8px;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.2px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
}

.notes-count-badge-mini {
  background: #facc15 !important;
  color: #0f172a !important;
  font-weight: 800 !important;
  font-size: 0.68rem;
  line-height: 1;
  padding: 2px 6px;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 4px;
}

.btn-note-toggle-close {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
  font-size: 0.76rem;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-note-toggle-close:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

/* ── Add Input ── */
.note-input-container {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.note-text-input {
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #f8fafc;
  font-size: 0.85rem;
  border-radius: 8px;
  padding: 8px 32px 8px 12px;
  transition: all 0.15s ease;
}

.note-text-input:focus {
  background: rgba(15, 23, 42, 0.95);
  border-color: #eab308;
  box-shadow: 0 0 0 2px rgba(234, 179, 8, 0.2);
  color: #ffffff;
}

.clear-input-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  cursor: pointer;
  font-size: 0.85rem;
}

.clear-input-btn:hover {
  color: #e2e8f0;
}

.btn-note-submit {
  background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
  border: none;
  color: #0f172a;
  font-weight: 700;
  font-size: 0.82rem;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
  box-shadow: 0 2px 10px rgba(234, 179, 8, 0.25);
}

.btn-note-submit:hover:not(:disabled) {
  opacity: 0.95;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(234, 179, 8, 0.4);
}

.btn-note-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-note-login-prompt {
  background: rgba(234, 179, 8, 0.15);
  border: 1px solid rgba(234, 179, 8, 0.4);
  color: #fde047;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-note-login-prompt:hover {
  background: rgba(234, 179, 8, 0.3);
  color: #ffffff;
}

/* ── Notes Grid & Card ── */
.notes-list-wrapper {
  max-height: 280px;
  overflow-y: auto;
  padding-right: 4px;
}

.notes-list-wrapper::-webkit-scrollbar {
  width: 5px;
}

.notes-list-wrapper::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}

.notes-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.note-item-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 8px 12px;
  transition: all 0.15s ease;
}

.note-item-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(234, 179, 8, 0.2);
}

.note-item-card.is-editing {
  background: rgba(0, 0, 0, 0.4);
  border-color: #eab308;
}

.note-text-body {
  color: #f1f5f9;
  font-size: 0.86rem;
  line-height: 1.5;
  word-break: break-word;
}

.note-timestamp {
  color: #64748b;
  font-size: 0.72rem;
  font-family: monospace;
}

.note-edited-tag {
  color: #ca8a04;
  font-size: 0.7rem;
  font-style: italic;
}

.btn-note-icon {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 0.8rem;
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-note-icon:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

.btn-note-icon-delete:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.12);
}

/* ── Inline Edit Form ── */
.note-edit-textarea {
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(234, 179, 8, 0.4);
  color: #f8fafc;
  font-size: 0.86rem;
  border-radius: 6px;
  resize: vertical;
}

.note-edit-textarea:focus {
  background: #0f172a;
  border-color: #facc15;
  box-shadow: 0 0 0 2px rgba(234, 179, 8, 0.25);
  color: #ffffff;
}

.btn-edit-save {
  background: #eab308;
  border: none;
  color: #0f172a;
  font-weight: 700;
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-edit-save:hover:not(:disabled) {
  background: #facc15;
}

.btn-edit-cancel {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-edit-cancel:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
}

/* ── Empty Box ── */
.empty-notes-box {
  background: rgba(0, 0, 0, 0.2);
  border: 1px dashed rgba(255, 255, 255, 0.08);
}

/* ── Login Modal ── */
.podcast-login-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 10500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.podcast-login-modal-card {
  background: #0f172a;
  border: 1px solid rgba(234, 179, 8, 0.3);
  border-radius: 14px;
  width: 100%;
  max-width: 440px;
  padding: 22px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 1.1rem;
  cursor: pointer;
}

.modal-close-btn:hover {
  color: #ffffff;
}

.btn-modal-dismiss {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  font-size: 0.84rem;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-modal-dismiss:hover {
  background: rgba(255, 255, 255, 0.14);
  color: #ffffff;
}

.btn-modal-confirm {
  background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
  border: none;
  color: #0f172a;
  font-size: 0.84rem;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-modal-confirm:hover {
  opacity: 0.95;
}
</style>
