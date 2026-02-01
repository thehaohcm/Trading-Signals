<template>

  <div class="d-flex flex-column min-vh-100">
    <NavBar />
    <div class="container mt-5 flex-grow-1 journal-container">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="text-white">Investment Journal</h2>
        <button class="btn btn-primary" @click="openModal('add')">
          <i class="fas fa-plus me-2"></i>Add Entry
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center text-white">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="entries.length === 0" class="alert alert-info" role="alert">
        No journal entries found. Start by adding your first investment!
      </div>

      <!-- Entries Table -->
      <div v-else class="table-responsive">
        <table class="table table-dark table-hover">
          <thead>
            <tr>
              <th>Date</th>
              <th>Asset Type</th>
              <th>Symbol/Name</th>
              <th>Quantity</th>
              <th>Price</th>
              <th>Total Value</th>
              <th>Notes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in entries" :key="entry.id">
              <td>{{ formatDate(entry.entry_date) }}</td>
              <td>
                <span :class="['badge', getBadgeClass(entry.asset_type)]">{{ entry.asset_type }}</span>
              </td>
              <td>{{ entry.symbol }}</td>
              <td>{{ entry.quantity }}</td>
              <td>{{ formatCurrency(entry.price) }}</td>
              <td>{{ formatCurrency(entry.price * entry.quantity) }}</td>
              <td class="text-truncate" style="max-width: 200px;" :title="entry.notes">{{ entry.notes }}</td>
              <td>
                <button class="btn btn-sm btn-outline-info me-2" @click="openModal('edit', entry)">
                  Edit
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteEntry(entry.id)">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Add/Edit Modal -->
      <div v-if="showModal" class="modal-backdrop fade show"></div>
      <div class="modal fade" :class="{ 'show': showModal }" style="display: block;" v-if="showModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content text-dark">
            <div class="modal-header">
              <h5 class="modal-title">{{ modalMode === 'add' ? 'Add Investment' : 'Edit Investment' }}</h5>
              <button type="button" class="btn-close" @click="closeModal"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="submitForm">
                <div class="mb-3">
                  <label class="form-label">Asset Type</label>
                  <select class="form-select" v-model="formData.asset_type" required>
                    <option value="GOLD">Gold</option>
                    <option value="SILVER">Silver</option>
                    <option value="STOCK">Stock</option>
                    <option value="CRYPTO">Crypto</option>
                    <option value="REAL_ESTATE">Real Estate</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
                <div class="mb-3">
                  <label class="form-label">Symbol / Name</label>
                  <input type="text" class="form-control" v-model="formData.symbol" placeholder="e.g., SJC, VN30, BTC" required>
                </div>
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label class="form-label">Quantity</label>
                    <input type="number" step="any" class="form-control" v-model.number="formData.quantity" required>
                  </div>
                  <div class="col-md-6 mb-3">
                    <label class="form-label">Price Data (per unit)</label>
                    <input type="number" step="any" class="form-control" v-model.number="formData.price" required>
                  </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Date</label>
                    <input type="datetime-local" class="form-control" v-model="formData.entry_date" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">Notes</label>
                  <textarea class="form-control" v-model="formData.notes" rows="3"></textarea>
                </div>
                <div class="d-grid">
                  <button type="submit" class="btn btn-primary">{{ modalMode === 'add' ? 'Save Entry' : 'Update Entry' }}</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

    </div>

    <AppFooter />
  </div>
</template>

<script>
import { ref, onMounted, reactive } from 'vue';

import { useRouter } from 'vue-router';
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';

