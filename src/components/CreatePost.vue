<template>
  <div class="card mb-4 create-post-card">
    <div class="card-body">
      <h5 class="card-title mb-3">Share your thoughts</h5>
      <div class="mb-3">
        <textarea
          class="form-control"
          rows="3"
          placeholder="What's on your mind? Share strategies, news, or questions..."
          v-model="content"
        ></textarea>
      </div>
      
      <div v-if="imageUrl" class="mb-3 position-relative d-inline-block">
        <img :src="imageUrl" class="img-preview rounded" alt="Preview">
        <button 
          @click="removeImage" 
          class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1 rounded-circle"
          style="width: 24px; height: 24px; padding: 0; line-height: 24px;"
        >
          &times;
        </button>
      </div>

      <div class="d-flex justify-content-between align-items-center">
        <div>
          <label class="btn btn-outline-secondary btn-sm me-2">
            <i class="fas fa-image"></i> Add Image
            <input type="file" @change="handleImageUpload" accept="image/*" class="d-none">
          </label>
        </div>
        <button 
          class="btn btn-primary" 
          @click="submitPost" 
          :disabled="!content.trim() && !imageUrl"
        >
          Post
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import communityService from '../services/communityService';

export default {
  name: 'CreatePost',
  emits: ['post-created'],
  setup(props, { emit }) {
    const content = ref('');
    const imageUrl = ref('');
    const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'));

    const handleImageUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;

      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        alert('File size too large. Max 5MB.');
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        imageUrl.value = e.target.result;
      };
      reader.readAsDataURL(file);
    };

    const removeImage = () => {
      imageUrl.value = '';
    };

    const submitPost = () => {
      if (!content.value.trim() && !imageUrl.value) return;

      const newPost = {
        content: content.value,
        image: imageUrl.value,
        userId: userInfo.value.id || 'unknown',
        userName: userInfo.value.name || userInfo.value.username || 'Anonymous',
        userCode: userInfo.value.custodyCode || ''
      };

      communityService.savePost(newPost);
      
      // Reset form
      content.value = '';
      imageUrl.value = '';
      
      emit('post-created');
    };

    return {
      content,
      imageUrl,
      handleImageUpload,
      removeImage,
      submitPost
    };
  }
};
</script>

<style scoped>
.create-post-card {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: none;
  background-color: #fff;
  color: #333;
}

.form-control {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  resize: none;
}

.form-control:focus {
  box-shadow: none;
  border-color: #6cb2eb;
}

.img-preview {
  max-width: 100%;
  max-height: 300px;
  object-fit: cover;
}
</style>
