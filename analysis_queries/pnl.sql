WITH wallet_aliases AS (
  SELECT DISTINCT ON (wallet_address) 
    wallet_address, 
    wallet_alias
  FROM wallet_transactions
  WHERE wallet_alias IS NOT NULL
  ORDER BY wallet_address, timestamp DESC  -- ✅ Get the latest alias recorded for each wallet
),
pnl_data AS (
  SELECT 
    wallet_address,
    SUM(CASE WHEN action = 'BUY' AND timestamp >= NOW() - INTERVAL '1 day' THEN amount_sol ELSE 0 END) AS total_buy_1d,
    SUM(CASE WHEN action = 'SELL' AND timestamp >= NOW() - INTERVAL '1 day' THEN amount_sol ELSE 0 END) AS total_sell_1d,
    SUM(CASE WHEN action = 'BUY' AND timestamp >= NOW() - INTERVAL '7 days' THEN amount_sol ELSE 0 END) AS total_buy_7d,
    SUM(CASE WHEN action = 'SELL' AND timestamp >= NOW() - INTERVAL '7 days' THEN amount_sol ELSE 0 END) AS total_sell_7d,
    SUM(CASE WHEN action = 'BUY' AND timestamp >= NOW() - INTERVAL '30 days' THEN amount_sol ELSE 0 END) AS total_buy_30d,
    SUM(CASE WHEN action = 'SELL' AND timestamp >= NOW() - INTERVAL '30 days' THEN amount_sol ELSE 0 END) AS total_sell_30d
  FROM wallet_transactions
  GROUP BY wallet_address
)
SELECT 
  p.wallet_address,
  wa.wallet_alias,  -- ✅ Join latest wallet alias
  ROUND((p.total_sell_1d - p.total_buy_1d), 2) AS pnl_1d,
  ROUND((p.total_sell_7d - p.total_buy_7d), 2) AS pnl_7d,
  ROUND((p.total_sell_30d - p.total_buy_30d), 2) AS pnl_30d
FROM pnl_data p
LEFT JOIN wallet_aliases wa ON p.wallet_address = wa.wallet_address
ORDER BY pnl_30d DESC;  -- ✅ Sort by highest 30-day PnL
