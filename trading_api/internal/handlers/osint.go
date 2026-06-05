package handlers

import (
	"net/http"

	"github.com/gorilla/mux"
)

// OSINT Handlers

func (h *Handler) GetWorldState(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	state, err := h.Repo.GetWorldState()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to get world state: "+err.Error())
		return
	}
	respondJSON(w, http.StatusOK, state)
}

func (h *Handler) GetPendingProposedChanges(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	changes, err := h.Repo.GetPendingProposedChanges()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to get proposed changes: "+err.Error())
		return
	}
	respondJSON(w, http.StatusOK, changes)
}

func (h *Handler) ApproveProposedChange(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	vars := mux.Vars(r)
	id := vars["id"]
	if id == "" {
		respondError(w, http.StatusBadRequest, "Missing id parameter")
		return
	}

	err := h.Repo.ApproveProposedChange(id)
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to approve change: "+err.Error())
		return
	}
	respondJSON(w, http.StatusOK, map[string]string{"message": "Change approved successfully"})
}

func (h *Handler) RejectProposedChange(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	vars := mux.Vars(r)
	id := vars["id"]
	if id == "" {
		respondError(w, http.StatusBadRequest, "Missing id parameter")
		return
	}

	err := h.Repo.RejectProposedChange(id)
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to reject change: "+err.Error())
		return
	}
	respondJSON(w, http.StatusOK, map[string]string{"message": "Change rejected successfully"})
}

func (h *Handler) GetSignals(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	signals, err := h.Repo.GetSignals()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to get signals: "+err.Error())
		return
	}
	respondJSON(w, http.StatusOK, signals)
}

func (h *Handler) GetTheses(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		return
	}

	theses, err := h.Repo.GetTheses()
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to get theses: "+err.Error())
		return
	}
	respondJSON(w, http.StatusOK, theses)
}
