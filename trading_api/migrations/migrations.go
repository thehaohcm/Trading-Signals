package migrations

import (
	"database/sql"
	"embed"
	"fmt"
	"io/fs"
	"log"
	"sort"
)

//go:embed *.sql
var MigrationFiles embed.FS

// Run automatically checks and executes pending SQL migrations in sequential order
func Run(db *sql.DB) error {
	// 1. Create schema_migrations table if not exists
	createTableQuery := `
		CREATE TABLE IF NOT EXISTS public.schema_migrations (
			version VARCHAR(255) PRIMARY KEY,
			applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
		);
	`
	if _, err := db.Exec(createTableQuery); err != nil {
		return fmt.Errorf("failed to create schema_migrations table: %w", err)
	}

	// 2. Read all embedded .sql files
	entries, err := fs.ReadDir(MigrationFiles, ".")
	if err != nil {
		return fmt.Errorf("failed to read embedded migrations: %w", err)
	}

	// Sort file names alphabetically (000, 001, 002... 022)
	var fileNames []string
	for _, entry := range entries {
		if !entry.IsDir() && len(entry.Name()) > 4 && entry.Name()[len(entry.Name())-4:] == ".sql" {
			fileNames = append(fileNames, entry.Name())
		}
	}
	sort.Strings(fileNames)

	// 3. Query already applied migrations
	rows, err := db.Query("SELECT version FROM public.schema_migrations;")
	if err != nil {
		return fmt.Errorf("failed to query schema_migrations: %w", err)
	}
	defer rows.Close()

	applied := make(map[string]bool)
	for rows.Next() {
		var v string
		if err := rows.Scan(&v); err == nil {
			applied[v] = true
		}
	}

	// 4. Apply pending migrations sequentially
	appliedCount := 0
	for _, name := range fileNames {
		if applied[name] {
			continue
		}

		log.Printf("📦 [Auto-Migration] Đang áp dụng migration: %s\n", name)
		content, err := MigrationFiles.ReadFile(name)
		if err != nil {
			return fmt.Errorf("failed to read migration file %s: %w", name, err)
		}

		// Execute migration in a transaction
		tx, err := db.Begin()
		if err != nil {
			return fmt.Errorf("failed to begin transaction for %s: %w", name, err)
		}

		if _, err := tx.Exec(string(content)); err != nil {
			tx.Rollback()
			return fmt.Errorf("failed to execute migration %s: %w", name, err)
		}

		if _, err := tx.Exec("INSERT INTO public.schema_migrations (version, applied_at) VALUES ($1, CURRENT_TIMESTAMP);", name); err != nil {
			tx.Rollback()
			return fmt.Errorf("failed to record migration %s: %w", name, err)
		}

		if err := tx.Commit(); err != nil {
			return fmt.Errorf("failed to commit migration %s: %w", name, err)
		}

		log.Printf("✅ [Auto-Migration] Áp dụng thành công: %s\n", name)
		appliedCount++
	}

	if appliedCount > 0 {
		log.Printf("🎉 [Auto-Migration] Đã tự động áp dụng %d migration mới!\n", appliedCount)
	} else {
		log.Println("✨ [Auto-Migration] Database schema đã ở trạng thái mới nhất.")
	}

	return nil
}
