package repository

import (
	"database/sql"
	"encoding/json"
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
