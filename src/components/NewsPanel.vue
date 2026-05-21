<template>
  <div class="news-panel" v-if="isVisible">
    <!-- Sticky Glassmorphic Header -->
    <div class="news-panel-header sticky-top">
      <div class="header-top-row d-flex justify-content-between align-items-center mb-3">
        <h5 class="panel-title m-0 d-flex align-items-center gap-2">
          <svg class="title-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v1m2 4a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-1" />
          </svg>
          Trading News
        </h5>
        
        <div class="header-actions d-flex align-items-center gap-2">
          <!-- Speech Synthesis Button -->
          <button 
            class="btn btn-speech d-flex align-items-center" 
            :class="{ active: speechActive, speaking: isSpeaking }"
            @click="toggleSpeech" 
            :title="speechActive ? 'Dừng đọc tin' : 'Nghe tin mới nhất'"
          >
            <svg v-if="!speechActive" class="speech-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
            </svg>
            <svg v-else class="speech-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
            </svg>
            <span class="speech-label ms-1">{{ speechActive ? 'Dừng' : 'Nghe' }}</span>
            
            <!-- Beautiful Soundwave Visualizer -->
            <div v-if="speechActive && isSpeaking" class="speech-soundwave ms-2">
              <span class="sw-bar"></span>
              <span class="sw-bar"></span>
              <span class="sw-bar"></span>
            </div>
          </button>

          <!-- Refresh Button -->
          <button class="btn btn-action" @click="refreshData" title="Làm mới">
            <svg class="action-icon refresh-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M23 4v6h-6"></path>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
          </button>

          <!-- Close Button -->
          <button class="btn btn-action btn-close-custom" @click="togglePanel" title="Đóng">
            <svg class="action-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>

      <!-- Tactile Custom Tabs -->
      <div class="news-tabs-wrapper">
        <div class="news-tabs">
          <button 
            type="button" 
            class="news-tab-btn" 
            :class="{ active: activeTab === 'vnwallstreet' }" 
            @click="switchTab('vnwallstreet')"
          >
            VNWallstreet
          </button>
          <button 
            type="button" 
            class="news-tab-btn" 
            :class="{ active: activeTab === 'tintucvnws' }" 
            @click="switchTab('tintucvnws')"
          >
            TinTucVNWS
          </button>
          <button 
            type="button" 
            class="news-tab-btn" 
            :class="{ active: activeTab === 'ktnews' }" 
            @click="switchTab('ktnews')"
          >
            KTNews
          </button>
        </div>
      </div>

      <!-- Glowing Micro Auto-Refresh Progress Bar -->
      <div class="progress-bar-container">
        <div class="refresh-progress-bar" :style="{ width: (countdown / 30 * 100) + '%' }"></div>
      </div>
    </div>
    
    <!-- News Content Section -->
    <div class="news-panel-content p-3">
      <!-- Live Status Badge Row -->
      <div class="news-meta-row d-flex justify-content-between align-items-center mb-3">
        <span class="live-indicator d-flex align-items-center gap-2">
          <span class="live-dot"></span>
          <span class="live-text">Live Feed</span>
        </span>
        <span class="countdown-badge">Auto-refresh in <strong class="text-neon">{{ countdown }}s</strong></span>
      </div>

      <!-- News Items List -->
      <ul class="list-unstyled m-0">
        <li v-for="(item, index) in newsItems" :key="index" class="mb-4">
          <div ref="newsCard" class="card news-card border-0" :class="{ 'reading-border': speechActive && currentlyReadingIndex === index && activeTab === currentSpeakingTab }">
            <!-- Image Section with glowing overlay -->
            <div class="card-img-wrapper" v-if="item.imageUrl">
              <img :src="item.imageUrl" class="card-img-top" alt="News Image">
              <div class="card-img-glow"></div>
            </div>
            
            <div class="card-body p-3">
              <!-- Content description -->
              <div class="card-text text-secondary mb-3 small" :class="{'text-truncate-3': !expandedItems[index]}">
                <span v-if="!expandedItems[index]" v-html="item.truncated"></span>
                <span v-else v-html="item.description"></span>
              </div>

              <!-- Footer with time and read more -->
              <div class="card-footer-row d-flex justify-content-between align-items-center mt-2">
                <small class="news-date d-flex align-items-center gap-1">
                  <svg class="clock-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 14px; height: 14px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {{ formatDate(item.date_published) }}
                </small>
                
                <div class="d-flex align-items-center gap-2">
                  <!-- Individual Speech Button -->
                  <button 
                    @click.stop="toggleArticleSpeech(item, index)"
                    class="btn btn-expand p-0 z-index-top d-inline-flex align-items-center gap-1 me-2"
                    :title="speechActive && currentlyReadingIndex === index && activeTab === currentSpeakingTab ? 'Dừng đọc' : 'Đọc tin này'"
                  >
                    <svg v-if="!(speechActive && currentlyReadingIndex === index && activeTab === currentSpeakingTab)" class="speech-icon-small" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="width: 14px; height: 14px;">
                      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></polygon>
                      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
                    </svg>
                    <svg v-else class="speech-icon-small text-danger animate-pulse-speech" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="width: 14px; height: 14px;">
                      <rect x="4" y="4" width="16" height="16" rx="2" ry="2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></rect>
                    </svg>
                  </button>

                  <button v-if="item.description.length > 200" 
                          @click.stop="toggleExpand(index)" 
                          class="btn btn-expand p-0 z-index-top d-inline-flex align-items-center gap-1">
                    <span>{{ expandedItems[index] ? 'Thu gọn' : 'Đọc thêm' }}</span>
                    <svg class="chevron-icon" :class="{ 'rotate-180': expandedItems[index] }" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 12px; height: 12px;">
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                  </button>
                </div>
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
      ktnewsNews: [],
      lastReadTitles: { vnwallstreet: '', tintucvnws: '', ktnews: '' },
      currentlyReadingIndex: 0,
      currentSpeakingTab: '',
      currentUtterance: null,
      
      // Playlist and sentence queue properties
      speechQueue: [],
      currentQueueIndex: 0,
      articleSentences: [],
      currentSentenceIndex: 0,
    };
  },
  created() {
    this.fetchData();
    this.startCountdown();
    this.loadSpeechVoices();
  },
  beforeUnmount() {
    clearInterval(this.intervalId);
    this.stopSpeech();
  },
  methods: {
    switchTab(tab) {
        this.activeTab = tab;
        this.expandedItems = []; // Reset expanded status of cards on tab changes
        
        if (tab === 'vnwallstreet') {
          this.newsItems = this.vnwallstreetNews;
        } else if (tab === 'tintucvnws') {
          this.newsItems = this.tintucvnwsNews;
        } else {
          this.newsItems = this.ktnewsNews;
        }
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

        const resKt = await fetch('/api/news/ktnews24');
        const xmlTextKt = await resKt.text();
        const parsedKt = this.parseXml(xmlTextKt);
        this.ktnewsNews = parsedKt;

        if (this.activeTab === 'vnwallstreet') {
          this.newsItems = parsedVn;
        } else if (this.activeTab === 'tintucvnws') {
          this.newsItems = parsedTin;
        } else {
          this.newsItems = parsedKt;
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
        const expanded = !this.expandedItems[index];
        this.expandedItems[index] = expanded;
        this.expandedItems = [...this.expandedItems]; // Trigger Vue reactivity
    },
    toggleSpeech() {
      if (this.speechActive) {
        this.stopSpeech();
      } else {
        this.startSpeechQueue();
      }
    },
    toggleArticleSpeech(item, index) {
      // If we are currently reading this exact article in the active tab, stop speech.
      if (this.speechActive && this.currentlyReadingIndex === index && this.activeTab === this.currentSpeakingTab) {
        this.stopSpeech();
        return;
      }
      
      // Otherwise, stop any current speech and start reading this single article
      this.stopSpeech();
      
      this.speechQueue = [{
        article: item,
        tab: this.activeTab,
        index: index
      }];
      
      this.speechActive = true;
      this.currentQueueIndex = 0;
      this.currentlyReadingIndex = index;
      this.currentSpeakingTab = this.activeTab;
      
      try {
        speechSynthesis.cancel();
      } catch (e) {
        console.error(e);
      }
      
      setTimeout(() => {
        if (this.speechActive) {
          this.speakQueueItem();
        }
      }, 100);
    },
    startSpeechQueue() {
      this.speechQueue = [];
      this.currentSpeakingTab = '';
      
      if (this.vnwallstreetNews && this.vnwallstreetNews.length > 0) {
        this.speechQueue.push({
          article: this.vnwallstreetNews[0],
          tab: 'vnwallstreet',
          index: 0
        });
      }
      
      if (this.tintucvnwsNews && this.tintucvnwsNews.length > 0) {
        this.speechQueue.push({
          article: this.tintucvnwsNews[0],
          tab: 'tintucvnws',
          index: 0
        });
      }
      
      if (this.ktnewsNews && this.ktnewsNews.length > 0) {
        this.speechQueue.push({
          article: this.ktnewsNews[0],
          tab: 'ktnews',
          index: 0
        });
      }
      
      if (this.speechQueue.length === 0) {
        alert('Không có tin tức mới nào để phát.');
        return;
      }
      
      this.speechActive = true;
      this.currentQueueIndex = 0;
      this.currentlyReadingIndex = 0;
      
      try {
        speechSynthesis.cancel();
      } catch (e) {
        console.error(e);
      }
      
      setTimeout(() => {
        if (this.speechActive) {
          this.speakQueueItem();
        }
      }, 100);
    },
    stopSpeech() {
      this.speechActive = false;
      this.isSpeaking = false;
      this.speechQueue = [];
      this.currentQueueIndex = 0;
      this.articleSentences = [];
      this.currentSentenceIndex = 0;
      this.currentlyReadingIndex = 0;
      this.currentSpeakingTab = '';
      this.expandedItems = []; // Collapse all cards when stopping speech
      
      if (this.currentUtterance) {
        this.currentUtterance.onstart = null;
        this.currentUtterance.onend = null;
        this.currentUtterance.onerror = null;
        this.currentUtterance = null;
      }
      
      try {
        speechSynthesis.cancel();
      } catch (e) {
        console.error('Error cancelling speech synthesis:', e);
      }
    },
    speakQueueItem() {
      if (!this.speechActive) return;
      if (this.currentQueueIndex >= this.speechQueue.length) {
        this.stopSpeech();
        return;
      }
      
      const item = this.speechQueue[this.currentQueueIndex];
      const article = item.article;
      const tab = item.tab;
      
      // Auto switch active tab to match the currently spoken article
      this.activeTab = tab;
      this.currentSpeakingTab = tab;
      this.expandedItems = [];
      if (tab === 'vnwallstreet') {
        this.newsItems = this.vnwallstreetNews;
      } else if (tab === 'tintucvnws') {
        this.newsItems = this.tintucvnwsNews;
      } else {
        this.newsItems = this.ktnewsNews;
      }
      
      this.currentlyReadingIndex = item.index !== undefined ? item.index : 0;
      this.expandedItems = [];
      this.expandedItems[this.currentlyReadingIndex] = true; // Auto-expand the currently spoken article card
      this.expandedItems = [...this.expandedItems]; // Force Vue reactivity trigger
      
      this.lastReadTitles[tab] = article.title;
      this.isSpeaking = true;
      
      // Scroll the expanded active card smoothly into view
      this.$nextTick(() => {
        const cardElements = this.$refs.newsCard;
        if (cardElements && cardElements[this.currentlyReadingIndex]) {
          cardElements[this.currentlyReadingIndex].scrollIntoView({
            behavior: 'smooth',
            block: 'nearest'
          });
        }
      });
      
      const rawText = article.title + '. ' + article.description;
      const cleanText = this.cleanSpeechText(rawText);
      this.articleSentences = this.splitIntoSentences(cleanText);
      this.currentSentenceIndex = 0;
      
      if (this.articleSentences.length === 0) {
        this.nextQueueItem();
        return;
      }
      
      this.speakSentence();
    },
    speakSentence() {
      if (!this.speechActive) return;
      
      if (this.currentSentenceIndex >= this.articleSentences.length) {
        this.nextQueueItem();
        return;
      }
      
      const sentence = this.articleSentences[this.currentSentenceIndex];
      
      if (this.currentUtterance) {
        this.currentUtterance.onstart = null;
        this.currentUtterance.onend = null;
        this.currentUtterance.onerror = null;
      }
      
      const utterance = new SpeechSynthesisUtterance(sentence);
      this.currentUtterance = utterance;
      
      utterance.rate = 1.35; 
      utterance.pitch = 1.0;
      
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
        this.currentUtterance = null;
        if (this.speechActive) {
          this.currentSentenceIndex++;
          setTimeout(() => {
            if (this.speechActive) {
              this.speakSentence();
            }
          }, 250);
        }
      };
      
      utterance.onerror = (e) => {
        console.error('Speech synthesis sentence error:', e);
        this.currentUtterance = null;
        if (this.speechActive) {
          this.currentSentenceIndex++;
          setTimeout(() => {
            if (this.speechActive) {
              this.speakSentence();
            }
          }, 200);
        }
      };
      
      speechSynthesis.speak(utterance);
    },
    nextQueueItem() {
      if (!this.speechActive) return;
      
      this.currentQueueIndex++;
      if (this.currentQueueIndex < this.speechQueue.length) {
        setTimeout(() => {
          if (this.speechActive) {
            this.speakQueueItem();
          }
        }, 1500);
      } else {
        this.stopSpeech();
      }
    },
    splitIntoSentences(text) {
      if (!text) return [];
      const sentences = [];
      const regex = /[^.?!;\n]+[.?!;\n]*/g;
      let match;
      while ((match = regex.exec(text)) !== null) {
        const sentence = match[0].trim();
        if (sentence.length > 0) {
          sentences.push(sentence);
        }
      }
      return sentences.length > 0 ? sentences : [text];
    },
    stripHtml(html) {
      const tmp = document.createElement('DIV');
      tmp.innerHTML = html;
      return tmp.textContent || tmp.innerText || '';
    },
    cleanSpeechText(text) {
      if (!text) return '';
      let clean = this.stripHtml(text);
      
      clean = clean.replace(/[⭐★☆]+/g, '');
      clean = clean.replace(/[\uD800-\uDBFF][\uDC00-\uDFFF]/g, ''); 
      clean = clean.replace(/[\u2600-\u27BF]/g, ''); 
      clean = clean.replace(/[▫▪•■□▲▼►◄◆◇○●®™©]/g, '');
      
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
/* ── News Panel Shell ────────────────────────────────────── */
.news-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 420px;
  max-width: 100vw;
  height: 100vh;
  background: linear-gradient(180deg, rgba(13, 16, 27, 0.96) 0%, rgba(22, 25, 38, 0.98) 100%);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: -10px 0 40px rgba(0, 0, 0, 0.6);
  overflow-y: auto;
  z-index: 1101;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #f8fafc;
}

/* Custom Scrollbar */
.news-panel::-webkit-scrollbar {
  width: 6px;
}
.news-panel::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.01);
}
.news-panel::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 3px;
  transition: background 0.2s;
}
.news-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* ── Sticky Header ────────────────────────────────────── */
.news-panel-header {
  background: rgba(13, 16, 27, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding: 1.25rem 1.25rem 0 1.25rem;
  z-index: 10;
}

.panel-title {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: #f8fafc;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.title-icon {
  width: 20px;
  height: 20px;
  color: #ff4757;
  filter: drop-shadow(0 0 6px rgba(255, 71, 87, 0.4));
}

/* Action buttons */
.btn-speech {
  background: rgba(99, 179, 237, 0.12);
  border: 1px solid rgba(99, 179, 237, 0.25);
  border-radius: 30px;
  color: #63b3ed;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 6px 14px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}
.btn-speech:hover {
  background: rgba(99, 179, 237, 0.2);
  border-color: rgba(99, 179, 237, 0.4);
  color: #90cdf4;
  transform: translateY(-1px);
}
.btn-speech.active {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.3) 100%);
  border-color: rgba(239, 68, 68, 0.4);
  color: #f87171;
}
.btn-speech.speaking {
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.25);
}

