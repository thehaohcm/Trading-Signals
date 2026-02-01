<template>
  <div class="community-feed">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    
    <div v-else-if="posts.length === 0" class="text-center py-5 text-muted">
      <p>No posts yet. Be the first to share something!</p>
    </div>

    <div v-else class="post-list">
      <div v-for="post in posts" :key="post.id" class="card mb-3 post-card">
        <div class="card-body">
          <div class="d-flex align-items-center mb-3">
            <div class="avatar-circle me-3">
              {{ getInitials(post.userName) }}
            </div>
            <div>
              <h6 class="mb-0 fw-bold">{{ post.userName }}</h6>
              <small class="text-muted">{{ formatTime(post.timestamp) }}</small>
            </div>
             <div class="ms-auto" v-if="post.userId === currentUserId || post.userId === 'unknown'"> <!-- Allow deleting if owner or legacy -->
                <button class="btn btn-sm btn-link text-danger text-decoration-none" @click="deletePost(post.id)">
                   <i class="fas fa-trash-alt"></i>
                </button>
            </div>
          </div>
          
          <p class="card-text mb-3" style="white-space: pre-wrap;">{{ post.content }}</p>
          
          <div v-if="post.image" class="mb-3">
            <img :src="post.image" class="img-fluid rounded" alt="Post content">
          </div>
          
          <div class="d-flex pt-2 border-top">
            <button 
              class="btn btn-sm btn-light me-3 flex-grow-1"
              @click="likePost(post.id)"
              :class="{ 'text-primary': post.liked }"
            >
              <i class="fas fa-thumbs-up me-1"></i> Like ({{ post.likes || 0 }})
            </button>
            <button class="btn btn-sm btn-light flex-grow-1">
              <i class="fas fa-comment me-1"></i> Comment
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import communityService from '../services/communityService';

export default {
  name: 'CommunityFeed',
  setup() {
    const posts = ref([]);
    const loading = ref(true);
    const currentUserId = ref('');

    const fetchPosts = () => {
      loading.value = true;
      try {
        posts.value = communityService.getPosts();
      } finally {
        loading.value = false;
      }
    };

    onMounted(() => {
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
      currentUserId.value = userInfo.id;
      fetchPosts();
    });

    const getInitials = (name) => {
      if (!name) return 'U';
      return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    };

    const formatTime = (timestamp) => {
      return communityService.formatTime(timestamp);
    };

    const likePost = (postId) => {
      const newLikes = communityService.likePost(postId);
      const post = posts.value.find(p => p.id === postId);
      if (post) {
        post.likes = newLikes;
        post.liked = true; // Local state only for visual feedback
      }
    };
    
    const deletePost = (postId) => {
       if(confirm("Are you sure you want to delete this post?")) {
           communityService.deletePost(postId);
           fetchPosts();
       }
    }

    return {
      posts,
      loading,
      getInitials,
      formatTime,
      likePost,
      deletePost,
      fetchPosts,
      currentUserId
    };
  }
};
</script>

<style scoped>
.avatar-circle {
  width: 40px;
  height: 40px;
  background-color: #2d3748;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.post-card {
  border: none;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  background: white;
  color: #333;
}

.btn-light {
  background-color: transparent;
  border: none;
  color: #6c757d;
  transition: all 0.2s;
}

.btn-light:hover {
  background-color: #f8f9fa;
  color: #2d3748;
}
</style>
