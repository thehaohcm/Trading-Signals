import axios from 'axios';

export default {
    async getPosts() {
        try {
            const response = await axios.get('/community/posts');
            return response.data;
        } catch (error) {
            console.error('Error fetching posts:', error);
            return [];
        }
    },

    async savePost(post) {
        try {
            const response = await axios.post('/community/posts', post);
            return response.data;
        } catch (error) {
            console.error('Error saving post:', error);
            throw error;
        }
    },

    async deletePost(postId) {
        try {
            await axios.delete(`/community/posts?id=${postId}`);
        } catch (error) {
            console.error('Error deleting post:', error);
            throw error;
        }
    },

    async updatePost(postId, content) {
        try {
            const response = await axios.put(`/community/posts?id=${postId}`, { content });
            return response.data;
        } catch (error) {
            console.error('Error updating post:', error);
            throw error;
        }
    },

    async getComments(postId) {
        try {
            const response = await axios.get(`/community/comments?post_id=${postId}`);
            return response.data;
        } catch (error) {
            console.error(`Error fetching comments for post ${postId}:`, error);
            return [];
        }
    },

    async addComment(comment) {
        try {
            const response = await axios.post('/community/comments', comment);
            return response.data;
        } catch (error) {
            console.error('Error adding comment:', error);
            throw error;
        }
    },

    async deleteComment(commentId) {
        try {
            await axios.delete(`/community/comments?id=${commentId}`);
        } catch (error) {
            console.error('Error deleting comment:', error);
            throw error;
        }
    },

    async updateComment(commentId, content) {
        try {
            const response = await axios.put(`/community/comments?id=${commentId}`, { content });
            return response.data;
        } catch (error) {
            console.error('Error updating comment:', error);
            throw error;
        }
    },

    // Helper to format date relative to now (e.g., "2 hours ago")
    formatTime(dateString) {
        if (!dateString) return '';
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

    // Mock like function (frontend only for now, or update API if needed)
    likePost(postId) {
        // In a real app, this would call an API
        console.log(`Liked post ${postId}`);
        return 1;
    },

    // Tổng hợp & Đúc kết bài học Trading bằng AI từ các bài post
    async generateLessons(posts = null) {
        try {
            let targetPosts = posts;
            if (!targetPosts || targetPosts.length === 0) {
                targetPosts = await this.getPosts();
            }

            if (!targetPosts || targetPosts.length === 0) {
                throw new Error('Chưa có bài viết nào trong cộng đồng để đúc kết bài học.');
            }

            // Lấy tối đa 25 bài post gần nhất có nội dung
            const validPosts = targetPosts.filter(p => p && p.content && p.content.trim().length > 0).slice(0, 25);
            if (validPosts.length === 0) {
                throw new Error('Không có bài viết nào có nội dung hợp lệ để phân tích.');
            }

            const postSummaries = validPosts.map((p, idx) => {
                const author = p.user_name || 'Thành viên';
                const date = p.created_at ? new Date(p.created_at).toLocaleDateString('vi-VN') : '';
                return `[Bài ${idx + 1}] Tác giả: ${author} (${date})\nNội dung: ${p.content.trim()}`;
            }).join('\n\n---\n\n');

            const prompt = `Bạn là Chuyên gia Cố vấn Chiến lược Giao dịch & Quản lý Rủi ro Tài chính (Chief Trading Strategist).

Dưới đây là tập hợp các bài viết, chia sẻ góc nhìn vĩ mô và kinh nghiệm thực chiến từ các trader trong cộng đồng Trading-Signals:

=== DANH SÁCH BÀI VIẾT CỘNG ĐỒNG ===
${postSummaries}

Hãy phân tích, chắt lọc và tổng hợp thành một bản **TỔNG HỢP BÀI HỌC TRADING & GÓC NHÌN CỘNG ĐỒNG** thật súc tích, sâu sắc và có giá trị thực chiến cao theo cấu trúc sau:

1. 🧭 **Tâm Lý & Xu Hướng Thị Trường Chung**: Tổng hợp bức tranh tổng thể và tâm lý cộng đồng đang theo dõi (Vĩ mô, Lãi suất, Cổ phiếu, Crypto, Vàng, Dầu...).
2. 💡 **Các Bài Học & Chiến Lược Đáng Chú Ý**: Rút ra 3-4 bài học đắt giá, luận điểm đầu tư hoặc phương pháp phân tích nổi bật từ các bài chia sẻ.
3. ⚠️ **Cảnh Báo Rủi Ro & Sai Lầm Tiềm Ẩn**: Những rủi ro cần phòng ngừa, bẫy tâm lý (FOMO, bắt dao rơi, nợ margin...) mà cộng đồng cần lưu ý.
4. 🎯 **Khuyến Nghị Hành Động Cho Trader**: Lời khuyên ngắn gọn, thiết thực để áp dụng ngay vào quản lý lệnh và danh mục đầu tư.

Yêu cầu: Trình bày bằng Tiếng Việt với định dạng Markdown chuyên nghiệp, có icon biểu tượng sinh động, bullet points rõ ràng, câu từ chuẩn xác, khách quan.`;

            const response = await axios.post('/api/chat', {
                message: prompt
            });

            return response.data?.response || 'Không thể tạo bản đúc kết từ AI.';
        } catch (error) {
            console.error('Error generating AI lessons:', error);
            throw error;
        }
    }
};
