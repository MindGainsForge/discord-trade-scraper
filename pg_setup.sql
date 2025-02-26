CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE wallet_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    wallet_address TEXT NOT NULL,
    wallet_alias TEXT NOT NULL,
    contract_address TEXT NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    action VARCHAR(4) CHECK (action IN ('BUY', 'SELL')) NOT NULL,
    amount_sol NUMERIC(12, 6) NOT NULL,
    amount_usd NUMERIC(20, 2) NULL,
    market_cap NUMERIC(20, 2) NULL,
    sold_percent NUMERIC(5, 2) NULL,
    pnl NUMERIC(12, 6) NULL
);

ALTER TABLE wallet_transactions ADD COLUMN message_id BIGINT UNIQUE;
