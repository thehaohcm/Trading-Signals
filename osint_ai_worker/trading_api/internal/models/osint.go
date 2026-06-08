package models

import (
	"encoding/json"
	"time"
)

type OsintSignal struct {
	ID           string    `json:"id"`
	SourceNewsID int       `json:"source_news_id"`
	Category     string    `json:"category"`
	Signal       string    `json:"signal"`
	Confidence   float64   `json:"confidence"`
	Reason       string    `json:"reason"`
	CreatedAt    time.Time `json:"created_at"`
}

type OsintThesis struct {
	ID                 string    `json:"id"`
	Thesis             string    `json:"thesis"`
	Confidence         float64   `json:"confidence"`
	SupportingEvidence string    `json:"supporting_evidence"`
	Status             string    `json:"status"`
	UpdatedAt          time.Time `json:"updated_at"`
}

type OsintWorldState struct {
	ID        int             `json:"id"`
	StateJSON json.RawMessage `json:"state_json"`
	UpdatedAt time.Time       `json:"updated_at"`
}

type OsintProposedChange struct {
	ID           string    `json:"id"`
	TargetEntity string    `json:"target_entity"`
	FieldName    string    `json:"field_name"`
	OldValue     string    `json:"old_value,omitempty"`
	NewValue     string    `json:"new_value"`
	Confidence   float64   `json:"confidence"`
	Reason       string    `json:"reason"`
	Status       string    `json:"status"` // 'pending', 'approved', 'rejected'
	CreatedAt    time.Time `json:"created_at"`
}
