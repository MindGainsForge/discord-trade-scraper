import re

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
