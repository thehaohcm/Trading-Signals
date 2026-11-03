package models

import "time"

// AssetSignal is the AI buy/avoid verdict for one asset group plus the optional admin override.
// AIStatus / AdminStatus are "buy" or "avoid"; AdminStatus is nil when the admin follows the AI.
type AssetSignal struct {
	AssetKey       string     `json:"asset_key"`
	AssetLabel     string     `json:"asset_label"`
	AIStatus       string     `json:"ai_status"`
	AIReason       string     `json:"ai_reason"`
	AIConfidence   *float64   `json:"ai_confidence"`
	AIUpdatedAt    *time.Time `json:"ai_updated_at"`
	AdminStatus    *string    `json:"admin_status"`
	AdminUpdatedBy *string    `json:"admin_updated_by"`
	AdminUpdatedAt *time.Time `json:"admin_updated_at"`
	// Who/what made the latest admin-side change: AdminSource "user" | "logic", AdminRule = which automatic rule.
	AdminSource *string `json:"admin_source"`
	AdminRule   *string `json:"admin_rule"`
	AdminNote   string  `json:"admin_note"`
	// Computed: COALESCE(admin_status, ai_status) and where it came from ("admin" | "ai").
	EffectiveStatus string `json:"effective_status"`
	Source          string `json:"source"`
}

// SetAssetSignalOverrideRequest: Status is "buy", "avoid", or "ai" (empty/"ai" clears the override).
type SetAssetSignalOverrideRequest struct {
	AssetKey  string `json:"asset_key"`
	Status    string `json:"status"`
	UpdatedBy string `json:"updated_by"`
	Note      string `json:"note"`
}

// AssetSignalChange is one row of the admin-status audit trail.
type AssetSignalChange struct {
	ID             int64     `json:"id"`
	AssetKey       string    `json:"asset_key"`
	ChangedAt      time.Time `json:"changed_at"`
	OldAdminStatus *string   `json:"old_admin_status"`
	NewAdminStatus *string   `json:"new_admin_status"`
	Source         string    `json:"source"`
	Rule           *string   `json:"rule"`
	ChangedBy      *string   `json:"changed_by"`
	Note           string    `json:"note"`
}
