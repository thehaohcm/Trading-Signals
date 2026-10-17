// Thông báo hệ thống của trình duyệt (Chrome / Edge / Firefox trên PC) qua Notification API.
// Hoạt động khi website đang mở (kể cả tab nền hoặc cửa sổ thu nhỏ).
// Mặc định TẮT — người dùng bật trong "Cài đặt Báo Động" (trình duyệt sẽ hỏi quyền).

const STORAGE_KEY = 'desktop_notify_enabled';
const SENT_PREFIX = 'desktop_notify_sent_';
const DEDUPE_MS = 2 * 60 * 1000;

const safeGet = (key) => {
  try { return localStorage.getItem(key); } catch (e) { return null; }
};
const safeSet = (key, val) => {
  try { localStorage.setItem(key, val); } catch (e) { /* ignore */ }
};

// Tuỳ chọn loại thông báo muốn nhận: 'alerts' (cảnh báo giao dịch) | 'news' (Breaking News Telegram).
// Dùng chung cho banner trong web, thông báo màn hình và Web Push.
// Mặc định: Cảnh báo giao dịch BẬT, Breaking News TẮT (chỉ nhận khi người dùng tự bật).
const PREF_PREFIX = 'notify_pref_';
const PREF_DEFAULTS = { alerts: true, news: false };
export const getNotifyPref = (kind) => {
  const v = safeGet(PREF_PREFIX + kind);
  if (v === 'true') return true;
  if (v === 'false') return false;
  return PREF_DEFAULTS[kind] !== undefined ? PREF_DEFAULTS[kind] : true;
};
export const setNotifyPref = (kind, enabled) => {
  safeSet(PREF_PREFIX + kind, enabled ? 'true' : 'false');
  try {
    window.dispatchEvent(new CustomEvent('notify-pref-changed', { detail: { kind, enabled } }));
  } catch (e) { /* ignore */ }
};

export const isDesktopNotifySupported = () =>
  typeof window !== 'undefined' && 'Notification' in window;

export const getDesktopNotifyPermission = () =>
  isDesktopNotifySupported() ? Notification.permission : 'unsupported';

export const isDesktopNotifyEnabled = () =>
  isDesktopNotifySupported() &&
  Notification.permission === 'granted' &&
  safeGet(STORAGE_KEY) === 'true';

// Phải gọi từ thao tác của người dùng (click/change) thì trình duyệt mới hiện hộp xin quyền.
export const enableDesktopNotify = async () => {
  if (!isDesktopNotifySupported()) return 'unsupported';
  let permission = Notification.permission;
  if (permission === 'default') {
    try {
      permission = await Notification.requestPermission();
    } catch (e) {
      // Safari cũ dùng callback
      permission = await new Promise((resolve) => Notification.requestPermission(resolve));
    }
  }
  safeSet(STORAGE_KEY, permission === 'granted' ? 'true' : 'false');
  return permission;
};

export const disableDesktopNotify = () => safeSet(STORAGE_KEY, 'false');

// Nhiều tab cùng mở website → chỉ 1 tab hiện thông báo cho cùng 1 sự kiện.
const alreadySentByAnotherTab = (tag) => {
  if (!tag) return false;
  const key = SENT_PREFIX + tag;
  const last = Number(safeGet(key) || 0);
  if (last && Date.now() - last < DEDUPE_MS) return true;
  safeSet(key, String(Date.now()));
  return false;
};

/**
 * Hiện thông báo trên màn hình.
 * @param {object} opts
 * @param {string} opts.title
 * @param {string} [opts.body]
 * @param {string} [opts.tag]                 Định danh duy nhất để chống trùng giữa các tab
 * @param {boolean} [opts.requireInteraction] Giữ thông báo cho tới khi người dùng bấm (lỗi lệnh, cắt lỗ...)
 * @param {boolean} [opts.onlyWhenHidden=true] Chỉ hiện khi người dùng không nhìn vào tab
 * @param {boolean} [opts.force=false]        Bỏ qua kiểm tra bật/tắt & ẩn tab (dùng để thử nghiệm)
 * @param {Function} [opts.onClick]
 */
export const showDesktopNotification = ({
  title,
  body = '',
  tag,
  requireInteraction = false,
  onlyWhenHidden = true,
  force = false,
  onClick,
} = {}) => {
  if (!isDesktopNotifySupported() || Notification.permission !== 'granted') return null;
  if (!force) {
    if (safeGet(STORAGE_KEY) !== 'true') return null;
    // Đã bật Web Push thì server tự gửi thông báo (kể cả khi đóng tab) → không hiện trùng từ trang
    if (safeGet('web_push_active') === 'true') return null;
    const userIsLooking = document.visibilityState === 'visible' && document.hasFocus();
    if (onlyWhenHidden && userIsLooking) return null; // đang xem trang thì đã có thẻ cảnh báo trong web
    if (alreadySentByAnotherTab(tag)) return null;
  }

  try {
    const n = new Notification(title, {
      body: String(body || '').slice(0, 300),
      tag,
      icon: '/icons/icon-192.png',
      requireInteraction,
      silent: false,
    });
    n.onclick = () => {
      try { window.focus(); } catch (e) { /* ignore */ }
      if (typeof onClick === 'function') onClick();
      n.close();
    };
    if (!requireInteraction) setTimeout(() => n.close(), 20000);
    return n;
  } catch (e) {
    console.warn('Desktop notification error:', e);
    return null;
  }
};