export default {
  name: 'JournalView',
  components: {
    NavBar,
    AppFooter
  },
  setup() {
    const router = useRouter();
    const entries = ref([]);
    const isLoading = ref(true);
    const showModal = ref(false);
    const modalMode = ref('add');
    const formData = reactive({
      id: null,
      asset_type: 'STOCK',
      symbol: '',
      quantity: 1,
      price: 0,
      entry_date: new Date().toISOString().slice(0, 16),
      notes: ''
    });

    const getUserInfo = () => {
        const userInfoStr = localStorage.getItem('userInfo');
        if (!userInfoStr) return null;
        try {
            return JSON.parse(userInfoStr);
        } catch (e) {
            return null;
        }
    };

    const getHeaders = () => {
        const userInfo = getUserInfo();
        const token = localStorage.getItem('token');
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-User-ID': userInfo ? userInfo.id || userInfo.custodyCode : '' // Fallback to custodyCode or whatever ID logic
        };
    };

    const fetchEntries = async () => {
      isLoading.value = true;
      try {
        const userInfo = getUserInfo();
        if (!userInfo) {
            router.push('/login');
            return;
        }

        const response = await fetch('/journal', {
            headers: getHeaders()
        });
        
        if (response.status === 401) {
            // Token expired or invalid
            router.push('/login');
            return;
        }

        if (response.ok) {
            const data = await response.json();
            entries.value = data || [];
        }
      } catch (error) {
        console.error('Error fetching journal:', error);
      } finally {
        isLoading.value = false;
      }
    };

    const openModal = (mode, entry = null) => {
      modalMode.value = mode;
      if (mode === 'edit' && entry) {
        formData.id = entry.id;
        formData.asset_type = entry.asset_type;
        formData.symbol = entry.symbol;
        formData.quantity = entry.quantity;
        formData.price = entry.price;
        formData.entry_date = new Date(entry.entry_date).toISOString().slice(0, 16);
        formData.notes = entry.notes;
      } else {
        // Reset form
        formData.id = null;
        formData.asset_type = 'STOCK';
        formData.symbol = '';
        formData.quantity = 0;
        formData.price = 0;
        formData.entry_date = new Date().toISOString().slice(0, 16);
        formData.notes = '';
      }
      showModal.value = true;
    };

    const closeModal = () => {
      showModal.value = false;
    };

    const submitForm = async () => {
        try {
            const url = '/journal';
            const method = modalMode.value === 'add' ? 'POST' : 'PUT';
            const body = { ...formData };
            // Ensure date is in ISO format expected by Go's time.Time unmarshal usually works with RFC3339
            body.entry_date = new Date(body.entry_date).toISOString();

            const response = await fetch(url, {
                method: method,
                headers: getHeaders(),
                body: JSON.stringify(body)
            });

            if (response.ok) {
                closeModal();
                fetchEntries();
            } else {
                const errorText = await response.text();
                alert(`Failed to save entry: ${response.status} ${response.statusText}\n${errorText}`);
            }
        } catch (error) {
            console.error("Error saving entry:", error);
            alert("An error occurred.");
        }
    };

    const deleteEntry = async (id) => {
        if (!confirm("Are you sure you want to delete this entry?")) return;
        
        try {
            const response = await fetch(`/journal?id=${id}`, {
                method: 'DELETE',
                headers: getHeaders()
            });

            if (response.ok) {
                fetchEntries();
            } else {
                const errorText = await response.text();
                alert(`Failed to delete entry: ${response.status} ${response.statusText}\n${errorText}`);
            }
        } catch (error) {
            console.error("Error deleting entry:", error);
        }
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        return new Date(dateStr).toLocaleDateString() + ' ' + new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
    };

    const getBadgeClass = (type) => {
        switch(type) {
            case 'GOLD': return 'bg-warning text-dark';
            case 'STOCK': return 'bg-success';
            case 'CRYPTO': return 'bg-info text-dark';
            case 'SILVER': return 'bg-secondary';
            default: return 'bg-primary';
        }
    };

    onMounted(() => {
        fetchEntries();
    });

    return {
      entries,
      isLoading,
      showModal,
      modalMode,
      formData,
      openModal,
      closeModal,
      submitForm,
      deleteEntry,
      formatDate,
      formatCurrency,
      getBadgeClass
    };
  }
};
</script>

<style scoped>
.journal-container {
  min-height: 80vh;
}
.modal-backdrop {
    background-color: rgba(0,0,0,0.5);
    z-index: 1040;
}
.modal {
    z-index: 1050;
}
</style>
