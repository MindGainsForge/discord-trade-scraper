import discord
import os
import re
import asyncpg
import asyncio
import uuid
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

if not TOKEN or not DB_HOST or not DB_NAME or not DB_USER or not DB_PASSWORD:
  raise ValueError("❌ Missing required environment variables! Check your .env file.")

# Enable required intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)

async def create_db_pool():
  """Creates a connection pool to PostgreSQL."""
  pool = await asyncpg.create_pool(
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    host=DB_HOST,
    port=DB_PORT
  )
  print(f"✅ Database connection pool established! Connected to `{DB_NAME}` at `{DB_HOST}:{DB_PORT}`")
  return pool

async def fetch_all_messages(channel):
  """Fetches all messages from the channel history."""
  all_messages = []
  last_message_id = None

  while True:
    # Fetch the next batch of messages
    if last_message_id:
      messages = [message async for message in channel.history(limit=100, before=discord.Object(id=last_message_id))]
    else:
      messages = [message async for message in channel.history(limit=100)]

    if not messages:
      break  # No more messages to fetch

    all_messages.extend(messages)
    last_message_id = messages[-1].id  # Fetch older messages next
    print(f"✅ Fetched {len(messages)} more messages, total: {len(all_messages)}")

    await asyncio.sleep(1)  # Prevent hitting Discord rate limits

  print(f"✅ Finished fetching {len(all_messages)} messages!")
  return all_messages

async def insert_transaction(pool, data):
  """Inserts transaction data into the PostgreSQL database."""
  
  required_fields = ["message_id", "wallet_address", "wallet_alias", "contract_address", "ticker", "action", "amount_sol", "timestamp"]
  missing_fields = [field for field in required_fields if not data.get(field)]

  if missing_fields:
    print(f"\n🚨 ERROR: Missing required fields {missing_fields} in transaction data! Skipping insert.")
    return

  # Convert types to match PostgreSQL schema
  amount_sol = float(data["amount_sol"]) if data["amount_sol"] is not None else None
  amount_usd = float(data["amount_usd"]) if data["amount_usd"] is not None else None
  market_cap = float(data["market_cap"].replace("M", "000000").replace("K", "000")) if data["market_cap"] else None
  sold_percent = float(data["sold_percent"]) if data["sold_percent"] is not None else None
  pnl = float(data["pnl"]) if data["pnl"] is not None else None

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
        str(uuid.uuid4()), 
        data["message_id"], 
        data["timestamp"],   
        str(data["wallet_address"]),
        str(data["wallet_alias"]),
        str(data["contract_address"]),
        str(data["ticker"]),  
        str(data["action"]),
        amount_sol,
        amount_usd,
        market_cap,
        sold_percent,
        pnl
      )
      print(f"✅ Transaction saved: {data['action']} {data['ticker']} ({amount_sol} SOL) at {data['timestamp']}")
    except Exception as e:
      print(f"❌ Database insert error: {e}")

def extract_transaction_data(description, timestamp, message_id):
  """Extracts buy/sell transaction details from the message description."""
  
  if "TRANSFER" in description.upper() or "CLOSE TOKEN ACCOUNT" in description.upper() or "BUY USDC" in description.upper():
    print(f"⚠️ Skipping message {message_id}: Transfer or Close Token Account or BUY USDC")
    return None

  data = {
    "message_id": message_id,
    "wallet_address": None,
    "wallet_alias": None,
    "contract_address": None,
    "ticker": None,
    "action": None,
    "amount_sol": None,
    "amount_usd": None,
    "market_cap": None,
    "sold_percent": None,
    "pnl": None,
    "timestamp": timestamp.replace(tzinfo=None)
  }

  if "BUY" in description:
    data["action"] = "BUY"
  elif "SELL" in description:
    data["action"] = "SELL"

  wallet_match = re.search(r'`([A-Za-z0-9]{25,})`', description)
  if wallet_match:
    data["wallet_address"] = wallet_match.group(1)

  alias_match = re.search(r"\*\*(.*?)\*\*", description)
  if alias_match:
    data["wallet_alias"] = alias_match.group(1)

  contract_match = re.search(r"`([A-Za-z0-9]{25,})`\n\n\[TX\]", description)
  if contract_match:
    data["contract_address"] = contract_match.group(1)

  ticker_match = re.search(r"🔗 \*\*#([A-Za-z0-9]+)\*\*", description)
  if ticker_match:
    data["ticker"] = ticker_match.group(1)

  if not data["ticker"] and data["contract_address"]:
    data["ticker"] = data["contract_address"]

  sol_match = re.search(r"\*\*([\d,]+\.?\d*)\*\* \*\*\[SOL\]", description)
  if sol_match:
    data["amount_sol"] = float(sol_match.group(1).replace(',', ''))

  usd_match = re.search(r"\(\$([\d,]+\.\d+)\)", description)
  if usd_match:
    data["amount_usd"] = float(usd_match.group(1).replace(',', ''))

  mcap_match = re.search(r"\*\*MC\*\*: \$(\d+\.\d+[KM]?)", description)
  if mcap_match:
    data["market_cap"] = mcap_match.group(1)

  sold_match = re.search(r"➖Sold: (\d+)%", description)
  if sold_match:
    data["sold_percent"] = int(sold_match.group(1))

  pnl_match = re.search(r"📈PnL: \*\*([\d\.\+\-]+)\*\* SOL", description)
  if pnl_match:
    data["pnl"] = float(pnl_match.group(1))

  return data

@client.event
async def on_ready():
  print(f"✅ Logged in as {client.user}")
  client.db_pool = await create_db_pool()
  channel = client.get_channel(CHANNEL_ID)

  if not channel:
    print("❌ Error: Cannot find the Discord channel.")
    return

  messages = await fetch_all_messages(channel)

  for message in messages:
    if message.embeds:
      for embed in message.embeds:
        if embed.description:
          data = extract_transaction_data(embed.description, message.created_at.replace(tzinfo=None), message.id)
          if data:
            await insert_transaction(client.db_pool, data)

  print("✅ Finished processing all historical messages.")
  await client.close()

client.run(TOKEN)
