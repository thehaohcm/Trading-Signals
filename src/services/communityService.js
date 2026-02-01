const POSTS_KEY = 'community_posts';

export default {
    getPosts() {
        const postsJson = localStorage.getItem(POSTS_KEY);
        return postsJson ? JSON.parse(postsJson) : [];
    },

    savePost(post) {
        const posts = this.getPosts();
        // Add new post to the beginning
        const newPost = {
            ...post,
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
            likes: 0,
            comments: 0
        };
        posts.unshift(newPost);
        localStorage.setItem(POSTS_KEY, JSON.stringify(posts));
        return newPost;
    },

    deletePost(postId) {
        let posts = this.getPosts();
        posts = posts.filter(p => p.id !== postId);
        localStorage.setItem(POSTS_KEY, JSON.stringify(posts));
    },

    // Helper to format date relative to now (e.g., "2 hours ago")
    formatTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + " years ago";
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + " months ago";
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + " days ago";
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + " hours ago";
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + " minutes ago";
        return Math.floor(seconds) + " seconds ago";
    },

    // Mock like function
    likePost(postId) {
        const posts = this.getPosts();
        const post = posts.find(p => p.id === postId);
        if (post) {
            post.likes = (post.likes || 0) + 1;
            localStorage.setItem(POSTS_KEY, JSON.stringify(posts));
            return post.likes;
        }
        return 0;
    }
};
