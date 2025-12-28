CREATE TABLE public.cryptos_watchlist (
	crypto varchar NOT NULL,
	is_ath bool NOT NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT cryptos_watchlist_pkey PRIMARY KEY (crypto)
);

CREATE TABLE public.forex_watchlist (
	pair varchar(10) NOT NULL,
	"action" varchar(10) NOT NULL,
	score_diff numeric(10, 2) NOT NULL,
	note text NULL,
	updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT forex_watchlist_pkey PRIMARY KEY (pair)
);

CREATE TABLE public.symbols_watchlist (
	symbol varchar NOT NULL,
	highest_price int8 NULL,
	lowest_price int8 NULL,
	auto_trade bool DEFAULT false NOT NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT symbols_watchlist_pkey PRIMARY KEY (symbol)
);

CREATE TABLE public.world_symbols_watchlist (
	symbol varchar NOT NULL,
	country varchar NOT NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT uq_symbol_country UNIQUE (symbol, country)
);

CREATE TABLE public.price_alerts (
	symbol varchar NOT NULL,
	asset_type varchar(20) NOT NULL CHECK (asset_type IN ('crypto', 'stock', 'gold', 'silver', 'forex')),
	alert_price numeric(20, 8) NOT NULL,
	is_active bool DEFAULT true NOT NULL,
	last_notified_at timestamptz NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT price_alerts_pkey PRIMARY KEY (symbol, asset_type)
);
CREATE INDEX idx_price_alerts_active ON public.price_alerts(is_active, asset_type);


#### OTHER TABLES ####

CREATE TABLE public.user_info (
	id varchar NOT NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	opt int8 NULL,
	CONSTRAINT user_info_pkey PRIMARY KEY (id)
);

CREATE TABLE public.user_trading_symbols (
	user_id varchar NOT NULL,
	symbol varchar NOT NULL,
	entry_price int8 NOT NULL,
	avg_price int8 NULL,
	current_price int8 DEFAULT 0 NOT NULL,
	CONSTRAINT user_trading_symbols_pkey PRIMARY KEY (user_id, symbol)
);