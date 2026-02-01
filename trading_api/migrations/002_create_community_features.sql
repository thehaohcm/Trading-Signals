CREATE TABLE IF NOT EXISTS public.community_posts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    user_name VARCHAR NOT NULL,
    user_code VARCHAR NOT NULL,
    content TEXT NOT NULL,
    image TEXT, -- Base64 encoded image or URL
    likes INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_community_posts_created_at ON community_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_community_posts_user_id ON community_posts(user_id);

CREATE TABLE IF NOT EXISTS public.community_comments (
    id SERIAL PRIMARY KEY,
    post_id INT NOT NULL,
    user_id VARCHAR NOT NULL,
    user_name VARCHAR NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_post
      FOREIGN KEY(post_id) 
      REFERENCES community_posts(id)
      ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_community_comments_post_id ON community_comments(post_id);
