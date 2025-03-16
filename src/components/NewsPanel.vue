<template>
  <div class="news-panel" v-if="isVisible">
    <div class="news-panel-header bg-light border-bottom p-3 d-flex justify-content-between align-items-center">
      <h2 class="mb-0">🔴 Latest News</h2>
      <div>
        <button class="btn btn-primary" @click="refreshData" title="Refresh">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" style="width: 20px; height: 20px;">
            <path fill-rule="evenodd" d="M4.755 10.059a7.5 7.5 0 0 1 12.548-3.364l1.903 1.903h-3.183a.75.75 0 1 0 0 1.5h4.992a.75.75 0 0 0 .75-.75V4.356a.75.75 0 0 0-1.5 0v3.18l-1.9-1.9A9 9 0 0 0 3.306 9.67a.75.75 0 1 0 1.45.388Zm14.54 3.364a.75.75 0 1 0-1.449-.388A9 9 0 0 0 20.694 14.33l-1.902-1.903h3.183a.75.75 0 0 0 0-1.5H19.008a.75.75 0 0 0-.75.75v4.992a.75.75 0 0 0 1.5 0v-3.18l1.9 1.9a7.5 7.5 0 0 1-12.548 3.364Z" clip-rule="evenodd" />
          </svg>
        </button>
        <button class="btn btn-secondary me-2" @click="togglePanel" title="Close">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 20px; height: 20px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L21 21" />
          </svg>
        </button>
      </div>
    </div>
    <div class="border-bottom">
      <p class="mb-1">Refresh in {{ countdown }}s</p>
    </div>
    <div class="news-panel-content p-3" style="font-family: 'Times New Roman', serif; font-size: 15px;">
      <ul class="list-unstyled">
        <li v-for="(item, index) in newsItems" :key="index" class="mb-3">
          <div class="card">
            <img v-if="item.imageUrl" :src="item.imageUrl" class="card-img-top" alt="News Image">
            <div class="card-body">
              <div v-if="!expandedItems[index]" v-html="item.truncated"></div>
              <div v-else v-html="item.description"></div>
              <button v-if="item.description.length > 200" @click="toggleExpand(index)" class="btn btn-link btn-sm">
                {{ expandedItems[index] ? 'Collapse' : 'Expand' }}
              </button>
              <p class="card-text"><small class="text-muted">Published: {{ formatDate(item.date_published) }}</small></p>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NewsPanel',
  props: {
    isVisible: Boolean,
  },
  data() {
    return {
      newsItems: [],
      countdown: 30,
      intervalId: null,
      expandedItems: [], // Keep track of expanded state per item
    };
  },
  created() {
    this.fetchData();
    this.startCountdown();
  },
  beforeUnmount() {
    clearInterval(this.intervalId);
  },
  methods: {
    async fetchData() {
      try {
        const response = await fetch('/api/news');
        const xmlText = await response.text();
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlText, 'text/xml');
        const items = Array.from(xmlDoc.querySelectorAll('item')).slice(0, 10);

        this.newsItems = items.map(item => {
          const title = item.querySelector('title').textContent;
          const link = item.querySelector('link').textContent;
          let description = item.querySelector('description').textContent;

          // Extract image URL
          let imageUrl = null;
          const mediaContent = item.querySelector('media\\:content, content'); // Select both media:content and standard content
            if (mediaContent && mediaContent.getAttribute('medium') === 'image') {
                imageUrl = mediaContent.getAttribute('url');
            } else {
                const imgTag = description.match(/<img[^>]+src="([^">]+)"/);
                if (imgTag) {
                    imageUrl = imgTag[1];
                }
            }

          // Remove <img> tag from description
          description = description.replace(/<img[^>]+>/, '');

          return {
            title,
            link,
            description,
            imageUrl,
            date_published: item.querySelector('pubDate').textContent,
            content_html: description, // still keep this for consistency
            truncated: description.substring(0, 200) + (description.length > 200 ? '...' : ''),
            expanded: false,
          };
        });
      } catch (error) {
        console.error('Error fetching news data:', error);
        // Handle error appropriately, e.g., display an error message
      }
    },
    refreshData() {
      this.fetchData();
      this.countdown = 30; // Reset countdown on manual refresh
    },
    startCountdown() {
      this.intervalId = setInterval(() => {
        this.countdown--;
        if (this.countdown <= 0) {
          this.refreshData();
        }
      }, 1000);
    },
    togglePanel() {
      this.$emit('toggle');
    },
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleString(); // Or any other desired format
    },
     toggleExpand(index) {
        this.expandedItems[index] = !this.expandedItems[index];
    },
  },
};
</script>

<style scoped>
.news-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px; /* Adjust width as needed */
  height: 100vh;
  background-color: white;
  border-left: 1px solid #ccc;
  overflow-y: auto;
  z-index: 1000;
}
</style>