WITH hold_times AS (
  SELECT 
    t1.wallet_address,
    t1.contract_address,
    CAST(EXTRACT(EPOCH FROM (t2.timestamp - t1.timestamp)) AS BIGINT) AS hold_time_seconds
  FROM wallet_transactions t1
  JOIN wallet_transactions t2 
    ON t1.wallet_address = t2.wallet_address 
    AND t1.contract_address = t2.contract_address
    AND t1.action = 'BUY'
    AND t2.action = 'SELL'
    AND t2.timestamp > t1.timestamp
),
wallet_aliases AS (
  SELECT DISTINCT ON (wallet_address) 
    wallet_address, 
    wallet_alias
  FROM wallet_transactions
  WHERE wallet_alias IS NOT NULL
  ORDER BY wallet_address, timestamp DESC  -- ✅ Get the latest alias recorded for each wallet
)
SELECT 
  main.wallet_address,
  wa.wallet_alias,  -- ✅ Added Wallet Alias
  COUNT(DISTINCT main.message_id) FILTER (WHERE main.pnl > 0) AS successful_sells,  -- ✅ Ensures each successful sell is counted only once
  COUNT(DISTINCT main.message_id) AS total_sells,  -- ✅ Ensures total sells are counted only once
  ROUND(
    (COUNT(DISTINCT main.message_id) FILTER (WHERE main.pnl > 0) * 100.0) / NULLIF(COUNT(DISTINCT main.message_id), 0), 
    2
  ) AS win_rate,
  ROUND(
    COALESCE(
      (SELECT AVG(amount_sol) FROM wallet_transactions WHERE action = 'BUY' AND wallet_transactions.wallet_address = main.wallet_address),
      0
    ), 
    2
  ) AS avg_buy_amount_sol,  -- ✅ Moved avg buy amount right after win rate & rounded to 2 decimals
  ROUND(
    COALESCE(
      (SELECT SUM(amount_sol) FROM wallet_transactions WHERE action = 'BUY' AND wallet_transactions.wallet_address = main.wallet_address),
      0
    ), 
    2
  ) AS total_sol_bought,
  ROUND(
    COALESCE(
      (SELECT SUM(amount_sol) FROM wallet_transactions WHERE action = 'SELL' AND wallet_transactions.wallet_address = main.wallet_address),
      0
    ), 
    2
  ) AS total_sol_sold,
  ROUND(
    COALESCE(
      (SELECT SUM(amount_sol) FROM wallet_transactions WHERE action = 'SELL' AND wallet_transactions.wallet_address = main.wallet_address), 0
    ) -
    COALESCE(
      (SELECT SUM(amount_sol) FROM wallet_transactions WHERE action = 'BUY' AND wallet_transactions.wallet_address = main.wallet_address), 0
    ), 
    2
  ) AS total_sol_gain,
  COUNT(DISTINCT main.contract_address) AS total_contracts_traded,
  ROUND(
    (
      COALESCE(
        (SELECT SUM(amount_sol) FROM wallet_transactions WHERE action = 'SELL' AND wallet_transactions.wallet_address = main.wallet_address), 0
      ) - 
      COALESCE(
        (SELECT SUM(amount_sol) FROM wallet_transactions WHERE action = 'BUY' AND wallet_transactions.wallet_address = main.wallet_address), 0
      )
    ) * 100.0 / NULLIF(
      COALESCE(
        (SELECT SUM(amount_sol) FROM wallet_transactions WHERE action = 'BUY' AND wallet_transactions.wallet_address = main.wallet_address), 0
      ), 0
    ), 
    2
  ) AS roi_percentage
FROM wallet_transactions AS main
LEFT JOIN wallet_aliases wa ON main.wallet_address = wa.wallet_address  -- ✅ Join latest wallet alias
WHERE main.action = 'SELL'  -- ✅ Ensures we only count sells properly
GROUP BY main.wallet_address, wa.wallet_alias  -- ✅ Group by alias as well
ORDER BY roi_percentage DESC;