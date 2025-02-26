WITH wallet_aliases AS (
  SELECT DISTINCT ON (wallet_address) 
    wallet_address, 
    wallet_alias
  FROM wallet_transactions
  WHERE wallet_alias IS NOT NULL
  ORDER BY wallet_address, timestamp DESC  -- ✅ Get the latest alias recorded for each wallet
),
roi_data AS (
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
  r.wallet_address,
  wa.wallet_alias,  -- ✅ Join latest wallet alias
  ROUND(
    (r.total_sell_1d - r.total_buy_1d) * 100.0 / NULLIF(r.total_buy_1d, 0),
    2
  ) AS roi_1d,
  ROUND(
    (r.total_sell_7d - r.total_buy_7d) * 100.0 / NULLIF(r.total_buy_7d, 0),
    2
  ) AS roi_7d,
  ROUND(
    (r.total_sell_30d - r.total_buy_30d) * 100.0 / NULLIF(r.total_buy_30d, 0),
    2
  ) AS roi_30d
FROM roi_data r
LEFT JOIN wallet_aliases wa ON r.wallet_address = wa.wallet_address
ORDER BY roi_30d DESC;
