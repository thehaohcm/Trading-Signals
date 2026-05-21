<template>
  <div class="news-panel" v-if="isVisible">
    <div class="news-panel-header bg-white border-bottom p-3 d-flex justify-content-between align-items-center sticky-top shadow-sm">
      <div class="d-flex align-items-center">
         <div class="btn-group me-3" role="group">
            <button type="button" class="btn btn-sm" :class="activeTab === 'vnwallstreet' ? 'btn-danger' : 'btn-outline-danger'" @click="switchTab('vnwallstreet')">VNWallstreet</button>
            <button type="button" class="btn btn-sm" :class="activeTab === 'tintucvnws' ? 'btn-danger' : 'btn-outline-danger'" @click="switchTab('tintucvnws')">TinTucVNWS</button>
         </div>
      </div>
      <div class="d-flex align-items-center">
        <button 
          class="btn btn-sm me-2 d-flex align-items-center" 
          :class="speechActive ? 'btn-outline-danger' : 'btn-outline-primary'"
          @click="toggleSpeech" 
          :title="speechActive ? 'Dừng đọc tin' : 'Nghe tin mới nhất'"
        >
          <svg v-if="!speechActive" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 18px; height: 18px; margin-right: 6px;">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 18px; height: 18px; margin-right: 6px;">
            <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
          </svg>
          {{ speechActive ? 'Dừng' : 'Nghe' }}
        </button>
        <button class="btn btn-icon me-2" @click="refreshData" title="Refresh">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 20px; height: 20px;">
            <path d="M23 4v6h-6"></path>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
          </svg>
        </button>
        <button class="btn btn-icon" @click="togglePanel" title="Close">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px;">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    </div>
    
    <div class="news-panel-content p-3">
       <div class="d-flex justify-content-between align-items-center mb-3">
          <small class="text-muted">Auto-refresh in {{ countdown }}s</small>
          <span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2">Live</span>
       </div>

      <ul class="list-unstyled">
        <li v-for="(item, index) in newsItems" :key="index" class="mb-4">
          <div class="card news-card border-0 shadow-sm h-100">
            <div class="card-img-wrapper" v-if="item.imageUrl">
                 <img :src="item.imageUrl" class="card-img-top" alt="News Image">
            </div>
            
            <div class="card-body">
              <div class="card-text text-secondary mb-3 small" :class="{'text-truncate-3': !expandedItems[index]}">
                   <span v-if="!expandedItems[index]" v-html="item.truncated"></span>
                   <span v-else v-html="item.description"></span>
              </div>

               <div class="d-flex justify-content-between align-items-center mt-2">
                   <small class="text-muted d-flex align-items-center gap-1">
                       <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 14px; height: 14px;">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                       {{ formatDate(item.date_published) }}
                   </small>
                   
                   <button v-if="item.description.length > 200" 
                           @click.stop="toggleExpand(index)" 
                           class="btn btn-link btn-sm p-0 text-primary text-decoration-none z-index-top">
                     {{ expandedItems[index] ? 'Show less' : 'Read more' }}
                   </button>
               </div>
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
      expandedItems: [], 
      activeTab: 'vnwallstreet',
      isSpeaking: false,
      availableVoices: [],
      speechActive: false,
      vnwallstreetNews: [],
      tintucvnwsNews: [],
      lastReadTitles: { vnwallstreet: '', tintucvnws: '' },
    };
  },
  created() {
    this.fetchData();
    this.startCountdown();
    this.loadSpeechVoices();
  },
  beforeUnmount() {
    clearInterval(this.intervalId);
    speechSynthesis.cancel();
  },
  methods: {
    switchTab(tab) {
        this.activeTab = tab;
        this.newsItems = tab === 'vnwallstreet' ? this.vnwallstreetNews : this.tintucvnwsNews;
    },
    parseXml(xmlText) {
      try {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlText, 'text/xml');
        const items = Array.from(xmlDoc.querySelectorAll('item')).slice(0, 15);

        return items.map(item => {
          const title = item.querySelector('title')?.textContent || '';
          const link = item.querySelector('link')?.textContent || '';
          let description = item.querySelector('description')?.textContent || '';

          let imageUrl = null;
          const mediaContent = item.querySelector('media\\:content, content');
          if (mediaContent && mediaContent.getAttribute('medium') === 'image') {
              imageUrl = mediaContent.getAttribute('url');
          } else {
              const imgTag = description.match(/<img[^>]+src="([^">]+)"/);
              if (imgTag) {
                  imageUrl = imgTag[1];
              }
          }
          
          description = description.replace(/<img[^>]+>/g, '').replace(/^(<br\s*\/?>\s*)+/i, '');

          return {
            title,
            link,
            description,
            imageUrl,
            date_published: item.querySelector('pubDate')?.textContent || '',
            content_html: description,
            truncated: description.substring(0, 200) + (description.length > 200 ? '...' : ''),
            expanded: false,
          };
        });
      } catch (e) {
        console.error('Error parsing XML:', e);
        return [];
      }
    },
    async fetchData() {
       try {
        const resVn = await fetch('/api/news/vnwallstreet');
        const xmlTextVn = await resVn.text();
        const parsedVn = this.parseXml(xmlTextVn);
        this.vnwallstreetNews = parsedVn;

        const resTin = await fetch('/api/news/tintucvnws');
        const xmlTextTin = await resTin.text();
        const parsedTin = this.parseXml(xmlTextTin);
        this.tintucvnwsNews = parsedTin;

        const isNewVn = parsedVn.length > 0 && parsedVn[0].title !== this.lastReadTitles.vnwallstreet;
        const isNewTin = parsedTin.length > 0 && parsedTin[0].title !== this.lastReadTitles.tintucvnws;

        this.newsItems = this.activeTab === 'vnwallstreet' ? parsedVn : parsedTin;

        if (this.speechActive && !speechSynthesis.speaking && !speechSynthesis.pending) {
          if (this.activeTab === 'vnwallstreet' && isNewVn) {
            this.speakArticle(parsedVn[0], 'vnwallstreet');
          } else if (this.activeTab === 'tintucvnws' && isNewTin) {
            this.speakArticle(parsedTin[0], 'tintucvnws');
          } else if (isNewVn) {
            this.speakArticle(parsedVn[0], 'vnwallstreet');
          } else if (isNewTin) {
            this.speakArticle(parsedTin[0], 'tintucvnws');
          }
        }
      } catch (error) {
        console.error('Error fetching news data:', error);
      }
    },
    refreshData() {
      this.fetchData();
      this.countdown = 30; 
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
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHrs = Math.floor(diffMins / 60);
      
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHrs < 24) return `${diffHrs}h ago`;
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    },
    loadSpeechVoices() {
      const updateVoices = () => {
        this.availableVoices = speechSynthesis.getVoices();
      };

      updateVoices();
      if ('onvoiceschanged' in speechSynthesis) {
        speechSynthesis.onvoiceschanged = updateVoices;
      }
    },
    getVietnameseVoice() {
      const voices = this.availableVoices.length > 0 ? this.availableVoices : speechSynthesis.getVoices();
      return voices.find(voice => {
        const normalized = `${voice.lang} ${voice.name} ${voice.voiceURI}`.toLowerCase();
        return /\bvi\b|vi-vn|vi_vn|vietnamese|việt|viet/.test(normalized);
      }) || null;
    },
    toggleExpand(index) {
        this.expandedItems[index] = !this.expandedItems[index];
    },
    toggleSpeech() {
      if (this.speechActive) {
        this.speechActive = false;
        if (speechSynthesis.speaking || speechSynthesis.pending) {
          speechSynthesis.cancel();
        }
        this.isSpeaking = false;
      } else {
        this.speechActive = true;
        const currentNewsList = this.activeTab === 'vnwallstreet' ? this.vnwallstreetNews : this.tintucvnwsNews;
        const latestArticle = currentNewsList[0];
        if (latestArticle) {
          this.speakArticle(latestArticle, this.activeTab);
        } else {
          alert('Không có tin tức nào để phát.');
          this.speechActive = false;
        }
      }
    },
    speakArticle(article, tab) {
      if (!article) return;

      if (speechSynthesis.speaking || speechSynthesis.pending) {
        speechSynthesis.cancel();
      }

      this.lastReadTitles[tab] = article.title;
      this.isSpeaking = true;

      const text = this.cleanSpeechText(article.title + '. ' + article.description);
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.3; 
      utterance.pitch = 1;

      const vietnameseVoice = this.getVietnameseVoice();
      if (vietnameseVoice) {
        utterance.voice = vietnameseVoice;
        utterance.lang = vietnameseVoice.lang || 'vi-VN';
      } else {
        utterance.lang = 'vi-VN';
      }

      utterance.onstart = () => {
        this.isSpeaking = true;
      };
      utterance.onend = () => {
        this.isSpeaking = false;
        if (this.speechActive) {
          const otherTab = tab === 'vnwallstreet' ? 'tintucvnws' : 'vnwallstreet';
          const otherNewsList = otherTab === 'vnwallstreet' ? this.vnwallstreetNews : this.tintucvnwsNews;
          const otherLatestArticle = otherNewsList[0];

          if (otherLatestArticle && otherLatestArticle.title !== this.lastReadTitles[otherTab]) {
            setTimeout(() => {
              if (this.speechActive) {
                this.speakArticle(otherLatestArticle, otherTab);
              }
            }, 1000); 
          }
        }
      };
      utterance.onerror = () => {
        this.isSpeaking = false;
      };

      speechSynthesis.speak(utterance);
    },
    stripHtml(html) {
      const tmp = document.createElement('DIV');
      tmp.innerHTML = html;
      return tmp.textContent || tmp.innerText || '';
    },
    cleanSpeechText(text) {
      if (!text) return '';
      // Strip HTML first
      let clean = this.stripHtml(text);
      
      // Remove star rating blocks like "⭐⭐⭐☆☆" or "⭐⭐⭐⭐⭐"
      clean = clean.replace(/[⭐★☆]+/g, '');
      
      // Remove specific emojis and symbols commonly found in news feeds
      // This includes 🔴, 🟢, 🟡, 🔵, ▫️, ▪️, 🔸, 🔹, ⚡, 🔥, 📣, 🔔, etc.
      clean = clean.replace(/[\uD800-\uDBFF][\uDC00-\uDFFF]/g, ''); // Emojis (including country flags)
      clean = clean.replace(/[\u2600-\u27BF]/g, ''); // Miscellaneous symbols and dingbats (stars, arrows, etc.)
      
      // Strip other common bullet-point symbols that might not be in the emoji range
      clean = clean.replace(/[▫▪•■□▲▼►◄◆◇○●®™©]/g, '');
      
      // Clean up double spaces or spaces before punctuation
      clean = clean
        .replace(/\s+/g, ' ')
        .replace(/\s+([.,;:?!])/g, '$1')
        .trim();
        
      return clean;
    }
  },
};
</script>

