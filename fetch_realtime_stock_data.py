# import yfinance as yf
# import json
# from time import sleep
# from kafka import KafkaProducer
# from datetime import datetime
#
# # Ticker symbols you want to track
# TICKERS = ["AAPL", "NVDA", "TSLA"]
#
# # Kafka setup
# KAFKA_TOPIC = "stock_data"
# KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
# producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
#
# def fetch_stock_data():
#     for ticker in TICKERS:
#         # Get the latest stock data
#         stock = yf.Ticker(ticker)
#         hist = stock.history(period="1d", interval="1m")
#
#         if not hist.empty:
#             latest_data = hist.iloc[-1]
#             stock_data = {
#                 "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                 "ticker": ticker,
#                 "open": latest_data['Open'],
#                 "high": latest_data['High'],
#                 "low": latest_data['Low'],
#                 "close": latest_data['Close'],
#                 "volume": latest_data['Volume']
#             }
#             print(f"Publishing to Kafka: {stock_data}")
#             producer.send(KAFKA_TOPIC, stock_data)
#             producer.flush()  # Ensure the message is sent
#         else:
#             print(f"No data found for ticker: {ticker}")
#
# if __name__ == "__main__":
#     while True:
#         fetch_stock_data()
#         sleep(60)  # Fetch data every minute

import yfinance as yf
import json
from kafka import KafkaProducer
import sqlite3
from datetime import datetime

# List of tickers to fetch data for
TICKERS = ["AAPL", "NVDA", "TSLA", "AMZN", "AMD", "GOOGL", "F", "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA"]

# Kafka setup
KAFKA_TOPIC = "stock_data"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


# Connect to SQLite and create table if not exists, with a unique constraint on timestamp and ticker
def init_database():
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_data (
            timestamp TEXT,
            ticker TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (timestamp, ticker)
        )
    ''')
    # Create an index for quicker retrieval by ticker and date
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_ticker_timestamp
        ON stock_data (ticker, timestamp)
    ''')
    conn.commit()
    conn.close()

# Save data to SQLite database, ignoring duplicates
def save_to_database(data):
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO stock_data (timestamp, ticker, open, high, low, close, volume) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data["timestamp"], data["ticker"], data["open"], data["high"], data["low"], data["close"], data["volume"]))
    conn.commit()
    conn.close()


# Fetch historical data for each ticker
def fetch_historical_data(period="30d"):
    for ticker in TICKERS:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)  # Fetch historical data for the specified period

        if not data.empty:
            for timestamp, row in data.iterrows():
                stock_data = {
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "ticker": ticker,
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"]
                }

                # Publish to Kafka
                producer.send(KAFKA_TOPIC, stock_data)
                producer.flush()

                # Save to database
                save_to_database(stock_data)

                print(f"Saved historical data for {ticker} at {timestamp}")
        else:
            print(f"No historical data found for ticker: {ticker}")


if __name__ == "__main__":
    # Initialize the database
    init_database()

    # Fetch and store historical data
    fetch_historical_data("5y")  # Change "1y" to desired period (e.g., "30d" for 30 days)