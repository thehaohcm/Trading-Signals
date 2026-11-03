package repository

import (
	"database/sql"
	"fmt"
	"strings"

	"trading_api/internal/models"
)

func nullStr(n sql.NullString) *string {
	if !n.Valid {
		return nil
	}
	v := n.String
	return &v
}

// GetAssetSignals returns every asset group with its AI verdict, admin override and effective status.
func (r *Repository) GetAssetSignals() ([]models.AssetSignal, error) {
	rows, err := r.DB.Query(`
		SELECT asset_key, asset_label, ai_status, ai_reason, ai_confidence, ai_updated_at,
		       admin_status, admin_updated_by, admin_updated_at, admin_source, admin_rule, admin_note
		FROM public.ai_asset_signals
		ORDER BY sort_order, asset_key
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	signals := []models.AssetSignal{}
	for rows.Next() {
		var s models.AssetSignal
		var conf sql.NullFloat64
		var aiAt, adminAt sql.NullTime
		var adminStatus, adminBy, adminSource, adminRule sql.NullString
		if err := rows.Scan(&s.AssetKey, &s.AssetLabel, &s.AIStatus, &s.AIReason, &conf, &aiAt,
			&adminStatus, &adminBy, &adminAt, &adminSource, &adminRule, &s.AdminNote); err != nil {
			return nil, err
		}
		if conf.Valid {
			v := conf.Float64
			s.AIConfidence = &v
		}
		if aiAt.Valid {
			s.AIUpdatedAt = &aiAt.Time
		}
		if adminAt.Valid {
			s.AdminUpdatedAt = &adminAt.Time
		}
		s.AdminStatus, s.AdminUpdatedBy = nullStr(adminStatus), nullStr(adminBy)
		s.AdminSource, s.AdminRule = nullStr(adminSource), nullStr(adminRule)
		s.EffectiveStatus, s.Source = s.AIStatus, "ai"
		if s.AdminStatus != nil {
			s.EffectiveStatus, s.Source = *s.AdminStatus, "admin"
		}
		signals = append(signals, s)
	}
	return signals, rows.Err()
}

// SetAssetSignalOverride sets the admin override ("buy" / "avoid") or clears it (status "" / "ai") for one asset.
// The change is recorded as made by a user (updatedBy) and appended to the audit trail.
func (r *Repository) SetAssetSignalOverride(assetKey, status, updatedBy, note string) error {
	tx, err := r.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	var old sql.NullString
	if err := tx.QueryRow(`SELECT admin_status FROM public.ai_asset_signals WHERE asset_key = $1 FOR UPDATE`, assetKey).Scan(&old); err != nil {
		if err == sql.ErrNoRows {
			return fmt.Errorf("unknown asset_key %q", assetKey)
		}
		return err
	}

	var newStatus interface{} // nil => follow the AI
	if status == "buy" || status == "avoid" {
		newStatus = status
	}
	note = strings.TrimSpace(note)
	if _, err := tx.Exec(`
		UPDATE public.ai_asset_signals
		SET admin_status = $2::varchar,
		    ai_disagree_since = CASE WHEN $2::varchar IS NOT NULL AND ai_status <> $2::varchar THEN CURRENT_TIMESTAMP ELSE NULL END,
		    admin_source = 'user', admin_rule = NULL, admin_note = $3,
		    admin_updated_by = $4, admin_updated_at = CURRENT_TIMESTAMP
		WHERE asset_key = $1`, assetKey, newStatus, note, updatedBy); err != nil {
		return err
	}
	if _, err := tx.Exec(`
		INSERT INTO public.ai_asset_signal_changes (asset_key, old_admin_status, new_admin_status, source, rule, changed_by, note)
		VALUES ($1, $2, $3::varchar, 'user', NULL, $4, $5)`, assetKey, nullStr(old), newStatus, updatedBy, note); err != nil {
		return err
	}
	return tx.Commit()
}

// GetAssetSignalChanges returns the audit trail, newest first (assetKey "" = all assets).
func (r *Repository) GetAssetSignalChanges(assetKey string, limit int) ([]models.AssetSignalChange, error) {
	if limit <= 0 || limit > 200 {
		limit = 50
	}
	rows, err := r.DB.Query(`
		SELECT id, asset_key, changed_at, old_admin_status, new_admin_status, source, rule, changed_by, note
		FROM public.ai_asset_signal_changes
		WHERE ($1 = '' OR asset_key = $1)
		ORDER BY changed_at DESC, id DESC
		LIMIT $2`, assetKey, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	changes := []models.AssetSignalChange{}
	for rows.Next() {
		var c models.AssetSignalChange
		var oldS, newS, rule, by sql.NullString
		if err := rows.Scan(&c.ID, &c.AssetKey, &c.ChangedAt, &oldS, &newS, &c.Source, &rule, &by, &c.Note); err != nil {
			return nil, err
		}
		c.OldAdminStatus, c.NewAdminStatus, c.Rule, c.ChangedBy = nullStr(oldS), nullStr(newS), nullStr(rule), nullStr(by)
		changes = append(changes, c)
	}
	return changes, rows.Err()
}
