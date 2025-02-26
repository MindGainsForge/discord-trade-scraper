# **mindgains-discord-scraper**

## **📌 Overview**
**mindgains-discord-scraper** connects to a Discord channel using a bot token and scrapes **RayBot** messages. It extracts the following **metrics** from buy and sell messages:

- **Timestamp** of the transaction
- **Wallet address**
- **Wallet alias** (if available)
- **Contract address**
- **Ticker**
- **Action** (BUY or SELL)
- **Amount of SOL**
- **Amount in USD**
- **Market cap** (for buys only)
- **Percentage sold** (for sells only)
- **PnL (Profit and Loss)** (for sells only)

The extracted metrics are stored in a **PostgreSQL database** for further analysis.

---
## **⚡ Requirements**
- Python 3.10+
- PostgreSQL 13+
- Docker (optional, for running PostgreSQL locally)
- A **Discord bot token** with the correct permissions
- `pip` for package management

---
## **🛠️ Local Development Setup**

### **1️⃣ Start a Local PostgreSQL Database**
You can use the following command to run a PostgreSQL database inside **Docker** with a **database named `mindgains`** and a **user `mindgains`**:

```sh
docker run --rm --name postgres \
  -e POSTGRES_USER=mindgains \
  -e POSTGRES_PASSWORD=mindgains \
  -e POSTGRES_DB=mindgains \
  --tmpfs /var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:latest
```

Alternatively, you can run the script:
```
./start_local_pg.sh
```

---
### **2️⃣ Export Required Environment Variables**

Before running the scraper, export the following environment variables:

```sh
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=mindgains
export DB_USER=mindgains
export DB_PASSWORD=mindgains
export DISCORD_BOT_TOKEN=<BOT_TOKEN>
export DISCORD_CHANNEL_ID=<CHANNEL_ID>
```

---
### **3️⃣ Create a Virtual Environment & Install Dependencies**

```sh
python -m venv venv  # Create a virtual environment
source venv/bin/activate  # Activate virtual environment (Mac/Linux)
pip install -r requirements.txt  # Install dependencies
```

---
## **📥 Fetching Historical Messages**
If the channel **already contains messages** that should be ingested into the database, run:

```sh
python fetch_message_history.py
```

This will retrieve all past messages and insert them into the **PostgreSQL database**.

---
## **📡 Running the Live Scraper**
To start the **service** that will scrape and ingest **all new messages** as they appear in the channel, run:

```sh
python run.py
```

This will continuously listen for new **BUY** and **SELL** messages and store their extracted metrics in the database.

---
## **📊 Basic Data Analysis**
For a basic analysis of the **stored transactions**, run a **SQL query** from the **analysis_queries** folder:

```sh
psql -h localhost -p 5432 -d mindgains -U mindgains -f analysis_queries/general_analysis.sql
```

This script for example calculates **win rates, gained SOL, and ROI** per wallet address.

---
