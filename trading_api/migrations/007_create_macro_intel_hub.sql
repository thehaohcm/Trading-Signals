-- news_groups table
CREATE TABLE IF NOT EXISTS news_groups (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    conclusion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- news_items table
CREATE TABLE IF NOT EXISTS news_items (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES news_groups(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,
    importance INTEGER CHECK (importance BETWEEN 1 AND 5) NOT NULL,
    status VARCHAR(10) CHECK (status IN ('active', 'expired')) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
