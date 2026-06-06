package repository

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"trading_api/internal/models"
)

// World State methods
func (r *Repository) GetWorldState() (models.OsintWorldState, error) {
	var state models.OsintWorldState
	var stateJSONStr string

	err := r.DB.QueryRow(`
		SELECT id, state_json, updated_at
		FROM osint_world_state
		WHERE id = 1
	`).Scan(&state.ID, &stateJSONStr, &state.UpdatedAt)

	if err != nil {
		if err == sql.ErrNoRows {
			// Return empty state if none exists
			return models.OsintWorldState{
				ID:        1,
				StateJSON: json.RawMessage("{}"),
				UpdatedAt: time.Now(),
			}, nil
		}
		return state, err
	}

	state.StateJSON = json.RawMessage(stateJSONStr)
	return state, nil
}

func (r *Repository) UpdateWorldState(stateJSON json.RawMessage) error {
	stateStr := string(stateJSON)
	_, err := r.DB.Exec(`
		INSERT INTO osint_world_state (id, state_json, updated_at)
		VALUES (1, $1, CURRENT_TIMESTAMP)
		ON CONFLICT (id) DO UPDATE
		SET state_json = EXCLUDED.state_json, updated_at = CURRENT_TIMESTAMP
	`, stateStr)
	return err
}

// Proposed Changes methods
func (r *Repository) GetPendingProposedChanges() ([]models.OsintProposedChange, error) {
	rows, err := r.DB.Query(`
		SELECT id, target_entity, field_name, old_value, new_value, confidence, reason, status, created_at
		FROM osint_proposed_changes
		WHERE status = 'pending'
		ORDER BY created_at ASC
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var changes []models.OsintProposedChange
	for rows.Next() {
		var c models.OsintProposedChange
		var oldVal sql.NullString
		if err := rows.Scan(&c.ID, &c.TargetEntity, &c.FieldName, &oldVal, &c.NewValue, &c.Confidence, &c.Reason, &c.Status, &c.CreatedAt); err != nil {
			return nil, err
		}
		if oldVal.Valid {
			c.OldValue = oldVal.String
		}
		changes = append(changes, c)
	}

	if changes == nil {
		changes = []models.OsintProposedChange{}
	}
	return changes, nil
}

func (r *Repository) ApproveProposedChange(id string) error {
	// 1. Get the change
	var change models.OsintProposedChange
	var oldVal sql.NullString
	err := r.DB.QueryRow(`
		SELECT id, target_entity, field_name, old_value, new_value, confidence, reason, status, created_at
		FROM osint_proposed_changes
		WHERE id = $1
	`, id).Scan(&change.ID, &change.TargetEntity, &change.FieldName, &oldVal, &change.NewValue, &change.Confidence, &change.Reason, &change.Status, &change.CreatedAt)
	
	if err != nil {
		return err
	}
	
	if change.Status != "pending" {
		return fmt.Errorf("Change is not pending")
	}

	// 2. Start Transaction
	tx, err := r.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// 3. Mark as approved
	_, err = tx.Exec("UPDATE osint_proposed_changes SET status = 'approved' WHERE id = $1", id)
	if err != nil {
		return err
	}

	// 4. Update World State
	var stateStr string
	err = tx.QueryRow("SELECT state_json FROM osint_world_state WHERE id = 1").Scan(&stateStr)
	
	stateMap := make(map[string]map[string]string)
	if err == nil {
		json.Unmarshal([]byte(stateStr), &stateMap)
	} else if err != sql.ErrNoRows {
		return err
	}

	// Apply change
	if stateMap[change.TargetEntity] == nil {
		stateMap[change.TargetEntity] = make(map[string]string)
	}
	stateMap[change.TargetEntity][change.FieldName] = change.NewValue

	newStateBytes, _ := json.Marshal(stateMap)
	newStateStr := string(newStateBytes)

	_, err = tx.Exec(`
		INSERT INTO osint_world_state (id, state_json, updated_at)
		VALUES (1, $1, CURRENT_TIMESTAMP)
		ON CONFLICT (id) DO UPDATE
		SET state_json = EXCLUDED.state_json, updated_at = CURRENT_TIMESTAMP
	`, newStateStr)
	
	if err != nil {
		return err
	}

	// 5. Commit
	return tx.Commit()
}

func (r *Repository) RejectProposedChange(id string) error {
	_, err := r.DB.Exec("UPDATE osint_proposed_changes SET status = 'rejected' WHERE id = $1 AND status = 'pending'", id)
	return err
}

// Signals methods
func (r *Repository) GetSignals() ([]models.OsintSignal, error) {
	rows, err := r.DB.Query(`
		SELECT id, source_news_id, category, signal, confidence, reason, created_at
		FROM osint_signals
		ORDER BY created_at DESC LIMIT 100
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var signals []models.OsintSignal
	for rows.Next() {
		var s models.OsintSignal
		if err := rows.Scan(&s.ID, &s.SourceNewsID, &s.Category, &s.Signal, &s.Confidence, &s.Reason, &s.CreatedAt); err != nil {
			return nil, err
		}
		signals = append(signals, s)
	}

	if signals == nil {
		signals = []models.OsintSignal{}
	}
	return signals, nil
}

// Theses methods
func (r *Repository) GetTheses() ([]models.OsintThesis, error) {
	rows, err := r.DB.Query(`
		SELECT id, thesis, confidence, supporting_evidence, status, updated_at
		FROM osint_theses
		ORDER BY updated_at DESC
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var theses []models.OsintThesis
	for rows.Next() {
		var t models.OsintThesis
		if err := rows.Scan(&t.ID, &t.Thesis, &t.Confidence, &t.SupportingEvidence, &t.Status, &t.UpdatedAt); err != nil {
			return nil, err
		}
		theses = append(theses, t)
	}

	if theses == nil {
		theses = []models.OsintThesis{}
	}
	return theses, nil
}
