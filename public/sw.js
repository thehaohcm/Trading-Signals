/* Service worker Web Push — Trading Signals
 * Nhận push từ backend (trading_api/internal/webpush) và hiện thông báo hệ thống
 * trên Chrome / Edge / Firefox / Safari, kể cả khi đã đóng tab website.
 */

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));

const urlB64ToUint8Array = (base64) => {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4);
  const raw = atob((base64 + padding).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
};

self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { title: 'Trading Signals', body: event.data ? event.data.text() : '' };
  }

  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    // Đang xem website → vẫn hiện (yêu cầu của Chrome) nhưng không phát tiếng, vì trang đã có thẻ cảnh báo/âm báo
    const userIsLooking = windows.some((c) => c.focused && c.visibilityState === 'visible');

    await self.registration.showNotification(data.title || 'Trading Signals', {
      body: data.body || '',
      tag: data.tag || undefined,
      renotify: Boolean(data.tag),
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      requireInteraction: Boolean(data.requireInteraction),
      silent: userIsLooking,
      data: { url: data.url || '/', kind: data.kind, news: data.news || null },
    });
  })());
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const { url = '/', kind, news } = event.notification.data || {};

  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    const client = windows.find((c) => new URL(c.url).origin === self.location.origin);

    if (client) {
      await client.focus();
      if (kind === 'news' && news) client.postMessage({ type: 'open-news', news });
      return;
    }

    let target = url;
    if (kind === 'news' && news) {
      const compact = { ...news, description: String(news.description || '').slice(0, 500) };
      target = '/?push_news=' + encodeURIComponent(JSON.stringify(compact));
    }
    await self.clients.openWindow(target);
  })());
});

// Trình duyệt tự làm mới subscription (hết hạn / đổi khoá) → đăng ký lại, giữ tuỳ chọn cũ
self.addEventListener('pushsubscriptionchange', (event) => {
  event.waitUntil((async () => {
    const res = await fetch('/api/push/vapid-public-key');
    const { publicKey } = await res.json();
    const sub = await self.registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlB64ToUint8Array(publicKey),
    });
    await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subscription: sub.toJSON(),
        old_endpoint: event.oldSubscription ? event.oldSubscription.endpoint : '',
      }),
    });
  })());
});
