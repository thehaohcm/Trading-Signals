package main

import (
	"fmt"
	"log"
	"net"
	"net/http"

	"trading_api/internal/db"
	"trading_api/internal/handlers"
	"trading_api/internal/repository"
)

func main() {
	// Initialize Database
	database, err := db.Connect()
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer database.Close()

	// Initialize Repository and Handler
	repo := repository.NewRepository(database)
	h := handlers.NewHandler(repo)

	// Setup Routes
	http.HandleFunc("/getPotentialSymbols", h.GetPotentialSymbols)
	http.HandleFunc("/getPotentialWorldSymbols", h.GetPotentialWorldSymbols)
	http.HandleFunc("/getPotentialCoins", h.GetPotentialCoins)
	http.HandleFunc("/getPotentialForexPairs", h.GetPotentialForexPairs)
	http.HandleFunc("/health", h.HealthCheck)
	http.HandleFunc("/inputOTP", h.InputOTP)
	http.HandleFunc("/userTrade", h.UserTrade)
	http.HandleFunc("/getUserTrade", h.GetUserTrade)
	http.HandleFunc("/updateTradingSignal", h.UpdateTradingSignal)
	http.HandleFunc("/api/chat", h.ChatHandler)
	http.HandleFunc("/priceAlerts", h.PriceAlertsHandler)
	http.HandleFunc("/priceAlerts/", h.PriceAlertHandler)
	http.HandleFunc("/journal", h.JournalHandler)
	http.HandleFunc("/community/posts", h.CommunityPostsHandler)
	http.HandleFunc("/community/comments", h.CommunityCommentsHandler)
	http.HandleFunc("/getRealEstate", h.GetRealEstate)

	// Start Server
	port := "8080"
	fmt.Printf("Server listening on :%s\n", port)
	addr := net.JoinHostPort("::", port)
	server := &http.Server{Addr: addr}
	log.Fatalln(server.ListenAndServe())
}
