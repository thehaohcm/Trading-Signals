package handlers

import (
	"net/http/httptest"
	"testing"
)

// Chưa cấu hình verifier / token rác / token literal cũ "clerk_session" đều phải bị từ chối.
func TestIsRequestAuthorizedFailClosed(t *testing.T) {
	SetAuthVerifier(nil)
	for _, tok := range []string{"", "Bearer x", "Bearer clerk_session", "clerk_session", "Bearer a.b.c"} {
		r := httptest.NewRequest("POST", "/x", nil)
		if tok != "" {
			r.Header.Set("Authorization", tok)
		}
		if isRequestAuthorized(r) {
			t.Errorf("%q lẽ ra bị từ chối", tok)
		}
	}
}
