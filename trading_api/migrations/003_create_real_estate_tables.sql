CREATE TABLE IF NOT EXISTS real_estate_prices (
    id SERIAL PRIMARY KEY,
    region TEXT NOT NULL,
    location TEXT,
    price_text TEXT,      -- Raw price string (e.g. "5 tỷ")
    price_numeric BIGINT, -- Parsed price in VND for charting/sorting
    property_type TEXT,   -- "House", "Land", "Apartment"
    url TEXT,
    fetched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_real_estate_region ON real_estate_prices(region);
CREATE INDEX idx_real_estate_type ON real_estate_prices(property_type);
CREATE INDEX idx_real_estate_fetched_at ON real_estate_prices(fetched_at);
