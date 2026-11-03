package handlers

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestOwnsUserIDRejectsMismatchWithoutClaims(t *testing.T) {
	r := httptest.NewRequest(http.MethodGet, "/journal?user_id=user_abc", nil)
	w := httptest.NewRecorder()
	if ownsUserID(w, r, "user_abc") {
		t.Fatal("không có claims thì không được coi là chủ sở hữu")
	}
	if w.Code != http.StatusForbidden {
		t.Fatalf("code=%d", w.Code)
	}
}

func TestOwnsUserIDLegacyIDsPass(t *testing.T) {
	r := httptest.NewRequest(http.MethodGet, "/journal?user_id=12345", nil)
	if !ownsUserID(httptest.NewRecorder(), r, "12345") {
		t.Fatal("id không phải kiểu Clerk giữ hành vi cũ")
	}
}