.speech-icon {
  width: 14px;
  height: 14px;
}

.speech-label {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Soundwave visualizer */
.speech-soundwave {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 10px;
}
.sw-bar {
  display: inline-block;
  width: 2px;
  height: 100%;
  background-color: currentColor;
  border-radius: 1px;
  animation: bounce 0.8s ease-in-out infinite alternate;
}
.sw-bar:nth-child(2) {
  animation-delay: 0.15s;
}
.sw-bar:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes bounce {
  0% { height: 2px; }
  100% { height: 10px; }
}

.btn-action {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 50%;
  color: #94a3b8;
  width: 32px;
  height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}
.btn-action:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
  color: #f8fafc;
  transform: translateY(-1px);
}
.btn-close-custom:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.25);
  color: #f87171;
}

.action-icon {
  width: 16px;
  height: 16px;
}
.refresh-icon:hover {
  animation: spin 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

/* ── Custom Tabs ────────────────────────────────────── */
.news-tabs-wrapper {
  margin-top: 1rem;
  margin-bottom: 0.75rem;
}

.news-tabs {
  display: flex;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 4px;
  gap: 2px;
}

.news-tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #94a3b8;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 8px 4px;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  text-align: center;
  white-space: nowrap;
}
.news-tab-btn:hover {
  color: #f8fafc;
  background: rgba(255, 255, 255, 0.03);
}
.news-tab-btn.active {
  background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(255, 71, 87, 0.35);
}

