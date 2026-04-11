package main

import (
	"fmt"
	"log"
	"net"
	"net/http"

	"trading_api/internal/db"
	"trading_api/internal/handlers"
	"trading_api/internal/repository"

	"github.com/gorilla/mux"
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

	// Register Macro Intelligence Hub API routes
	handlers.RegisterNewsRoutes(router, database)

	// Start Server
	port := "8080"
	fmt.Printf("Server listening on :%s\n", port)
	addr := net.JoinHostPort("::", port)
	server := &http.Server{Addr: addr, Handler: router}
	log.Fatalln(server.ListenAndServe())
}
