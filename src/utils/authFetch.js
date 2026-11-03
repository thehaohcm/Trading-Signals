// Gắn JWT Clerk THẬT vào mọi request gọi API cùng origin.
//
// Trước đây nhiều component tự gửi `Authorization: Bearer clerk_session` (chuỗi cố định) và backend chỉ
// kiểm tra "không rỗng". Nay backend kiểm tra chữ ký JWT của Clerk, nên mọi request tới API phải mang
// session token thật. Thay vì sửa hàng chục chỗ gọi fetch, bọc window.fetch một lần ở đây:
//   - chỉ áp dụng cho URL cùng origin (không rò token sang domain khác),
//   - bỏ qua file tĩnh / asset của webpack,
//   - ghi đè Authorization bằng token Clerk khi người dùng đang đăng nhập,
//   - nếu chưa đăng nhập: xoá token giả `clerk_session` để server trả 401 rõ ràng thay vì token rác.

const STATIC_PREFIXES = ['/static/', '/js/', '/css/', '/img/', '/fonts/', '/favicon', '/sockjs-node', '/hot-update']

function isApiRequest(url) {
  let u
  try {
    u = new URL(url, window.location.origin)
  } catch (e) {
    return false
  }
  if (u.origin !== window.location.origin) return false
  return !STATIC_PREFIXES.some((p) => u.pathname.startsWith(p))
}

// Lấy session token hiện tại (Clerk tự làm mới khi sắp hết hạn). Trả '' nếu chưa đăng nhập.
export async function getClerkToken() {
  try {
    const clerk = window.Clerk
    if (!clerk || !clerk.session) return ''
    return (await clerk.session.getToken()) || ''
  } catch (e) {
    return ''
  }
}

export function installAuthFetch() {
  if (window.__authFetchInstalled) return
  window.__authFetchInstalled = true
  const nativeFetch = window.fetch.bind(window)

  window.fetch = async function authFetch(input, init) {
    const url = typeof input === 'string' ? input : input && input.url
    if (!url || !isApiRequest(url)) return nativeFetch(input, init)

    const token = await getClerkToken()
    const headers = new Headers((init && init.headers) || (input instanceof Request ? input.headers : undefined))
    const current = headers.get('Authorization') || ''
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    } else if (/clerk_session/.test(current)) {
      headers.delete('Authorization') // token giả cũ → để server từ chối đúng nghĩa
    }
    return nativeFetch(input, { ...(init || {}), headers })
  }
}
