import discord
from src.config import CHANNEL_ID
from src.database import create_db_pool, insert_transaction
from src.extract import extract_transaction_data

# ✅ Enable required intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
  print(f"✅ Logged in as {client.user}")
  client.db_pool = await create_db_pool()
  print(f"📡 Listening for messages in channel {CHANNEL_ID}...")

@client.event
async def on_message(message):
  """Processes new messages in the target Discord channel."""
  
  if message.channel.id != int(CHANNEL_ID):
    return

  if message.author == client.user:
    return  

  if not message.embeds:
    print(f"⚠️ Message {message.id} ignored (No embeds)")
    return  

  print(f"\n📩 Processing Message (ID: {message.id}) from {message.author}")

  print(f"📦 Message {message.id} contains {len(message.embeds)} embeds")

  for embed in message.embeds:
    if embed.description:
      print(f"🔹 Extracting data from embed description...")

      timestamp = message.created_at.replace(tzinfo=None)
      message_id = message.id
      data = extract_transaction_data(embed.description, timestamp, message_id)

      # Log missing fields before inserting into the database
      if not data:
        print(f"❌ Data extraction failed for message {message.id}. Skipping...")
        return

      # Insert transaction into the database
      await insert_transaction(client.db_pool, data)
      print(f"✅ Successfully saved transaction for {data['ticker']} ({data['amount_sol']} SOL)")
