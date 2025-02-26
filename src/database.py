import asyncpg
import uuid
import sys
from src.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

async def create_db_pool():
  """Creates a connection pool to PostgreSQL. Exits if connection fails."""
  try:
    pool = await asyncpg.create_pool(
      user=DB_USER, password=DB_PASSWORD,
      database=DB_NAME, host=DB_HOST, port=DB_PORT
    )
    print(f"✅ Database connection pool established! Connected to `{DB_NAME}` at `{DB_HOST}:{DB_PORT}`")
    return pool
  except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

async def insert_transaction(pool, data):
  """Inserts transaction data into the PostgreSQL database."""
  
  required_fields = ["message_id", "wallet_address", "wallet_alias", "contract_address", "ticker", "action", "amount_sol", "timestamp"]
  missing_fields = [field for field in required_fields if not data.get(field)]

  if missing_fields:
    print(f"\n🚨 ERROR: Missing required fields {missing_fields}! Skipping insert.")
    return

  def convert_float(value):
    if value is None:
      return None
    try:
      return float(value.replace(",", "")) if isinstance(value, str) else float(value)
    except ValueError:
      return None

  amount_sol = convert_float(data["amount_sol"])
  amount_usd = convert_float(data["amount_usd"])
  market_cap = convert_float(data["market_cap"])
  sold_percent = convert_float(data["sold_percent"])
  pnl = convert_float(data["pnl"])

  async with pool.acquire() as conn:
    try:
      await conn.execute(
        """
        INSERT INTO wallet_transactions (
          id, message_id, timestamp, wallet_address, wallet_alias, contract_address, ticker, action, 
          amount_sol, amount_usd, market_cap, sold_percent, pnl
        ) VALUES (
          $1::UUID, $2::BIGINT, $3::TIMESTAMP, $4::TEXT, $5::TEXT, $6::TEXT, $7::VARCHAR(20), 
          $8::VARCHAR(4), $9::NUMERIC(12, 6), $10::NUMERIC(20, 2), 
          $11::NUMERIC(20, 2), $12::NUMERIC(5, 2), $13::NUMERIC(12, 6)
        ) ON CONFLICT (message_id) DO NOTHING
        """,
        str(uuid.uuid4()), data["message_id"], data["timestamp"],
        data["wallet_address"], data["wallet_alias"], data["contract_address"],
        data["ticker"], data["action"], amount_sol, amount_usd, 
        market_cap, sold_percent, pnl
      )
      print(f"✅ Transaction saved: {data['action']} {data['ticker']} ({amount_sol} SOL) at {data['timestamp']}")
    except Exception as e:
      print(f"❌ Database insert error: {e}")
