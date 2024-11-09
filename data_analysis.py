import sqlite3

def fetch_recent_data(ticker, days=30):
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM stock_data
        WHERE ticker = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (ticker, days))
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    ticker = "NVDA"  # Example ticker
    days = 30  # Retrieve data for the last 30 days
    data = fetch_recent_data(ticker, days)
    for row in data:
        print(row)