<style scoped>
.news-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  max-width: 100vw;
  height: 100vh;
  background-color: #f8f9fa; /* Light gray background */
  box-shadow: -5px 0 25px rgba(0,0,0,0.1);
  overflow-y: auto;
  z-index: 1101;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  transition: transform 0.3s ease-in-out;
}

/* Custom Scrollbar */
.news-panel::-webkit-scrollbar {
  width: 6px;
}
.news-panel::-webkit-scrollbar-track {
  background: #f1f1f1;
}
.news-panel::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}
.news-panel::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.card-img-wrapper {
    position: relative;
    width: 100%;
    height: 0;
    padding-bottom: 56.25%; /* 16:9 Aspect Ratio */
    overflow: hidden;
    background-color: #e9ecef;
}

.card-img-top {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
}

.news-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    overflow: hidden;
}

.news-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 .5rem 1rem rgba(0,0,0,.15)!important;
}

.news-card:hover .card-img-top {
    transform: scale(1.05);
}

.text-truncate-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* Ensure read more button stays clickable and above stretched link if we used it, 
   but here we use scoped link for title so button works naturally. 
   Currently title is not a stretched link for the whole card to allow selecting text. 
   If we wanted whole card clickable we would need stretched-link on title 
   and position: relative; z-index: 2 on the button. */
   
.z-index-top {
    position: relative;
    z-index: 2;
}

.btn-icon {
  background: transparent;
  border: none;
  border-radius: 50%;
  padding: 8px;
  color: #6c757d;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon:hover {
  background-color: #f1f3f5; /* Light gray hover */
  color: #212529;
  transform: rotate(90deg); /* Playful rotation for close/refresh */
}

/* Specific hover for refresh to rotate fully */
.btn-icon[title="Refresh"]:hover svg {
  animation: spin 1s linear infinite;
  transform: none; /* Override general hover transform */
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>