/* ── Auto-Refresh Progress Bar ────────────────────────────────────── */
.progress-bar-container {
  height: 2px;
  background: rgba(255, 255, 255, 0.02);
  width: calc(100% + 2.5rem);
  margin-left: -1.25rem;
  overflow: hidden;
  position: relative;
}

.refresh-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #ff4757, #ff6b81);
  box-shadow: 0 0 6px rgba(255, 71, 87, 0.6);
  transition: width 1s linear;
}

/* ── Live / Meta Row ────────────────────────────────────── */
.news-meta-row {
  margin-top: 0.5rem;
}

.live-indicator {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.15);
  border-radius: 20px;
  padding: 4px 10px;
}

.live-dot {
  width: 6px;
  height: 6px;
  background-color: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 8px #10b981;
  animation: pulse-live 1.5s infinite alternate;
}

@keyframes pulse-live {
  0% { opacity: 0.4; transform: scale(0.9); }
  100% { opacity: 1; transform: scale(1.1); }
}

.live-text {
  color: #34d399;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.countdown-badge {
  color: #64748b;
  font-size: 0.75rem;
}
.text-neon {
  color: #ff4757;
  text-shadow: 0 0 4px rgba(255, 71, 87, 0.2);
}

/* ── News Cards ────────────────────────────────────── */
.news-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05) !important;
  border-radius: 16px !important;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}
