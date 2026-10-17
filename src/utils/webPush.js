// Web Push: đăng ký trình duyệt nhận thông báo từ server (kể cả khi đã đóng tab).
// Backend: trading_api/internal/webpush — Service worker: public/sw.js

import { getNotifyPref, enableDesktopNotify, disableDesktopNotify, isDesktopNotifyEnabled } from './desktopNotify';

const ACTIVE_KEY = 'web_push_active';
// Người dùng đã chủ động TẮT thông báo trên màn hình → không tự hỏi quyền nữa
const OPTOUT_KEY = 'desktop_notify_optout';

const safeGet = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const safeSet = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } };

export const isWebPushSupported = () =>
  typeof window !== 'undefined' &&
  window.isSecureContext &&
  'serviceWorker' in navigator &&
  'PushManager' in window &&
  'Notification' in window;

export const isWebPushActive = () => safeGet(ACTIVE_KEY) === 'true';

// ── iPhone / iPad ───────────────────────────────────────────────
// Mọi trình duyệt trên iOS (Safari, Chrome, Firefox...) dùng WebKit: Notification/Push chỉ có khi
// web được mở từ icon Màn hình chính (iOS/iPadOS 16.4+). Mở trong trình duyệt thì API bị ẩn hoàn toàn.
export const isIOSDevice = () =>
  typeof navigator !== 'undefined' &&
  (/iPhone|iPad|iPod/i.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)); // iPadOS báo là "Macintosh"

export const isStandaloneApp = () =>
  typeof window !== 'undefined' &&
  (window.navigator.standalone === true ||
    (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches));

/** Phiên bản iOS dạng số, VD 17.2 (0 nếu không xác định) */
export const iosVersion = () => {
  const ua = (typeof navigator !== 'undefined' && navigator.userAgent) || '';
  const m = ua.match(/OS (\d+)[_.](\d+)/) || ua.match(/Version\/(\d+)\.(\d+)/);
  return m ? parseFloat(`${m[1]}.${m[2]}`) : 0;
};

/** '' nếu dùng được bình thường; 'install' cần thêm vào Màn hình chính; 'upgrade' iOS quá cũ */
export const iosPushBlocker = () => {
  if (!isIOSDevice()) return '';
  const v = iosVersion();
  if (v && v < 16.4) return 'upgrade';
  if (!isStandaloneApp()) return 'install';
  return '';
};

const urlB64ToUint8Array = (base64) => {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4);
  const raw = atob((base64 + padding).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
};

const sameKey = (buf, b64) => {
  if (!buf) return false;
  const a = new Uint8Array(buf);
  const b = urlB64ToUint8Array(b64);
  return a.length === b.length && a.every((v, i) => v === b[i]);
};

const currentPrefs = () => ({
  notify_alerts: getNotifyPref('alerts'),
  notify_news: getNotifyPref('news'),
});

const postJSON = async (url, body) => {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  let data = {};
  try { data = await res.json(); } catch (e) { /* ignore */ }
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
};

const registerWorker = async () => {
  const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
  await navigator.serviceWorker.ready;
  return reg;
};

export const getCurrentSubscription = async () => {
  if (!isWebPushSupported()) return null;
  const reg = await navigator.serviceWorker.getRegistration('/');
  return reg ? reg.pushManager.getSubscription() : null;
};

/** Bật Web Push. Phải gọi từ thao tác của người dùng (click). Trả về 'granted' | 'denied' | 'default' | 'unsupported'. */
export const enableWebPush = async () => {
  if (!isWebPushSupported()) return 'unsupported';
  let permission = Notification.permission;
  if (permission === 'default') permission = await Notification.requestPermission();
  if (permission !== 'granted') return permission;

  const reg = await registerWorker();
  const keyRes = await fetch('/api/push/vapid-public-key');
  if (!keyRes.ok) throw new Error(`Server chưa hỗ trợ Web Push (HTTP ${keyRes.status})`);
  const { publicKey } = await keyRes.json();

  let sub = await reg.pushManager.getSubscription();
  if (sub && !sameKey(sub.options && sub.options.applicationServerKey, publicKey)) {
    await sub.unsubscribe(); // khoá server đã đổi → đăng ký lại
    sub = null;
  }
  if (!sub) {
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlB64ToUint8Array(publicKey),
    });
  }
  await postJSON('/api/push/subscribe', { subscription: sub.toJSON(), ...currentPrefs() });
  safeSet(ACTIVE_KEY, 'true');
  return 'granted';
};

export const disableWebPush = async () => {
  safeSet(ACTIVE_KEY, 'false');
  const sub = await getCurrentSubscription();
  if (!sub) return;
  try { await postJSON('/api/push/unsubscribe', { endpoint: sub.endpoint }); } catch (e) { console.warn(e); }
  try { await sub.unsubscribe(); } catch (e) { console.warn(e); }
};

/** Gửi tuỳ chọn bật/tắt Cảnh báo / Breaking News lên server (nếu đang bật Web Push). */
export const syncWebPushPrefs = async () => {
  if (!isWebPushActive()) return;
  const sub = await getCurrentSubscription();
  if (sub) await postJSON('/api/push/subscribe', { subscription: sub.toJSON(), ...currentPrefs() });
};

