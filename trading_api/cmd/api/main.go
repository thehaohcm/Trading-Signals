package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"strings"

	"trading_api/internal/db"
	"trading_api/internal/handlers"
	"trading_api/internal/repository"

	"github.com/gorilla/mux"
)

func loadEnv() {
	// Try loading .env from current directory, parent directory, or trading_api directory
	paths := []string{".env", "../.env", "trading_api/.env"}
	for _, p := range paths {
		if _, err := os.Stat(p); err == nil {
			log.Printf("Loading environment from %s\n", p)
			file, err := os.Open(p)
			if err != nil {
				continue
			}
			defer file.Close()

			scanner := bufio.NewScanner(file)
			for scanner.Scan() {
				line := strings.TrimSpace(scanner.Text())
				if line == "" || strings.HasPrefix(line, "#") {
					continue
				}
				parts := strings.SplitN(line, "=", 2)
				if len(parts) == 2 {
					key := strings.TrimSpace(parts[0])
					value := strings.TrimSpace(parts[1])
					// Strip quotes if present
					if (strings.HasPrefix(value, "\"") && strings.HasSuffix(value, "\"")) ||
						(strings.HasPrefix(value, "'") && strings.HasSuffix(value, "'")) {
						value = value[1 : len(value)-1]
					}
					os.Setenv(key, value)
				}
			}
			break
		}
	}
}

func main() {
	// Load environment variables locally
	loadEnv()

	// Initialize Database
	database, err := db.Connect()
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer database.Close()

	// Initialize Repository and Handler
	repo := repository.NewRepository(database)
	h := handlers.NewHandler(repo)

	// Use gorilla/mux for advanced routing
	router := mux.NewRouter()

	// Register legacy routes (giữ nguyên các route cũ)
	router.HandleFunc("/getPotentialSymbols", h.GetPotentialSymbols)
	router.HandleFunc("/getPotentialWorldSymbols", h.GetPotentialWorldSymbols)
	router.HandleFunc("/getPotentialCoins", h.GetPotentialCoins)
	router.HandleFunc("/getPotentialForexPairs", h.GetPotentialForexPairs)
	router.HandleFunc("/health", h.HealthCheck)
	router.HandleFunc("/inputOTP", h.InputOTP)
	router.HandleFunc("/userTrade", h.UserTrade)
	router.HandleFunc("/getUserTrade", h.GetUserTrade)
	router.HandleFunc("/updateTradingSignal", h.UpdateTradingSignal)
	router.HandleFunc("/api/chat", h.ChatHandler)
	router.HandleFunc("/priceAlerts", h.PriceAlertsHandler)
	router.HandleFunc("/priceAlerts/", h.PriceAlertHandler)
	router.HandleFunc("/journal", h.JournalHandler)
	router.HandleFunc("/community/posts", h.CommunityPostsHandler)
	router.HandleFunc("/community/comments", h.CommunityCommentsHandler)
	router.HandleFunc("/getRealEstate", h.GetRealEstate)

	// Register SSH Script execution route
	router.HandleFunc("/runSSHScript", h.RunSSHScript).Methods("POST", "OPTIONS")

	// Register Triggered Alerts routes
	router.HandleFunc("/triggeredAlerts", h.GetTriggeredAlerts).Methods("GET", "OPTIONS")
	router.HandleFunc("/triggeredAlerts/read", h.MarkTriggeredAlertsAsRead).Methods("POST", "OPTIONS")

	// Register Macro Intelligence Hub API routes
	handlers.RegisterNewsRoutes(router, database)

	// Start Server
	port := "8080"
	fmt.Printf("Server listening on :%s\n", port)
	addr := net.JoinHostPort("::", port)
	server := &http.Server{Addr: addr, Handler: router}
	log.Fatalln(server.ListenAndServe())
}
