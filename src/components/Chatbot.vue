<template>
  <div v-if="isChatVisible" class="chatbot-container card shadow">
    <div class="chat-header card-header d-flex justify-content-between align-items-center">
      <span>Chatbot</span>
      <button type="button" class="btn-close" aria-label="Close" @click="toggleChat"></button>
    </div>
    <div class="chat-window card-body">
      <div v-for="(message, index) in messages" :key="index" :class="message.sender">
        {{ message.text }}
      </div>
    </div>
    <div class="card-footer">
      <div class="input-group">
        <input v-model="newMessage" @keyup.enter="sendMessage" placeholder="Type your message..." type="text" class="form-control">
        <button @click="sendMessage" class="btn btn-primary">Send</button>
      </div>
    </div>
  </div>
  <button v-else @click="toggleChat" class="chat-icon btn btn-primary rounded-circle">💬</button>
</template>

<script>
import { ref, watch } from 'vue';

export default {
  name: 'ChatbotWidget',
  props: {
    message: {
      type: String,
      default: ''
    },
    show: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const messages = ref([]);
    const newMessage = ref('');
    const isChatVisible = ref(props.show);

     watch(() => props.show, (newVal) => {
        isChatVisible.value = newVal;
        if (newVal && props.message) {
            messages.value.push({ text: props.message, sender: 'ai' });
        }
    });


    const sendMessage = () => {
      if (newMessage.value.trim() !== '') {
        messages.value.push({ text: newMessage.value, sender: 'user' });
        messages.value.push({ text: 'This is a placeholder response.', sender: 'ai' });
        newMessage.value = '';
      }
    };

    const toggleChat = () => {
      isChatVisible.value = !isChatVisible.value;
    };

    return {
      messages,
      newMessage,
      sendMessage,
      isChatVisible,
      toggleChat
    };
  },
};
</script>

<style scoped>
.chatbot-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 300px;
  height: 400px;
}

.chat-header {
  cursor: pointer;
}

.chat-window {
  overflow-y: auto;
}

.user {
  text-align: right;
  color: blue;
}

.ai {
  text-align: left;
  color: green;
}

.chat-icon {
  position: fixed;
  bottom: 20px;
  right: 20px;
  font-size: 36px;
  cursor: pointer;
}
</style>