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
      <div v-for="post in posts" :key="post.id" class="card mb-3 post-card text-start">
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
            <button class="btn btn-sm btn-light flex-grow-1" @click="toggleComments(post)">
              <i class="fas fa-comment me-1"></i> Comment
            </button>
          </div>
          
          <!-- Comments Section -->
          <div v-if="post.showComments" class="mt-3 pt-3 border-top">
             <div v-if="post.commentsLoading" class="text-center">
                 <div class="spinner-border spinner-border-sm text-secondary" role="status"></div>
             </div>
             <div v-else>
                 <div v-for="comment in post.comments" :key="comment.id" class="d-flex mb-2">
                     <div class="avatar-circle-sm me-2 flex-shrink-0">
                         {{ getInitials(comment.user_name) }}
                     </div>
                     <div class="bg-light p-2 rounded flex-grow-1">
                         <div class="d-flex justify-content-between">
                            <span class="fw-bold small">{{ comment.user_name }}</span>
                            <small class="text-muted" style="font-size: 0.75rem;">{{ formatTime(comment.created_at) }}</small>
                         </div>
                         <p class="mb-0 small">{{ comment.content }}</p>
                     </div>
                 </div>
                 
                 <!-- Add Comment Input -->
                 <div class="d-flex mt-2 align-items-center">
                     <input 
                        type="text" 
                        class="form-control form-control-sm me-2" 
                        placeholder="Write a comment..." 
                        v-model="post.newComment"
                        @keyup.enter="submitComment(post)"
                     >
                     <button class="btn btn-sm btn-primary" @click="submitComment(post)" :disabled="!post.newComment">
                         <i class="fas fa-paper-plane"></i>
                     </button>
                 </div>
             </div>
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
    const currentUserInfo = ref({});

    const fetchPosts = async () => {
      loading.value = true;
      try {
        posts.value = await communityService.getPosts();
        // Initialize reactive properties for comments
        posts.value.forEach(p => {
            p.showComments = false;
            p.comments = [];
            p.commentsLoading = false;
            p.newComment = '';
        });
      } finally {
        loading.value = false;
      }
    };

    onMounted(() => {
      const userInfoStr = localStorage.getItem('userInfo');
      if (userInfoStr) {
          currentUserInfo.value = JSON.parse(userInfoStr);
          currentUserId.value = currentUserInfo.value.id;
      }
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
    
    const deletePost = async (postId) => {
       if(confirm("Are you sure you want to delete this post?")) {
           await communityService.deletePost(postId);
           fetchPosts();
       }
    };

    const toggleComments = async (post) => {
        post.showComments = !post.showComments;
        if (post.showComments && post.comments.length === 0) {
            post.commentsLoading = true;
            try {
                post.comments = await communityService.getComments(post.id);
            } finally {
                post.commentsLoading = false;
            }
        }
    };

    const submitComment = async (post) => {
        if (!post.newComment || !post.newComment.trim()) return;
        
        const commentData = {
            post_id: post.id,
            user_id: currentUserInfo.value.custodyCode || currentUserInfo.value.id || 'unknown',
            user_name: currentUserInfo.value.name || 'Anonymous',
            content: post.newComment
        };

        try {
            const newComment = await communityService.addComment(commentData);
            post.comments.push(newComment);
            post.newComment = '';
        } catch (error) {
            alert('Failed to post comment');
        }
    };

    return {
      posts,
      loading,
      getInitials,
      formatTime,
      likePost,
      deletePost,
      fetchPosts,
      currentUserId,
      toggleComments,
      submitComment
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

.avatar-circle-sm {
  width: 32px;
  height: 32px;
  background-color: #4a5568;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.8rem;
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
