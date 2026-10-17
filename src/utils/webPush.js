// Web Push: đăng ký trình duyệt nhận thông báo từ server (kể cả khi đã đóng tab).
// Backend: trading_api/internal/webpush — Service worker: public/sw.js

import { getNotifyPref } from './desktopNotify';

const ACTIVE_KEY = 'web_push_active';

const safeGet = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const safeSet = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } };

export const isWebPushSupported = () =>
  typeof window !== 'undefined' &&
  window.isSecureContext &&
  'serviceWorker' in navigator &&
  'PushManager' in window &&
  'Notification' in window;

export const isWebPushActive = () => safeGet(ACTIVE_KEY) === 'true';

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