.news-card:hover {
  transform: translateY(-3px);
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.1) !important;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
}

/* Highlight border for card currently being read */
.reading-border {
  border: 1px solid rgba(99, 179, 237, 0.4) !important;
  box-shadow: 0 0 15px rgba(99, 179, 237, 0.15), 0 4px 20px rgba(0, 0, 0, 0.15) !important;
  background: rgba(99, 179, 237, 0.02) !important;
}

.card-img-wrapper {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%; /* 16:9 */
  overflow: hidden;
  background-color: rgba(255, 255, 255, 0.01);
}

.card-img-top {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.news-card:hover .card-img-top {
  transform: scale(1.05);
}

.card-img-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, transparent 60%, rgba(13, 16, 27, 0.85) 100%);
  pointer-events: none;
}

.card-text {
  color: #cbd5e1 !important;
  line-height: 1.55;
  font-size: 0.85rem !important;
}

/* Custom styling for parsed telegram HTML inside card content */
.card-text :deep(a) {
  color: #63b3ed;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.15s ease;
}
.card-text :deep(a):hover {
  color: #90cdf4;
  text-decoration: underline;
}

.card-text :deep(br) {
  margin-bottom: 6px;
}

.text-truncate-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Footer Section */
.news-date {
  color: #64748b;
  font-size: 0.75rem;
}
.clock-icon {
  width: 13px;
  height: 13px;
  color: rgba(255, 255, 255, 0.25);
}

.btn-expand {
  background: transparent;
  border: none;
  color: #63b3ed;
  font-size: 0.8rem;
  font-weight: 600;
  transition: all 0.2s ease;
}
.btn-expand:hover {
  color: #90cdf4;
  transform: translateX(1px);
}

.chevron-icon {
  width: 12px;
  height: 12px;
  transition: transform 0.25s ease;
}
.rotate-180 {
  transform: rotate(180deg);
}

.z-index-top {
  position: relative;
  z-index: 2;
}

.speech-icon-small {
  color: #63b3ed;
  transition: all 0.2s ease;
}
.speech-icon-small:hover {
  color: #90cdf4;
  transform: scale(1.1);
}
.animate-pulse-speech {
  animation: pulse-speech 1.2s infinite alternate;
}
@keyframes pulse-speech {
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(1.15); opacity: 1; filter: drop-shadow(0 0 4px rgba(239, 68, 68, 0.6)); }
}

/* Smooth layout animation */
.news-panel-content ul {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>