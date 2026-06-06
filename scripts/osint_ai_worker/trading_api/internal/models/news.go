package models

import (
	"time"
)

type NewsGroup struct {
	ID          int       `json:"id"`
	UserID      string    `json:"user_id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	Conclusion  string    `json:"conclusion"`
	CreatedAt   time.Time `json:"created_at"`
}

type NewsItem struct {
	ID         int       `json:"id"`
	GroupID    int       `json:"group_id"`
	Title      string    `json:"title"`
	Content    string    `json:"content"`
	SourceURL  string    `json:"source_url"`
	Importance int       `json:"importance"`
	Status     string    `json:"status"`
	CreatedAt  time.Time `json:"created_at"`
}