export const sendTestPush = async () => {
  const sub = await getCurrentSubscription();
  if (!sub) throw new Error('Trình duyệt chưa đăng ký nhận thông báo');
  await postJSON('/api/push/test', { endpoint: sub.endpoint });
};

/** Gọi khi tải trang: đồng bộ trạng thái thực tế của trình duyệt với cờ đã lưu. */
export const restoreWebPush = async () => {
  if (!isWebPushSupported() || !isWebPushActive()) return false;
  try {
    const sub = await getCurrentSubscription();
    if (!sub || Notification.permission !== 'granted') {
      safeSet(ACTIVE_KEY, 'false');
      return false;
    }
    // Đăng ký lại phòng khi server mất dữ liệu / đổi instance
    await postJSON('/api/push/subscribe', { subscription: sub.toJSON(), ...currentPrefs() });
    return true;
  } catch (e) {
    console.warn('restoreWebPush:', e);
    return isWebPushActive();
  }
};

export const isNotifyOptedOut = () => safeGet(OPTOUT_KEY) === 'true';

/** Trạng thái thông báo hiện tại: { supported, permission, mode: 'push' | 'local' | '' } */
export const getNotificationStatus = () => {
  const supported = typeof window !== 'undefined' && 'Notification' in window;
  const permission = supported ? Notification.permission : 'unsupported';
  let mode = '';
  if (supported && permission === 'granted') {
    if (isWebPushActive()) mode = 'push';
    else if (isDesktopNotifyEnabled()) mode = 'local';
  }
  return { supported, permission, mode };
};

// Báo cho các component (AlertOverlay, banner nhắc bật thông báo) cập nhật giao diện
export const emitNotificationStatus = () => {
  try {
    window.dispatchEvent(new CustomEvent('notify-status-changed', { detail: getNotificationStatus() }));
  } catch (e) { /* ignore */ }
};
export const setNotifyOptOut = (optOut) => safeSet(OPTOUT_KEY, optOut ? 'true' : 'false');

/**
 * Bật thông báo: ưu tiên Web Push (nhận cả khi đóng tab), lỗi thì dùng thông báo khi website đang mở.
 * Trả về { mode: 'push' | 'local' | '', permission, error }.
 * Lưu ý: hàm này gọi Notification.requestPermission() ngay ở bước đầu tiên (không await gì trước đó)
 * để trình duyệt vẫn coi là trong thao tác của người dùng.
 */
export const enableNotifications = async () => {
  let mode = '';
  let error = '';
  let permission = typeof Notification !== 'undefined' ? Notification.permission : 'unsupported';
  if (isWebPushSupported()) {
    try {
      permission = await enableWebPush();
      if (permission === 'granted') mode = 'push';
    } catch (e) {
      console.warn('Web Push error:', e);
      error = e.message || String(e);
      permission = Notification.permission;
    }
  }
  if (!mode && permission !== 'denied') {
    permission = await enableDesktopNotify();
    if (permission === 'granted') mode = 'local';
  }
  emitNotificationStatus();
  return { mode, permission, error };
};

export const disableNotifications = async () => {
  await disableWebPush();
  disableDesktopNotify();
  emitNotificationStatus();
};

/**
 * Gọi khi vào website. Thông báo trên màn hình MẶC ĐỊNH BẬT:
 * - Đã cho phép nhưng chưa đăng ký push (hoặc mất đăng ký) → tự đăng ký lại, không hỏi gì.
 * - Chưa cấp quyền → hiện hộp xin quyền của trình duyệt ở lần click/gõ phím đầu tiên trên trang
 *   (Firefox/Safari bắt buộc phải có thao tác người dùng; Chrome cũng hiện rõ hơn so với hỏi lúc tải trang).
 * - Người dùng đã tắt trong Cài đặt Báo Động hoặc đã chặn quyền → không làm gì.
 * onChange(result) được gọi khi trạng thái thay đổi.
 */
export const autoSetupNotifications = async (onChange) => {
  if (typeof window === 'undefined' || !('Notification' in window)) return;
  if (isNotifyOptedOut() || Notification.permission === 'denied') return;

  const run = async () => {
    const result = await enableNotifications();
    // Người dùng có thể vừa tắt toggle trong lúc đang đăng ký
    if (isNotifyOptedOut()) {
      await disableNotifications();
      return;
    }
    if (typeof onChange === 'function') onChange(result);
  };

  if (Notification.permission === 'granted') {
    const restored = await restoreWebPush();
    if (!restored) await run();
    else if (typeof onChange === 'function') onChange({ mode: 'push', permission: 'granted', error: '' });
    return;
  }

  // permission === 'default' → chờ thao tác đầu tiên của người dùng
  const events = ['pointerdown', 'keydown'];
  const handler = (e) => {
    // Bấm nút "Bật thông báo" trên banner → để nút đó tự xử lý, tránh hỏi quyền 2 lần
    if (e && e.target && e.target.closest && e.target.closest('[data-notify-cta]')) return;
    events.forEach((ev) => window.removeEventListener(ev, handler, true));
    if (!isNotifyOptedOut() && Notification.permission === 'default') run();
  };
  events.forEach((ev) => window.addEventListener(ev, handler, true));
};
